import random
from datetime import datetime, timedelta
import json
import time
import os

class TicketSimulator:
    def __init__(self, jira, tickets):
        self.jira = jira
        self.tickets = tickets
        # Get the authenticated user's email
        self.team_members = [os.getenv('JIRA_EMAIL')]
        
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
            # Assign to the authenticated user
            assignee = self.team_members[0]
            self.jira.assign_issue(ticket.key, assignee)
            
            # Add work log
            self.jira.add_worklog(
                ticket.key,
                timeSpentSeconds=random.randint(3600, 28800),  # 1-8 hours
                comment=f"Working on implementing the requested changes."
            )
            
            # Try to transition through different states
            transitions = self.jira.transitions(ticket.key)
            transition_ids = {t['name'].lower(): t['id'] for t in transitions}
            
            # Try common transition names
            for status in ['in progress', 'in review', 'qa', 'done']:
                if status in transition_ids:
                    try:
                        self.jira.transition_issue(ticket.key, transition_ids[status])
                        print(f"Moved {ticket.key} to {status.upper()}")
                    except Exception as e:
                        print(f"Warning: Could not find transition to {status.upper()} for {ticket.key}")
            
            # Add comments
            block_chance = int(os.getenv('INPUT_BLOCK_CHANCE', 30)) / 100
            if random.random() < block_chance:
                self.jira.add_comment(
                    ticket.key,
                    "Blocked: Waiting for dependency to be resolved."
                )
            else:
                self.jira.add_comment(
                    ticket.key,
                    "Implementation completed, ready for review."
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