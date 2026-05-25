import httpx
from shared.settings import settings

async def web_search(query: str):
    if not settings.TAVILY_API_KEY:
        return {"error": "Missing Tavily API key"}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://tavily.com",
            json={"api_key": settings.TAVILY_API_KEY, "query": query, "max_results": 5},
            timeout=30.0
        )
        return response.json()
