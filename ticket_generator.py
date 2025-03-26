import os
from anthropic import Anthropic
from faker import Faker
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import random

class TicketGenerator:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))
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
        
        message = self.client.messages.create(
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
        
        message = self.client.messages.create(
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": prompt
            }],
            model="claude-3-sonnet-20240229"
        )
        
        return message.content[0].text.strip()
    
    def generate_epic(self):
        prompt = """Generate a realistic Jira Epic with the following format:
        {
            "summary": "Epic title",
            "description": "Epic description with high-level goals",
            "expected_duration_months": number between 1-6
        }
        Make it related to software development and be specific."""
        
        message = self.client.messages.create(
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