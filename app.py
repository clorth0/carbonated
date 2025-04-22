import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx

# Initialize FastAPI
app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Serve static files (like CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define the route for the main page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Define the route to process the form submission
@app.post("/submit/")
async def submit(request: Request, prompt: str = Form(...)):
    # xAI API endpoint URL
    xai_api_url = "https://api.x.ai/v1/chat/completions"
    
    # Set up headers with API key
    headers = {
        "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
        "Content-Type": "application/json"
    }

    # Set up the payload for the xAI API
    payload = {
        "model": "grok-beta",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "temperature": 0.7
    }

    # Send the prompt to the xAI API
    async with httpx.AsyncClient() as client:
        response = await client.post(xai_api_url, json=payload, headers=headers)
        
        # Check if the API request was successful
        if response.status_code == 200:
            result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response from API")
        else:
            result = f"Error: {response.status_code} - Unable to process the prompt"

    # Return the result to the user
    return templates.TemplateResponse("index.html", {"request": request, "prompt": prompt, "result": result})