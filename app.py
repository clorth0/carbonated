import os
import re
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import httpx
import markdown
import bleach
import logging

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

AVAILABLE_MODELS = [
    {"name": "grok-beta", "provider": "xai"},
    {"name": "grok-3-beta", "provider": "xai"},
    {"name": "grok-3-mini-beta", "provider": "xai"},
    {"name": "gpt-4", "provider": "openai"},
    {"name": "gpt-4-turbo", "provider": "openai"},
    {"name": "gpt-3.5-turbo", "provider": "openai"}
]

def get_provider_for_model(model_name: str) -> str:
    for model in AVAILABLE_MODELS:
        if model["name"] == model_name:
            return model["provider"]
    return "xai"

def annotate_sources(text: str) -> str:
    return text.replace("(Reddit)", "<sup data-tooltip='Content derived from Reddit posts'>[Reddit]</sup>")\
               .replace("(DuckDuckGo)", "<sup data-tooltip='Content derived from DuckDuckGo search'>[DuckDuckGo]</sup>")

def render_markdown_safe(md_text: str) -> str:
    md_text = annotate_sources(md_text)
    html = markdown.markdown(
        md_text,
        extensions=["fenced_code", "codehilite", "tables", "nl2br", "sane_lists"]
    )
    return bleach.clean(
        html,
        tags=bleach.sanitizer.ALLOWED_TAGS.union([
            "p", "pre", "code", "span", "h1", "h2", "h3", "h4", "h5", "h6",
            "img", "table", "thead", "tbody", "tr", "th", "td", "hr", "br",
            "sup", "blockquote", "details", "summary"
        ]),
        attributes={
            "*": ["class", "style"],
            "a": ["href", "title", "target", "rel"],
            "img": ["src", "alt", "title", "width", "height"],
            "sup": ["data-tooltip"],
            "details": ["open"],
            "summary": []
        },
        protocols=["http", "https", "mailto"],
        strip=False
    )

async def fetch_reddit_content(query: str) -> (str, list):
    posts_summary = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        parsed = urlparse(query)
        if "reddit.com" in parsed.netloc and "comments" in parsed.path:
            post_id_match = re.search(r"/comments/([a-z0-9]+)/", parsed.path)
            if post_id_match:
                post_id = post_id_match.group(1)
                url = f"https://api.pushshift.io/reddit/submission/search/?ids={post_id}"
                res = await client.get(url)
                if res.status_code == 200:
                    posts = res.json().get("data", [])
                    if posts:
                        post = posts[0]
                        summary = f"**{post.get('title', '')}**\n{post.get('selftext', '')}"
                        posts_summary.append(summary)
                        return summary, posts_summary
                return "", []

        search_url = "https://api.pushshift.io/reddit/search/submission"
        params = {"q": query, "size": 5, "sort": "desc", "sort_type": "score"}
        res = await client.get(search_url, params=params)
        if res.status_code == 200:
            posts = res.json().get("data", [])
            if posts:
                summary = "\n\n".join(
                    f"**{p.get('title', '')}**\n{p.get('selftext', '')}" for p in posts
                )
                posts_summary = [f"**{p.get('title', '')}**\n{p.get('selftext', '')}" for p in posts]
                return summary, posts_summary
        return "", []

async def fetch_duckduckgo_context(query: str) -> str:
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            abstract = data.get("Abstract", "")
            related_topics = data.get("RelatedTopics", [])
            related_texts = "\n".join(t.get("Text", "") for t in related_topics if "Text" in t)
            return abstract + "\n\n" + related_texts if abstract or related_texts else ""
    return ""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_input": "",
        "result": "",
        "model": "grok-beta",
        "available_models": AVAILABLE_MODELS,
        "threads": []
    })

@app.post("/", response_class=HTMLResponse)
async def generate(request: Request):
    form = await request.form()
    user_input = form.get("user_input", "").strip()
    selected_model = form.get("model", "grok-beta").strip()
    provider = get_provider_for_model(selected_model)
    output = ""

    if not user_input:
        output = "Please enter a topic, Reddit post URL, or a question."
        return templates.TemplateResponse("index.html", {
            "request": request,
            "user_input": user_input,
            "result": output,
            "model": selected_model,
            "available_models": AVAILABLE_MODELS,
            "threads": []
        })

    reddit_context, threads = await fetch_reddit_content(user_input)
    duckduckgo_context = await fetch_duckduckgo_context(user_input)

    combined_context = ""
    if reddit_context:
        combined_context += f"Reddit context:\n{reddit_context}\n\n"
    if duckduckgo_context:
        combined_context += f"DuckDuckGo summary:\n{duckduckgo_context}\n\n"

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use the provided Reddit and DuckDuckGo content as sources "
                "when relevant. When referencing something that comes from Reddit or DuckDuckGo, clearly annotate it "
                "by adding (Reddit) or (DuckDuckGo) in parentheses. If no source is used, do not add anything."
            )
        },
        {
            "role": "user",
            "content": combined_context + f"User input:\n{user_input}"
        }
    ]

    try:
        if provider == "xai":
            api_url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {os.getenv('XAI_API_KEY')}",
                "Content-Type": "application/json"
            }
        else:
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

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            raw = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            output = render_markdown_safe(raw) if raw else "No content returned from the model."
        else:
            output = f"<p>Error {response.status_code}: {response.text}</p>"

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        output = f"Unexpected error: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_input": user_input,
        "result": output,
        "model": selected_model,
        "available_models": AVAILABLE_MODELS,
        "threads": threads
    })
