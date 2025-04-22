import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import httpx
import markdown
import bleach
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Markdown conversion and sanitization
def render_markdown_safe(md_text: str) -> str:
    html = markdown.markdown(
        md_text,
        extensions=["fenced_code", "codehilite", "tables", "nl2br", "sane_lists"]
    )
    return bleach.clean(
        html,
        tags=bleach.sanitizer.ALLOWED_TAGS.union([
            "p", "pre", "code", "span", "h1", "h2", "h3", "h4", "h5", "h6",
            "img", "table", "thead", "tbody", "tr", "th", "td", "hr"
        ]),
        attributes={
            "*": ["class", "style"],
            "a": ["href", "title", "target", "rel"],
            "img": ["src", "alt", "title", "width", "height"]
        },
        protocols=["http", "https", "mailto"],
        strip=False
    )

# GET route for homepage
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "prompt": "",
        "result": ""
    })

# POST route to process form and call xAI
@app.post("/", response_class=HTMLResponse)
async def generate(request: Request):
    form = await request.form()
    prompt = form.get("prompt", "").strip()
    output = ""

    if not prompt:
        output = "No prompt provided."
        return templates.TemplateResponse("index.html", {
            "request": request,
            "prompt": prompt,
            "result": output
        })

    # xAI API config
    xai_api_url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "grok-beta",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": 0.7
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(xai_api_url, json=payload, headers=headers)

        logger.info(f"xAI API status: {response.status_code}")

        if response.status_code == 200:
            raw = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            output = render_markdown_safe(raw)
        else:
            output = f"<p>Error {response.status_code}: {response.text}</p>"

    except httpx.TimeoutException:
        output = "Error: xAI API request timed out."
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        output = f"Unexpected error: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "prompt": prompt,
        "result": output
    })
