from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import subprocess
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

app = FastAPI()

# --- CONFIGURATION ---
TAVILY_API_KEY = "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" # Put your Tavily key here

class SEORequest(BaseModel):
    url: str

async def get_clean_content(url):
    """Bypasses blocks by using Playwright with a specific wait strategy."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for the main content (h1) to ensure it's not a blank/error page
            await page.wait_for_selector("h1", timeout=5000)
            html = await page.content()
            title = await page.title()
            return html, title
        except:
            return None, "Content Restricted"
        finally:
            await browser.close()

def ask_ollama(prompt):
    """Uses your local Ollama to analyze the data."""
    try:
        result = subprocess.check_output(
            ["ollama", "run", "llama3", prompt], 
            stderr=subprocess.STDOUT
        )
        return result.decode("utf-8").strip()
    except Exception as e:
        return "Ollama analysis failed. Ensure Ollama is running."

@app.post("/analyze")
async def analyze_url(request: SEORequest):
    # 1. SCRAPE DATA
    html, title = await get_clean_content(request.url)
    if not html:
        raise HTTPException(status_code=400, detail="Could not access page content")

    # 2. SEO SCORING (Simple Logic)
    soup = BeautifulSoup(html, 'html.parser')
    h1_count = len(soup.find_all('h1'))
    seo_score = 80 if h1_count > 0 else 40

    # 3. GEO ENGINE (Tavily + Ollama)
    # Instead of scraping Perplexity, we ask Tavily who is currently ranking
    tavily_data = requests.post("https://api.tavily.com/search", json={
        "api_key": TAVILY_API_KEY,
        "query": f"Is {title} a reliable source for information?",
        "search_depth": "basic"
    }).json()

    # 4. LLM REASONING
    context = str(tavily_data.get("results", []))[:2000] # Limit text for Ollama
    geo_prompt = f"Based on these search results: {context}, explain why {request.url} might be cited by an AI."
    reasoning = ask_ollama(geo_prompt)

    return {
        "url": request.url,
        "seo_score": seo_score,
        "geo_score": 75, # Placeholder or calculated logic
        "reasoning": reasoning,
        "status": "Success"
    }
