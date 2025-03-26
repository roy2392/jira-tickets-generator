# Jira Ticket Simulator

This project uses the Jira API and Claude AI to automatically generate and create realistic tickets and sprints in your Jira board.

## Features

- Generates realistic Epics with AI-powered content
- Creates time-boxed Sprints with meaningful goals
- Generates various ticket types (Stories, Tasks, Bugs) with AI-generated content
- Automatically assigns tickets to Epics and Sprints
- Configurable number of sprints and tickets per sprint

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
4. Configure your environment variables in `.env`:
   - `JIRA_SERVER`: Your Atlassian domain (e.g., https://your-domain.atlassian.net)
   - `JIRA_EMAIL`: Your Atlassian account email
   - `JIRA_API_TOKEN`: Your Jira API token (generate at https://id.atlassian.com/manage-profile/security/api-tokens)
   - `JIRA_PROJECT_KEY`: The key of your Jira project (e.g., "PROJ")
   - `CLAUDE_API_KEY`: Your Claude API key

## Usage

Run the simulator:
```bash
python main.py
```

This will:
1. Create a new Epic
2. Create 2 Sprints
3. Generate 3-5 tickets per Sprint
4. Assign all tickets to the Epic and their respective Sprints

## Requirements

- Python 3.8+
- Jira account with admin access to the project
- Claude API access
- Scrum board configured in your Jira project

## Notes

- The script uses the customfield IDs 10014 for Epic Link and 10016 for Story Points. These might need to be adjusted based on your Jira instance configuration.
- Make sure your Jira project has a Scrum board configured before running the script.
- The script generates realistic content using Claude AI, so each run will create unique tickets and descriptions. 