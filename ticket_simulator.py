import random
from datetime import datetime, timedelta
import json
import time
import os
from faker import Faker

class TicketSimulator:
    def __init__(self, jira, tickets):
        self.jira = jira
        self.tickets = tickets
        self.fake = Faker()
        self.team_members = self.create_or_get_team_members()
        
        self.status_transitions = [
            "To Do",
            "In Progress",
            "In Review",
            "QA",
            "Done"
        ]
        
        self.common_blockers = [
            "Waiting for API documentation",
            "Dependent ticket not completed",
            "Need clarification from Product Owner",
            "Environment issues",
            "Integration test failures",
            "Performance concerns",
            "Security review pending"
        ]
        
    def create_or_get_team_members(self):
        """Create or get existing team members"""
        team_members = []
        
        # Define team roles and number of members per role from environment variables
        team_structure = {
            'Developer': int(os.getenv('INPUT_NUM_DEVELOPERS', 4)),
            'QA Engineer': int(os.getenv('INPUT_NUM_QA', 2)),
            'Tech Lead': int(os.getenv('INPUT_NUM_TECH_LEADS', 1)),
            'Product Owner': int(os.getenv('INPUT_NUM_PRODUCT_OWNERS', 1)),
            'Scrum Master': int(os.getenv('INPUT_NUM_SCRUM_MASTERS', 1))
        }
        
        try:
            # Get all users in Jira
            existing_users = self.jira._get_json('user/search', params={'query': '@'})
            existing_emails = {user['emailAddress'] for user in existing_users if 'emailAddress' in user}
            
            # Create users for each role
            for role, count in team_structure.items():
                for i in range(count):
                    first_name = self.fake.first_name()
                    last_name = self.fake.last_name()
                    email = f"{first_name.lower()}.{last_name.lower()}@example.com"
                    
                    # Skip if user already exists
                    if email in existing_emails:
                        team_members.append(email)
                        continue
                    
                    # Create new user
                    try:
                        user_data = {
                            'displayName': f"{first_name} {last_name}",
                            'emailAddress': email,
                            'name': email.split('@')[0],
                            'password': self.fake.password(),
                            'notification': 'DONT_NOTIFY'
                        }
                        
                        # Try to create user using admin API
                        response = self.jira._session.post(
                            f"{self.jira.server_url}/rest/api/2/user",
                            json=user_data
                        )
                        
                        if response.status_code in [201, 400]:  # 400 means user might already exist
                            team_members.append(email)
                            print(f"Added team member: {email} ({role})")
                    except Exception as e:
                        print(f"Warning: Could not create user {email}: {str(e)}")
            
            # If we couldn't create any users, fall back to the authenticated user
            if not team_members:
                team_members = [os.getenv('JIRA_EMAIL')]
                print("Warning: Using authenticated user as fallback")
            
            return team_members
            
        except Exception as e:
            print(f"Warning: Could not create team members: {str(e)}")
            # Fall back to authenticated user
            return [os.getenv('JIRA_EMAIL')]

    def simulate_work(self):
        """Simulate work on tickets"""
        print("\nSimulating work on tickets...")
        work_chance = int(os.getenv('INPUT_WORK_CHANCE', 70)) / 100
        
        for ticket in self.tickets:
            # Skip some tickets to simulate incomplete work
            if random.random() < work_chance:
                self.simulate_ticket_progress(ticket)
                # Add small delay to make transitions more realistic
                time.sleep(0.5)

    def simulate_ticket_progress(self, ticket):
        """Simulate progress on a single ticket"""
        try:
            # Assign to random team member
            assignee = random.choice(self.team_members)
            self.jira.assign_issue(ticket.key, assignee)
            
            # Add work log with assignee's name
            self.jira.add_worklog(
                ticket.key,
                timeSpentSeconds=random.randint(3600, 28800),  # 1-8 hours
                comment=f"{assignee.split('@')[0]} working on implementing the requested changes."
            )
            
            # Try to transition through different states
            transitions = self.jira.transitions(ticket.key)
            transition_ids = {t['name'].lower(): t['id'] for t in transitions}
            
            # Try common transition names
            for status in ['in progress', 'in review', 'qa', 'done']:
                if status in transition_ids:
                    try:
                        self.jira.transition_issue(ticket.key, transition_ids[status])
                        print(f"Moved {ticket.key} to {status.upper()} (Assignee: {assignee})")
                    except Exception as e:
                        print(f"Warning: Could not find transition to {status.upper()} for {ticket.key}")
            
            # Add comments
            block_chance = int(os.getenv('INPUT_BLOCK_CHANCE', 30)) / 100
            if random.random() < block_chance:
                blocker = random.choice(self.team_members)
                self.jira.add_comment(
                    ticket.key,
                    f"Blocked: {blocker.split('@')[0]} needs to complete dependent work first."
                )
            else:
                reviewer = random.choice([m for m in self.team_members if m != assignee])
                self.jira.add_comment(
                    ticket.key,
                    f"Implementation completed by {assignee.split('@')[0]}, requesting review from {reviewer.split('@')[0]}."
                )
                
        except Exception as e:
            print(f"Error simulating work on {ticket.key}: {str(e)}")
        
    def create_incomplete_ticket(self, epic_key=None, sprint_id=None):
        """Create a ticket with missing or incomplete information"""
        issues = [
            "Missing acceptance criteria",
            "Unclear requirements",
            "No story points estimated",
            "Dependencies not identified",
            "Technical approach not defined"
        ]
        
        selected_issues = random.sample(issues, k=random.randint(1, 3))
        
        ticket_data = {
            "summary": f"[Incomplete] {random.choice(['Feature', 'Enhancement', 'Task'])} needed",
            "description": "This ticket needs more information.\n\nMissing elements:\n- " + "\n- ".join(selected_issues),
            "story_points": 0,  # Unestimated
            "priority": "Medium"
        }
        
        return self.jira.create_ticket(json.dumps(ticket_data), epic_key, sprint_id)
        
    def _transition_ticket(self, ticket_key, from_status, to_status, assignee):
        """Transition a ticket to a new status with appropriate comments"""
        try:
            # Add transition comment
            comment = self._generate_status_comment(to_status, assignee)
            self.jira.add_comment(ticket_key, comment)
            
            # Update the ticket status
            self.jira.transition_issue(ticket_key, to_status)
            
            # Add time spent (if applicable)
            if to_status in ["In Progress", "In Review", "QA"]:
                time_spent = random.randint(1, 8) * assignee["velocity"]
                self.jira.add_worklog(ticket_key, f"{time_spent}h")
                
        except Exception as e:
            print(f"Warning: Could not transition ticket {ticket_key} - {str(e)}")
            
    def _add_blocker_comment(self, ticket_key, blocker):
        """Add a blocker comment to a ticket"""
        comment = f"🚫 **Blocked**\nReason: {blocker}\nImpact: This is preventing progress on the ticket."
        try:
            self.jira.add_comment(ticket_key, comment)
            self.jira.add_label(ticket_key, "blocked")
        except Exception as e:
            print(f"Warning: Could not add blocker to ticket {ticket_key} - {str(e)}")
            
    def _generate_status_comment(self, status, assignee):
        """Generate a realistic comment for the status transition"""
        comments = {
            "In Progress": [
                f"Starting work on this ticket. - {assignee['name']}",
                f"Beginning implementation. Will update with progress. - {assignee['name']}",
                f"Taking this one. - {assignee['name']}"
            ],
            "In Review": [
                f"Ready for code review. Main changes:\n- Implementation complete\n- Added unit tests\n- Updated documentation - {assignee['name']}",
                f"Completed implementation. Please review. - {assignee['name']}",
                f"PR created and ready for review. - {assignee['name']}"
            ],
            "QA": [
                f"Moving to QA. Test cases added in the description. - {assignee['name']}",
                f"Ready for testing. All automated tests passing. - {assignee['name']}",
                f"Implementation complete and verified in dev environment. Ready for QA. - {assignee['name']}"
            ],
            "Done": [
                f"All acceptance criteria met and verified. - {assignee['name']}",
                f"Completed and verified in staging environment. - {assignee['name']}",
                f"Ready for production deployment. - {assignee['name']}"
            ]
        }
        
        return random.choice(comments.get(status, [f"Moving to {status} - {assignee['name']}"])) 