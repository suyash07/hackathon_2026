# Conference Search (Cloud Native Hackathon – Elasticsearch track)

> Project description goes here.

## Features
- [ ] Talk search by meaning
- [ ] Hallway matchmaker
- [ ] Conference assistant (RAG)

## Setup
1. Start Elasticsearch + Kibana locally (needs Docker):
   `curl -fsSL https://elastic.co/start-local | sh`
2. Create a virtual environment:
   ```bash
   python3 -m venv hackathon
   source hackathon/bin/activate
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your values.
4. Check everything connects: `python src/check_setup.py`

## Architecture
_Add during the hackathon._

## Data
_Describe data sources here._

## AI use disclosure
This project was built with help from Claude (Anthropic) as a coding assistant.
