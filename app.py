from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import subprocess
import re

app = FastAPI()

# ✅ CORS FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class URLInput(BaseModel):
    url: str


# -------- FETCH PAGE --------
def fetch_page(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.title.string.strip() if soup.title else ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    meta_desc = meta_tag["content"].strip() if meta_tag and meta_tag.get("content") else ""
    h1 = soup.find("h1")

    return {
        "title": title,
        "title_length": len(title),
        "meta": meta_desc,
        "meta_length": len(meta_desc),
        "has_h1": bool(h1)
    }


# -------- CTR + SEO --------
def ctr_analysis(data):
    issues = []
    score = 100

    if data["title_length"] > 60:
        issues.append("Title too long")
        score -= 15

    if data["meta_length"] < 120:
        issues.append("Weak meta description")
        score -= 15

    if not data["has_h1"]:
        issues.append("Missing H1")
        score -= 20

    return issues, max(score, 0)


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


def ai_rewrite(data):
    prompt = f"""
    Improve SEO:
    Title: {data['title']}
    Meta: {data['meta']}

    Give improved versions.
    """
    return run_ollama(prompt)


# -------- GEO --------
def extract_domain(url):
    return re.findall(r"https?://(?:www\.)?([^/]+)", url)[0]


def check_perplexity(query, domain):
    try:
        r = requests.get(f"https://www.perplexity.ai/search?q={query}")
        if domain in r.text.lower():
            return "CITED"
        return "NOT CITED"
    except:
        return "UNKNOWN"


def geo_score(status):
    return {"CITED": 90, "NOT CITED": 40}.get(status, 60)


# -------- MAIN --------
@app.post("/analyze")
def analyze(input: URLInput):
    url = input.url
    domain = extract_domain(url)

    data = fetch_page(url)
    issues, seo_score = ctr_analysis(data)
    ai_output = ai_rewrite(data)

    query = data["title"][:60]
    citation = check_perplexity(query, domain)
    geo = geo_score(citation)

    final_score = int((seo_score * 0.6) + (geo * 0.4))

    return {
        "url": url,
        "seo_score": seo_score,
        "geo_score": geo,
        "final_score": final_score,
        "issues": issues,
        "ai_rewrite": ai_output,
        "citation_status": citation
    }
