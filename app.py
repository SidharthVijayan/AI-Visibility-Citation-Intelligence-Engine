from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bs4 import BeautifulSoup
import requests
import re
import asyncio
from playwright.async_api import async_playwright

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLInput(BaseModel):
    url: str


# -------- CACHE --------
cache = {}

def get_cache(url):
    return cache.get(url)

def set_cache(url, data):
    cache[url] = data


# -------- FETCH (PLAYWRIGHT) --------
async def fetch_page(url):
    cached = get_cache(url)
    if cached:
        return cached

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(url, timeout=60000)
            await page.wait_for_timeout(2000)

            html = await page.content()
            await browser.close()

        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.string.strip() if soup.title else ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta_tag["content"].strip() if meta_tag and meta_tag.get("content") else ""
        h1 = soup.find("h1")

        data = {
            "title": title,
            "title_length": len(title),
            "meta": meta_desc,
            "meta_length": len(meta_desc),
            "has_h1": bool(h1)
        }

        set_cache(url, data)
        return data

    except Exception as e:
        print("FETCH ERROR:", e)
        return {
            "title": "Error",
            "title_length": 5,
            "meta": "",
            "meta_length": 0,
            "has_h1": False
        }


# -------- SEO --------
def seo_score(data):
    score = 100
    issues = []

    if data["title_length"] > 60:
        issues.append("Title too long")
        score -= 15

    if data["meta_length"] < 120:
        issues.append("Weak meta description")
        score -= 15

    if not data["has_h1"]:
        issues.append("Missing H1")
        score -= 20

    return max(score, 0), issues


# -------- GEO --------
def extract_domain(url):
    return re.findall(r"https?://(?:www\.)?([^/]+)", url)[0]


def check_perplexity(query, domain):
    try:
        r = requests.get(f"https://www.perplexity.ai/search?q={query}")
        return "CITED" if domain in r.text.lower() else "NOT CITED"
    except:
        return "UNKNOWN"


def geo_score(status):
    return {"CITED": 90, "NOT CITED": 40}.get(status, 60)


def geo_reasoning(data, citation):
    reasons = []
    fixes = []

    if citation == "NOT CITED":
        reasons.append("Page not referenced in AI answers")

    if data["title_length"] > 60:
        reasons.append("Title too long for AI summarization")
        fixes.append("Shorten title")

    if data["meta_length"] < 120:
        reasons.append("Meta lacks structured summary")
        fixes.append("Improve meta description")

    if not data["has_h1"]:
        reasons.append("Missing strong H1 structure")
        fixes.append("Add keyword-aligned H1")

    return {"reasons": reasons, "fixes": fixes}


# -------- SINGLE --------
@app.post("/analyze")
async def analyze(input: URLInput):

    url = input.url
    domain = extract_domain(url)

    data = await fetch_page(url)

    seo, issues = seo_score(data)

    query = data["title"] + " " + data["meta"]

    citation = check_perplexity(query, domain)
    geo = geo_score(citation)

    final = int((seo * 0.6) + (geo * 0.4))

    geo_details = geo_reasoning(data, citation)

    return {
        "url": url,
        "seo_score": seo,
        "geo_score": geo,
        "final_score": final,
        "issues": issues,
        "citation_status": citation,
        "geo_details": geo_details
    }


# -------- BATCH --------
@app.post("/batch-analyze")
async def batch_analyze(urls: list[str]):

    tasks = [fetch_page(url) for url in urls]
    pages = await asyncio.gather(*tasks)

    results = []

    for i, data in enumerate(pages):
        url = urls[i]
        domain = extract_domain(url)

        seo, _ = seo_score(data)
        query = data["title"] + " " + data["meta"]

        citation = check_perplexity(query, domain)
        geo = geo_score(citation)

        final = int((seo * 0.6) + (geo * 0.4))

        results.append({
            "url": url,
            "score": final,
            "seo": seo,
            "geo": geo,
            "citation": citation
        })

    return {"results": results}


# -------- KEYWORD --------
@app.post("/keyword-check")
def keyword_check(keyword: str, domains: list[str]):

    results = {}

    try:
        r = requests.get(f"https://www.perplexity.ai/search?q={keyword}")
        text = r.text.lower()

        for d in domains:
            results[d] = "CITED" if d in text else "NOT CITED"

    except:
        for d in domains:
            results[d] = "UNKNOWN"

    return results
