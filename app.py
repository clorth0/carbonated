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

# Combined list of xAI and OpenAI models
AVAILABLE_MODELS = [
    {"name": "grok-beta", "provider": "xai"},
    {"name": "grok-3-beta", "provider": "xai"},
    {"name": "grok-3-mini-beta", "provider": "xai"},
    {"name": "gpt-4", "provider": "openai"},
    {"name": "gpt-4-turbo", "provider": "openai"},
    {"name": "gpt-3.5-turbo", "provider": "openai"}
]

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
            "img", "table", "thead", "tbody", "tr", "th", "td", "hr", "br"
        ]),
        attributes={
            "*": ["class", "style"],
            "a": ["href", "title", "target", "rel"],
            "img": ["src", "alt", "title", "width", "height"]
        },
        protocols=["http", "https", "mailto"],
        strip=False
    )

# Provider lookup
def get_provider_for_model(model_name: str) -> str:
    for model in AVAILABLE_MODELS:
        if model["name"] == model_name:
            return model["provider"]
    return "xai"  # Default to xAI

# GET route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "prompt": "",
        "result": "",
        "model": "grok-beta",
        "available_models": AVAILABLE_MODELS
    })

# POST route
@app.post("/", response_class=HTMLResponse)
async def generate(request: Request):
    form = await request.form()
    prompt = form.get("prompt", "").strip()
    selected_model = form.get("model", "grok-beta").strip()
    provider = get_provider_for_model(selected_model)
    output = ""

    if not prompt:
        output = "No prompt provided."
        return templates.TemplateResponse("index.html", {
            "request": request,
            "prompt": prompt,
            "result": output,
            "model": selected_model,
            "available_models": AVAILABLE_MODELS
        })

    # System prompt for consistent behavior
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that prioritizes truth above all. "
                "Always provide direct, candid, and intellectually honest responses. "
                "Avoid hedging. Clearly state when information is uncertain or not available. "
                "Support your answers with reasoning and facts when possible."
            )
        },
        {"role": "user", "content": prompt}
    ]

    # Determine API and headers
    try:
        if provider == "xai":
            api_url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": selected_model,
                "messages": messages,
                "stream": False,
                "temperature": 0.7
            }

        elif provider == "openai":
            api_url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": selected_model,
                "messages": messages,
                "temperature": 0.7
            }

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)

        logger.info(f"{provider.upper()} API status: {response.status_code}")

        if response.status_code == 200:
            raw = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            if not raw:
                output = "<p>No content returned. The model may have been unable to generate a reply.</p>"
            else:
                output = render_markdown_safe(raw)
        else:
            output = f"<p>Error {response.status_code}: {response.text}</p>"

    except httpx.TimeoutException:
        logger.error("Request timed out.")
        output = "Error: API request timed out."
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        output = f"Unexpected error: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "prompt": prompt,
        "result": output,
        "model": selected_model,
        "available_models": AVAILABLE_MODELS
    })
