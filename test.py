import asyncio
from xai_sdk.v1 import Client

def sync_sample(prompt):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response = loop.run_until_complete(client.sampler.sample(prompt=prompt, stop_tokens=["\n"]))
    output = "".join(chunk.text for chunk in response)
    loop.close()
    return output

client = Client(api_key="your_api_key")
print(sync_sample("Test"))