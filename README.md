# xAI Prompt Tester

A lightweight FastAPI web app that lets you test prompts against xAI's Grok model. Prompts are submitted through a web interface, sent to the xAI API, and responses are returned as rendered, sanitized markdown.

---

## Features

- Connects securely to xAI's API using an environment variable
- Accepts user-submitted prompts via a web form
- Supports markdown rendering with HTML sanitization for safety
- Displays output styled with custom CSS
- Easily extendable to support image generation, maps, or other AI integrations

---

## Requirements

- Python 3.9+
- An xAI API key
- Dependencies listed in `requirements.txt`

---

## Setup

1. Clone the repo:

```bash
git clone https://github.com/your-username/xai-prompt-tester.git
cd xai-prompt-tester
