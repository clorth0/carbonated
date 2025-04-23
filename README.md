# Carbonated - Reddit Insight Analyzer

A lightweight FastAPI web application that allows users to analyze Reddit discussions using large language models from xAI (Grok) or OpenAI (GPT-3.5 / GPT-4). Users can enter a topic, question, or Reddit URL. The app retrieves relevant Reddit content via the Pushshift API and generates contextual insights using the selected model.

## Features

- Single input field for natural language queries or Reddit post URLs
- Retrieves relevant Reddit threads based on user input
- Uses xAI's Grok or OpenAI's GPT models for context-aware analysis
- Displays the Reddit content used for transparency
- Renders model responses as safe, sanitized HTML from markdown
- Customizable model selection

## Requirements

- Python 3.9 or higher
- Environment variables:
  - `XAI_API_KEY` for access to Grok via xAI
  - `OPENAI_API_KEY` for access to GPT via OpenAI

## Setup

1. Clone the repository:

git clone https://github.com/your-username/reddit-insight-analyzer.git
cd reddit-insight-analyzer

2. Create and Activate Environment

python3 -m venv venv
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

4. Create a .env file in the project root with the following contents:

XAI_API_KEY=your_xai_api_key
OPENAI_API_KEY=your_openai_api_key

5. Run the Application

uvicorn main:app --reload

6. Open your browser to http://127.0.0.1:8000/

