import random
from datetime import datetime, timedelta
import json

class TicketSimulator:
    def __init__(self, jira_manager):
        self.jira = jira_manager
        self.team_members = [
            {"name": "John Smith", "role": "Developer", "velocity": 0.8},
            {"name": "Alice Johnson", "role": "Developer", "velocity": 1.0},
            {"name": "Bob Wilson", "role": "Developer", "velocity": 0.9},
            {"name": "Sarah Davis", "role": "QA", "velocity": 0.85},
            {"name": "Mike Brown", "role": "Tech Lead", "velocity": 0.7}
        ]
        
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
        
    def simulate_work(self, ticket_key, assignee=None, include_blockers=True):
        """Simulate work on a ticket by transitioning it through various states"""
        if not assignee:
            assignee = random.choice(self.team_members)
            
        # 20% chance of a ticket being blocked
        is_blocked = include_blockers and random.random() < 0.2
        
        if is_blocked:
            blocker = random.choice(self.common_blockers)
            self._add_blocker_comment(ticket_key, blocker)
            return
            
        # Simulate progress through states
        current_status = "To Do"
        for next_status in self.status_transitions[1:]:
            # 85% chance of moving to next state
            if random.random() < 0.85:
                self._transition_ticket(ticket_key, current_status, next_status, assignee)
                current_status = next_status
            else:
                break
                
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