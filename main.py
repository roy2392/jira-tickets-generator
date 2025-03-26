import os
from dotenv import load_dotenv
from ticket_generator import TicketGenerator
from jira_manager import JiraManager
import random

def main():
    # Load environment variables
    load_dotenv()
    
    # Get configuration from GitHub Actions inputs or use defaults
    num_sprints = int(os.getenv('INPUT_NUM_SPRINTS', '2'))
    max_tickets_per_sprint = int(os.getenv('INPUT_TICKETS_PER_SPRINT', '5'))
    
    # Initialize our classes
    ticket_gen = TicketGenerator()
    jira = JiraManager()
    
    try:
        # 1. Create an Epic
        print("Generating Epic...")
        epic_data = ticket_gen.generate_epic()
        epic = jira.create_epic(epic_data)
        print(f"Created Epic: {epic.key}")
        
        # 2. Create Sprints
        print("\nGenerating Sprints...")
        sprints_data = ticket_gen.generate_sprint_data(num_sprints=num_sprints)
        created_sprints = []
        for sprint_data in sprints_data:
            sprint = jira.create_sprint(sprint_data)
            if sprint:
                created_sprints.append(sprint)
                print(f"Created Sprint: {sprint.name}")
        
        # 3. Create Tickets
        print("\nGenerating Tickets...")
        ticket_types = ["Story", "Task", "Bug"]
        if created_sprints:
            # If we have sprints, create tickets in sprints
            for sprint in created_sprints:
                num_tickets = random.randint(3, max_tickets_per_sprint)
                for _ in range(num_tickets):
                    ticket_type = random.choice(ticket_types)
                    ticket_data = ticket_gen.generate_ticket_content(ticket_type)
                    ticket = jira.create_ticket(
                        ticket_data,
                        epic_key=epic.key,
                        sprint_id=sprint.id
                    )
                    print(f"Created {ticket_type}: {ticket.key}")
        else:
            # If no sprints, just create tickets under the epic
            num_tickets = random.randint(6, max_tickets_per_sprint * 2)  # Create more tickets since we don't have sprints
            for _ in range(num_tickets):
                ticket_type = random.choice(ticket_types)
                ticket_data = ticket_gen.generate_ticket_content(ticket_type)
                ticket = jira.create_ticket(
                    ticket_data,
                    epic_key=epic.key
                )
                print(f"Created {ticket_type}: {ticket.key}")
                
        print("\nSimulation completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise  # Re-raise the exception to fail the GitHub Action

if __name__ == "__main__":
    main() 