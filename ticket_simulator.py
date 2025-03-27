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
        """Create or get team members for the simulation."""
        team_members = []
        
        # Define team structure based on environment variables
        team_structure = {
            'Developer': int(os.getenv('INPUT_NUM_DEVELOPERS', 4)),
            'QA Engineer': int(os.getenv('INPUT_NUM_QA', 2)),
            'Tech Lead': int(os.getenv('INPUT_NUM_TECH_LEADS', 1)),
            'Product Owner': int(os.getenv('INPUT_NUM_PRODUCT_OWNERS', 1)),
            'Scrum Master': int(os.getenv('INPUT_NUM_SCRUM_MASTERS', 1))
        }
        
        fake = Faker()
        
        try:
            # Get all existing users first
            existing_users = self.jira.search_users(query='')
            existing_emails = {user.emailAddress for user in existing_users}
            
            # Create users for each role
            for role, count in team_structure.items():
                for _ in range(count):
                    first_name = fake.first_name()
                    last_name = fake.last_name()
                    email = f"{first_name.lower()}.{last_name.lower()}@example.com"
                    
                    # Skip if user already exists
                    if email in existing_emails:
                        continue
                    
                    try:
                        # Create user with product access
                        user_data = {
                            'displayName': f"{first_name} {last_name}",
                            'emailAddress': email,
                            'name': email,  # Using email as username
                            'password': fake.password(),
                            'notification': 'DONT_NOTIFY',
                            'applicationKeys': ['jira-software']  # Specify Jira Software access
                        }
                        
                        new_user = self.jira._session.post(
                            f"{self.jira.server_url}/rest/api/2/user",
                            json=user_data
                        )
                        
                        if new_user.status_code == 201:
                            team_members.append({
                                'email': email,
                                'role': role
                            })
                        else:
                            print(f"Warning: Could not create user {email}: {new_user.text}")
                    except Exception as e:
                        print(f"Warning: Could not create user {email}: {str(e)}")
            
            if not team_members:
                print("\nWarning: Using authenticated user as fallback")
                # Get the current user's email
                myself = self.jira.myself()
                team_members.append({
                    'email': myself['emailAddress'],
                    'role': 'Developer'  # Default role
                })
            
            return team_members
        
        except Exception as e:
            print(f"Error creating team members: {str(e)}")
            print("Using authenticated user as fallback")
            # Get the current user's email
            myself = self.jira.myself()
            return [{
                'email': myself['emailAddress'],
                'role': 'Developer'  # Default role
            }]

    def simulate_work(self):
        """Simulate work being done on tickets."""
        # Get all transitions
        transitions = {
            'To Do': 'Open',
            'In Progress': 'Start Progress',
            'In Review': 'Review',
            'QA': 'QA Review',
            'Done': 'Done'
        }
        
        # Create team members if not already created
        if not hasattr(self, 'team_members'):
            self.team_members = self.create_or_get_team_members()
        
        if not self.team_members:
            print("Error: No team members available for simulation")
            return
        
        # Process each ticket
        for ticket in self.tickets:
            try:
                # Get available transitions for this ticket
                available_transitions = self.jira.transitions(ticket.key)
                transition_ids = {t['name']: t['id'] for t in available_transitions}
                
                # Assign to random team member
                assignee = random.choice(self.team_members)
                self.jira.assign_issue(ticket.key, assignee['email'])
                
                # Add work log with assignee's name
                self.jira.add_worklog(
                    ticket.key,
                    timeSpentSeconds=random.randint(3600, 28800),  # 1-8 hours
                    comment=f"{assignee['email'].split('@')[0]} working on implementing the requested changes."
                )
                
                # Move through workflow states
                for status in ['In Progress', 'Done']:
                    if status in transition_ids:
                        try:
                            self.jira.transition_issue(ticket.key, transition_ids[status])
                            print(f"Moved {ticket.key} to {status.upper()} (Assignee: {assignee['email']})")
                        except Exception as e:
                            print(f"Warning: Could not find transition to {status.upper()} for {ticket.key}")
                            continue
                        
                        # Add comments based on status
                        comment = self._get_status_comment(status, assignee)
                        self.jira.add_comment(ticket.key, comment)
                        
                        # Simulate work time
                        time.sleep(0.5)  # Small delay to prevent rate limiting
                        
                        # Randomly decide if ticket gets blocked
                        if status == 'In Progress' and random.randint(1, 100) <= int(os.getenv('INPUT_BLOCK_CHANCE', 30)):
                            # Choose a random team member as blocker (not the assignee)
                            other_members = [m for m in self.team_members if m['email'] != assignee['email']]
                            if other_members:  # Only add blocker if there are other team members
                                blocker = random.choice(other_members)
                                self.jira.add_comment(
                                    ticket.key,
                                    f"Blocked: {blocker['email'].split('@')[0]} needs to complete dependent work first."
                                )
                        else:
                            # Add code review comment
                            other_members = [m for m in self.team_members if m['email'] != assignee['email']]
                            if other_members:  # Only add review comment if there are other team members
                                reviewer = random.choice(other_members)
                                self.jira.add_comment(
                                    ticket.key,
                                    f"Implementation completed by {assignee['email'].split('@')[0]}, requesting review from {reviewer['email'].split('@')[0]}."
                                )
            except Exception as e:
                print(f"Error simulating work on {ticket.key}: {str(e)}")
                continue

    def _get_status_comment(self, status, assignee):
        """Get a random comment for the given status."""
        comments = {
            "In Progress": [
                f"Starting work on this ticket. - {assignee['email'].split('@')[0]}",
                f"Beginning implementation. Will update with progress. - {assignee['email'].split('@')[0]}",
                f"Taking this one. - {assignee['email'].split('@')[0]}"
            ],
            "In Review": [
                f"Ready for code review. Main changes:\n- Implementation complete\n- Added unit tests\n- Updated documentation - {assignee['email'].split('@')[0]}",
                f"Completed implementation. Please review. - {assignee['email'].split('@')[0]}",
                f"PR created and ready for review. - {assignee['email'].split('@')[0]}"
            ],
            "QA": [
                f"Moving to QA. Test cases added in the description. - {assignee['email'].split('@')[0]}",
                f"Ready for testing. All automated tests passing. - {assignee['email'].split('@')[0]}",
                f"Implementation complete and verified in dev environment. Ready for QA. - {assignee['email'].split('@')[0]}"
            ],
            "Done": [
                f"All acceptance criteria met and verified. - {assignee['email'].split('@')[0]}",
                f"Completed and verified in staging environment. - {assignee['email'].split('@')[0]}",
                f"Ready for production deployment. - {assignee['email'].split('@')[0]}"
            ]
        }
        
        return random.choice(comments.get(status, [f"Moving to {status} - {assignee['email'].split('@')[0]}"]))

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
                f"Starting work on this ticket. - {assignee['email'].split('@')[0]}",
                f"Beginning implementation. Will update with progress. - {assignee['email'].split('@')[0]}",
                f"Taking this one. - {assignee['email'].split('@')[0]}"
            ],
            "In Review": [
                f"Ready for code review. Main changes:\n- Implementation complete\n- Added unit tests\n- Updated documentation - {assignee['email'].split('@')[0]}",
                f"Completed implementation. Please review. - {assignee['email'].split('@')[0]}",
                f"PR created and ready for review. - {assignee['email'].split('@')[0]}"
            ],
            "QA": [
                f"Moving to QA. Test cases added in the description. - {assignee['email'].split('@')[0]}",
                f"Ready for testing. All automated tests passing. - {assignee['email'].split('@')[0]}",
                f"Implementation complete and verified in dev environment. Ready for QA. - {assignee['email'].split('@')[0]}"
            ],
            "Done": [
                f"All acceptance criteria met and verified. - {assignee['email'].split('@')[0]}",
                f"Completed and verified in staging environment. - {assignee['email'].split('@')[0]}",
                f"Ready for production deployment. - {assignee['email'].split('@')[0]}"
            ]
        }
        
        return random.choice(comments.get(status, [f"Moving to {status} - {assignee['email'].split('@')[0]}"])) 