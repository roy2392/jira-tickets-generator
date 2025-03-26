import os
from jira import JIRA
import json

class JiraManager:
    def __init__(self):
        self.jira = JIRA(
            server=os.getenv('JIRA_SERVER'),
            basic_auth=(os.getenv('JIRA_EMAIL'), os.getenv('JIRA_API_TOKEN'))
        )
        self.project_key = os.getenv('JIRA_PROJECT_KEY')
        
        # Get available fields
        self.available_fields = self._get_available_fields()

    def _get_available_fields(self):
        """Get all available custom fields and their IDs"""
        fields = {}
        try:
            for field in self.jira.fields():
                fields[field['name'].lower()] = field['id']
        except Exception as e:
            print(f"Warning: Could not fetch fields - {str(e)}")
        return fields

    def create_epic(self, epic_data):
        """Create an epic in Jira"""
        # Handle both string and Message object responses
        if hasattr(epic_data, 'content'):
            epic_data = epic_data.content
            
        epic_dict = json.loads(epic_data)
        
        epic = self.jira.create_issue(
            project=self.project_key,
            summary=epic_dict['summary'],
            description=epic_dict['description'],
            issuetype={'name': 'Epic'}
        )
        return epic

    def create_sprint(self, sprint_data):
        """Create a sprint in Jira if a Scrum board exists"""
        try:
            board_id = self._get_scrum_board_id()
            
            sprint = self.jira.create_sprint(
                name=sprint_data['name'],
                board_id=board_id,
                startDate=sprint_data['startDate'],
                endDate=sprint_data['endDate'],
                goal=sprint_data['goal']
            )
            return sprint
        except Exception as e:
            print(f"Warning: Could not create sprint - {str(e)}")
            return None

    def create_ticket(self, ticket_data, epic_key=None, sprint_id=None):
        """Create a ticket in Jira"""
        # Handle both string and Message object responses
        if hasattr(ticket_data, 'content'):
            ticket_data = ticket_data.content
            
        ticket_dict = json.loads(ticket_data)
        
        issue_dict = {
            'project': self.project_key,
            'summary': ticket_dict['summary'],
            'description': ticket_dict['description'],
            'issuetype': {'name': 'Story'}
        }
            
        # Add story points if available
        story_points_field = next((field_id for field_name, field_id in self.available_fields.items() 
                                 if 'story points' in field_name.lower()), None)
        if story_points_field:
            try:
                issue_dict[story_points_field] = float(ticket_dict['story_points'])
            except Exception:
                print("Warning: Could not set story points field")
        
        # Add epic link if available
        if epic_key:
            epic_link_field = next((field_id for field_name, field_id in self.available_fields.items() 
                                  if 'epic link' in field_name.lower()), None)
            if epic_link_field:
                try:
                    issue_dict[epic_link_field] = epic_key
                except Exception:
                    print("Warning: Could not set epic link field")
            
        issue = self.jira.create_issue(fields=issue_dict)
        
        if sprint_id:
            try:
                self.jira.add_issues_to_sprint(sprint_id, [issue.key])
            except Exception as e:
                print(f"Warning: Could not add ticket to sprint - {str(e)}")
            
        return issue

    def _get_scrum_board_id(self):
        """Get the first Scrum board ID for the project"""
        boards = self.jira.boards(projectKeyOrID=self.project_key, type='scrum')
        if not boards:
            raise Exception(f"No Scrum boards found for project {self.project_key}")
        return boards[0].id 