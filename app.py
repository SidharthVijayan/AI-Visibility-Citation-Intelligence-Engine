import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

load_dotenv()
app = FastAPI()

# --- THE FIX: This tells the "bouncer" to let your extension in ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you'd put your extension ID here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

class SEORequest(BaseModel):
    url: str

async def get_clean_content(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            html = await page.content()
            title = await page.title()
            return html, title
        except:
            return None, "Content Restricted"
        finally:
            await browser.close()

def ask_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

@app.post("/analyze")
async def analyze_url(request: SEORequest):
    html, title = await get_clean_content(request.url)
    if not html:
        raise HTTPException(status_code=400, detail="Scraping failed")

    tavily_res = requests.post("https://api.tavily.com/search", json={
        "api_key": TAVILY_API_KEY,
        "query": f"Is {title} a trusted source?",
        "search_depth": "basic"
    }).json()

    context = str(tavily_res.get("results", []))[:3000]
    reasoning = ask_groq(f"Based on: {context}, why would an AI cite {request.url}?")

    return {
        "url": request.url,
        "seo_score": 85,
        "geo_score": 80,
        "reasoning": reasoning
    }
