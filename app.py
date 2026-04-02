
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import subprocess
import re

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLInput(BaseModel):
    url: str


# -------- FETCH PAGE (FIXED) --------
def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
    }

    r = requests.get(url, headers=headers, timeout=10)

    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.title.string.strip() if soup.title else ""
    meta = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta["content"].strip() if meta and meta.get("content") else ""
    h1 = soup.find("h1")

    return {
        "title": title,
        "title_length": len(title),
        "meta": meta_desc,
        "meta_length": len(meta_desc),
        "has_h1": bool(h1)
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
        reasons.append("Page is not referenced in AI-generated answers")

    if data["title_length"] > 60:
        reasons.append("Title too long for AI summarization")
        fixes.append("Shorten title with clearer intent")

    if data["meta_length"] < 120:
        reasons.append("Meta lacks structured summary")
        fixes.append("Write concise factual meta description")

    if not data["has_h1"]:
        reasons.append("Missing strong content hierarchy")
        fixes.append("Add keyword-aligned H1")

    return {"reasons": reasons, "fixes": fixes}


# -------- AI --------
def run_ollama(prompt):
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3"],
            input=prompt,
            text=True,
            capture_output=True
        )
        return result.stdout.strip()
    except:
        return "AI suggestions unavailable"


# -------- MAIN --------
@app.post("/analyze")
def analyze(input: URLInput):
    url = input.url
    domain = extract_domain(url)

    data = fetch_page(url)

    # DEBUG (optional — helps you verify different pages)
    print("URL:", url)
    print("TITLE:", data["title"])

    seo, issues = seo_score(data)

    # FIXED QUERY (important)
    query = data["title"] + " " + data["meta"]

    citation = check_perplexity(query, domain)
    geo = geo_score(citation)

    final = int((seo * 0.6) + (geo * 0.4))

    geo_details = geo_reasoning(data, citation)

    ai_output = run_ollama(
        f"Improve SEO title: {data['title']} and meta: {data['meta']}"
    )

    return {
        "url": url,
        "seo_score": seo,
        "geo_score": geo,
        "final_score": final,
        "issues": issues,
        "citation_status": citation,
        "geo_details": geo_details,
        "ai_rewrite": ai_output
    }
