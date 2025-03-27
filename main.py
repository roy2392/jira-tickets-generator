import os
from dotenv import load_dotenv
from ticket_generator import TicketGenerator
from jira_manager import JiraManager
from ticket_simulator import TicketSimulator
import random
import time
from jira import JIRA

def create_scrum_board(jira, project_key):
    # Check if board already exists
    boards = jira.boards()
    for board in boards:
        if board.name == f"{project_key} Scrum Board":
            print(f"Board {board.name} already exists with id {board.id}")
            return board.id

    # Create JQL for the board filter
    jql = f"project = {project_key} ORDER BY Rank ASC"
    
    # Create a filter for the board
    filter_name = f"{project_key} Board Filter"
    filter_config = {
        'name': filter_name,
        'description': f'Filter for {project_key} Scrum Board',
        'jql': jql,
        'favourite': True
    }
    
    try:
        # Create filter first
        new_filter = jira.create_filter(**filter_config)
        
        # Create board using REST API
        board_config = {
            'name': f"{project_key} Scrum Board",
            'type': 'scrum',
            'filterId': new_filter.id
        }
        
        # Use the REST API directly
        url = f"{jira.server_url}/rest/agile/1.0/board"
        response = jira._session.post(url, json=board_config)
        
        if response.status_code == 201:
            new_board = response.json()
            print(f"Created new Scrum board: {new_board['name']} with id {new_board['id']}")
            return new_board['id']
        else:
            print(f"Failed to create board. Status: {response.status_code}, Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error creating board: {str(e)}")
        return None

def main():
    # Load environment variables
    print("Loading environment variables...")
    load_dotenv(verbose=True)
    
    # Print all environment variables for debugging
    print("\nEnvironment variables loaded:")
    for key in ['JIRA_SERVER', 'JIRA_EMAIL', 'JIRA_API_TOKEN', 'JIRA_PROJECT_KEY']:
        print(f"{key}: {os.getenv(key)}")
    
    # Get and verify environment variables
    jira_server = os.getenv('JIRA_SERVER')
    jira_email = os.getenv('JIRA_EMAIL')
    jira_api_token = os.getenv('JIRA_API_TOKEN')
    project_key = os.getenv('JIRA_PROJECT_KEY')
    
    # Verify all required environment variables are present
    if not all([jira_server, jira_email, jira_api_token, project_key]):
        print("\nError: Missing required environment variables.")
        print(f"JIRA_SERVER: {'✓' if jira_server else '✗'}")
        print(f"JIRA_EMAIL: {'✓' if jira_email else '✗'}")
        print(f"JIRA_API_TOKEN: {'✓' if jira_api_token else '✗'}")
        print(f"JIRA_PROJECT_KEY: {'✓' if project_key else '✗'}")
        return
    
    print(f"\nConnecting to Jira server: {jira_server}")
    
    # Initialize Jira client
    jira = JIRA(
        server=jira_server,
        basic_auth=(jira_email, jira_api_token)
    )
    
    # Create Scrum board first
    board_id = create_scrum_board(jira, project_key)
    if not board_id:
        print("Failed to create or find Scrum board. Exiting.")
        return

    # Generate tickets
    ticket_generator = TicketGenerator(jira, project_key)
    epic = ticket_generator.create_epic()
    
    if epic:
        # Create sprints first
        sprints = ticket_generator.create_sprints(board_id)
        
        # Generate tickets and assign to sprints
        tickets = ticket_generator.generate_tickets(epic.key, sprints)
        
        # Simulate work on tickets
        simulator = TicketSimulator(jira, tickets)
        simulator.simulate_work()
        
        print("\nSimulation completed successfully!")
    else:
        print("Failed to create epic. Simulation aborted.")

if __name__ == "__main__":
    main() 