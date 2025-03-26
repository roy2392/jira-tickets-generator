import os
from anthropic import Anthropic
from faker import Faker
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random

class TicketGenerator:
    def __init__(self, jira, project_key):
        self.jira = jira
        self.project_key = project_key
        self.anthropic = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
        self.fake = Faker()
        
    def generate_ticket_content(self, ticket_type="Task"):
        prompt = f"""Generate a realistic Jira {ticket_type} with the following format:
        {{
            "summary": "Brief ticket title",
            "description": "Detailed description with acceptance criteria",
            "story_points": number between 1-13,
            "priority": "High/Medium/Low"
        }}
        Make it related to software development and be specific."""
        
        message = self.anthropic.messages.create(
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            model="claude-3-sonnet-20240229"
        )
        
        # Extract just the JSON part from the response
        content = message.content[0].text
        # Remove any markdown formatting if present
        if content.startswith('```json'):
            content = content[7:-3]  # Remove ```json and ``` markers
        elif content.startswith('{'):
            content = content  # Already clean JSON
        else:
            # Find the first { and last }
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > 0:
                content = content[start:end]
            
        return content
        
    def generate_sprint_data(self, num_sprints=1):
        sprints = []
        start_date = datetime.now()
        
        for i in range(num_sprints):
            end_date = start_date + timedelta(days=14)  # 2-week sprints
            sprint = {
                "name": f"Sprint {i + 1}",
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "goal": self.generate_sprint_goal()
            }
            sprints.append(sprint)
            start_date = end_date + timedelta(days=1)  # 1 day between sprints
            
        return sprints
    
    def generate_sprint_goal(self):
        prompt = """Generate a realistic sprint goal that's focused and achievable within 2 weeks.
        Make it specific to software development."""
        
        message = self.anthropic.messages.create(
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            model="claude-3-sonnet-20240229"
        )
        
        return message.content[0].text.strip()
    
    def create_epic(self):
        """Create an epic for the project"""
        print("\nGenerating Epic...")
        
        epic_data = {
            'project': {'key': self.project_key},
            'summary': 'Q2 2024 Development Initiative',
            'description': 'Strategic development initiative for Q2 2024 focusing on core platform improvements and feature additions.',
            'issuetype': {'name': 'Epic'}
        }
        
        try:
            epic = self.jira.create_issue(**epic_data)
            print(f"Created Epic: {epic.key}")
            return epic
        except Exception as e:
            print(f"Error creating epic: {str(e)}")
            return None

    def create_sprints(self, board_id):
        """Create sprints for the project"""
        print("\nGenerating Sprints...")
        sprints = []
        num_sprints = int(os.getenv('INPUT_NUM_SPRINTS', 2))
        sprint_length = int(os.getenv('INPUT_SPRINT_LENGTH_DAYS', 14))
        
        # Calculate sprint dates
        current_date = datetime.now()
        
        for i in range(num_sprints):
            start_date = current_date + timedelta(days=i * sprint_length)
            end_date = start_date + timedelta(days=sprint_length)
            
            sprint_name = f"Sprint {i + 1}"
            try:
                sprint = self.jira.create_sprint(
                    name=sprint_name,
                    board_id=board_id,
                    startDate=start_date.isoformat(),
                    endDate=end_date.isoformat()
                )
                print(f"Created Sprint: {sprint.name}")
                sprints.append(sprint)
            except Exception as e:
                print(f"Warning: Could not create sprint - {str(e)}")
        
        return sprints

    def generate_tickets(self, epic_key, sprints):
        """Generate tickets and assign them to sprints"""
        print("\nGenerating Tickets...")
        created_tickets = []
        tickets_per_sprint = int(os.getenv('INPUT_TICKETS_PER_SPRINT', 5))
        incomplete_tickets_per_sprint = int(os.getenv('INPUT_INCOMPLETE_TICKETS_PER_SPRINT', 1))
        ticket_types = os.getenv('INPUT_TICKET_TYPES', 'Story,Task,Bug').split(',')
        
        # Get all fields to find the Epic Link field
        fields = self.jira.fields()
        epic_link_field = None
        for field in fields:
            if field['name'] == 'Epic Link':
                epic_link_field = field['id']
                break
        
        for sprint in sprints:
            # Create regular tickets
            for _ in range(tickets_per_sprint):
                ticket_type = random.choice(ticket_types)
                summary = self.generate_ticket_summary(ticket_type)
                description = self.generate_ticket_description(ticket_type)
                
                ticket_data = {
                    'project': {'key': self.project_key},
                    'summary': summary,
                    'description': description,
                    'issuetype': {'name': ticket_type}
                }
                
                # Add Epic Link if available
                if epic_link_field:
                    ticket_data[epic_link_field] = epic_key
                
                try:
                    ticket = self.jira.create_issue(**ticket_data)
                    self.jira.add_issues_to_sprint(sprint.id, [ticket.id])
                    print(f"Created {ticket_type}: {ticket.key}")
                    created_tickets.append(ticket)
                except Exception as e:
                    print(f"Error creating ticket: {str(e)}")
            
            # Create incomplete tickets per sprint
            for _ in range(incomplete_tickets_per_sprint):
                try:
                    ticket_data = {
                        'project': {'key': self.project_key},
                        'summary': 'Incomplete ticket needs refinement',
                        'description': 'This ticket needs more information and refinement.',
                        'issuetype': {'name': 'Story'}
                    }
                    
                    # Add Epic Link if available
                    if epic_link_field:
                        ticket_data[epic_link_field] = epic_key
                    
                    ticket = self.jira.create_issue(**ticket_data)
                    self.jira.add_issues_to_sprint(sprint.id, [ticket.id])
                    print(f"Created Incomplete Ticket: {ticket.key}")
                    created_tickets.append(ticket)
                except Exception as e:
                    print(f"Error creating incomplete ticket: {str(e)}")
        
        return created_tickets

    def generate_ticket_summary(self, ticket_type):
        """Generate a realistic ticket summary"""
        if ticket_type == 'Story':
            return f"As a user, I want to {self.fake.bs()}"
        elif ticket_type == 'Task':
            return f"Implement {self.fake.catch_phrase()}"
        else:  # Bug
            return f"Fix issue with {self.fake.catch_phrase()}"

    def generate_ticket_description(self, ticket_type):
        """Generate a realistic ticket description"""
        if ticket_type == 'Story':
            return f"""User Story:
As a user
I want to {self.fake.bs()}
So that I can {self.fake.catch_phrase()}

Acceptance Criteria:
1. {self.fake.sentence()}
2. {self.fake.sentence()}
3. {self.fake.sentence()}

Technical Notes:
- {self.fake.sentence()}
- {self.fake.sentence()}"""
        elif ticket_type == 'Task':
            return f"""Technical Task:
{self.fake.paragraph()}

Implementation Details:
- {self.fake.sentence()}
- {self.fake.sentence()}
- {self.fake.sentence()}"""
        else:  # Bug
            return f"""Bug Report:
Current Behavior: {self.fake.sentence()}
Expected Behavior: {self.fake.sentence()}

Steps to Reproduce:
1. {self.fake.sentence()}
2. {self.fake.sentence()}
3. {self.fake.sentence()}

Impact: {random.choice(['Low', 'Medium', 'High'])}
Environment: {random.choice(['Development', 'Staging', 'Production'])}""" 