# Carbonated - SourceIQ

**Carbonated - SourceIQ** is a lightweight FastAPI web application that enables users to analyze online discussions using large language models from xAI (Grok) or OpenAI (GPT-3.5 / GPT-4). Given a topic, question, or Reddit URL, SourceIQ retrieves relevant Reddit content (via the Pushshift API) and DuckDuckGo search summaries, then generates contextualized insights using the selected AI model — with transparent source annotations.

## Features

- Single input for natural language queries or Reddit URLs
- Retrieves top Reddit threads and DuckDuckGo search context
- Supports xAI’s Grok and OpenAI’s GPT-4, GPT-4 Turbo, and GPT-3.5
- Clearly annotates which parts of the response are based on Reddit or DuckDuckGo
- Displays retrieved source content for transparency
- Renders model responses as safe, styled HTML with markdown support
- Supports model selection via dropdown

## Requirements

- Python 3.9 or higher
- Environment variables:
  - `XAI_API_KEY` for access to Grok via xAI
  - `OPENAI_API_KEY` for access to GPT via OpenAI

## Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/carbonated.git
    cd sourceiq
    ```

2. Create and activate a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the project root:

    ```env
    XAI_API_KEY=your_xai_api_key
    OPENAI_API_KEY=your_openai_api_key
    ```

5. Run the application:

    ```bash
    uvicorn app:app --reload
    ```

6. Open your browser to:

    ```
    http://127.0.0.1:8000/
    ```
---
