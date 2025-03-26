import os
from dotenv import load_dotenv
from ticket_generator import TicketGenerator
from jira_manager import JiraManager
from ticket_simulator import TicketSimulator
import random
import time

def main():
    # Load environment variables
    load_dotenv()
    
    # Get configuration from GitHub Actions inputs or use defaults
    num_sprints = int(os.getenv('INPUT_NUM_SPRINTS', '2'))
    max_tickets_per_sprint = int(os.getenv('INPUT_TICKETS_PER_SPRINT', '5'))
    
    # Initialize our classes
    ticket_gen = TicketGenerator()
    jira = JiraManager()
    simulator = TicketSimulator(jira)
    
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
        created_tickets = []
        ticket_types = ["Story", "Task", "Bug"]
        
        if created_sprints:
            # If we have sprints, create tickets in sprints
            for sprint in created_sprints:
                # Regular tickets
                num_tickets = random.randint(3, max_tickets_per_sprint)
                for _ in range(num_tickets):
                    ticket_type = random.choice(ticket_types)
                    ticket_data = ticket_gen.generate_ticket_content(ticket_type)
                    ticket = jira.create_ticket(
                        ticket_data,
                        epic_key=epic.key,
                        sprint_id=sprint.id
                    )
                    created_tickets.append(ticket)
                    print(f"Created {ticket_type}: {ticket.key}")
                
                # Add 1-2 incomplete tickets per sprint
                num_incomplete = random.randint(1, 2)
                for _ in range(num_incomplete):
                    ticket = simulator.create_incomplete_ticket(
                        epic_key=epic.key,
                        sprint_id=sprint.id
                    )
                    created_tickets.append(ticket)
                    print(f"Created Incomplete Ticket: {ticket.key}")
        else:
            # If no sprints, just create tickets under the epic
            # Regular tickets
            num_tickets = random.randint(6, max_tickets_per_sprint * 2)
            for _ in range(num_tickets):
                ticket_type = random.choice(ticket_types)
                ticket_data = ticket_gen.generate_ticket_content(ticket_type)
                ticket = jira.create_ticket(
                    ticket_data,
                    epic_key=epic.key
                )
                created_tickets.append(ticket)
                print(f"Created {ticket_type}: {ticket.key}")
            
            # Add 2-3 incomplete tickets
            num_incomplete = random.randint(2, 3)
            for _ in range(num_incomplete):
                ticket = simulator.create_incomplete_ticket(epic_key=epic.key)
                created_tickets.append(ticket)
                print(f"Created Incomplete Ticket: {ticket.key}")
        
        # 4. Simulate work on tickets
        print("\nSimulating work on tickets...")
        for ticket in created_tickets:
            # Skip some tickets to simulate incomplete work
            if random.random() < 0.7:  # 70% chance of working on a ticket
                simulator.simulate_work(ticket.key)
                # Add small delay to make transitions more realistic
                time.sleep(0.5)
                
        print("\nSimulation completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise  # Re-raise the exception to fail the GitHub Action

if __name__ == "__main__":
    main() 