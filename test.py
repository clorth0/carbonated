import httpx
import asyncio

async def test_xai():
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": "Bearer your_api_key", "Content-Type": "application/json"}
    payload = {
        "model": "grok-beta",
        "messages": [{"role": "user", "content": "Test"}],
        "stream": False
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        print(response.json())

asyncio.run(test_xai())