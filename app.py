from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import subprocess
import re

app = FastAPI()

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
    suggestions = []

    if data["title_length"] > 60:
        issues.append("Title too long")
        suggestions.append("Keep title under 60 chars")

    if data["meta_length"] < 120:
        issues.append("Weak meta description")
        suggestions.append("Write compelling 120–155 char meta")

    if not data["has_h1"]:
        issues.append("Missing H1")
        suggestions.append("Add keyword-rich H1")

    return issues, suggestions


# -------- OLLAMA AI --------
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
        return "AI unavailable"


def ai_rewrite(data):
    prompt = f"""
    Improve SEO for:
    Title: {data['title']}
    Meta: {data['meta']}

    Return:
    - Better title
    - Better meta
    - Why it improves CTR
    """
    return run_ollama(prompt)


# -------- GEO CITATION ENGINE --------
def extract_domain(url):
    return re.findall(r"https?://(?:www\.)?([^/]+)", url)[0]


def check_perplexity(query, domain):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://www.perplexity.ai/search?q={query}"

    try:
        r = requests.get(url, headers=headers, timeout=10)
        text = r.text.lower()

        if domain in text:
            return "CITED"
        return "NOT CITED"
    except:
        return "UNKNOWN"


def geo_score(citation):
    if citation == "CITED":
        return 8
    elif citation == "NOT CITED":
        return 3
    return 5


# -------- BOT STRATEGY --------
def bot_strategy(url):
    if "webmd" in url:
        return {
            "training": "BLOCK",
            "rag": "ALLOW",
            "reason": "Protect medical IP, allow AI citation"
        }
    return {
        "training": "ALLOW",
        "rag": "ALLOW",
        "reason": "General content"
    }


# -------- MAIN --------
@app.post("/analyze")
def analyze(input: URLInput):
    url = input.url
    domain = extract_domain(url)

    try:
        data = fetch_page(url)
    except:
        return {"error": "Fetch failed"}

    issues, suggestions = ctr_analysis(data)
    ai_output = ai_rewrite(data)

    query = data["title"][:60]
    citation = check_perplexity(query, domain)

    return {
        "url": url,

        "seo": data,
        "issues": issues,
        "suggestions": suggestions,

        "ai_rewrite": ai_output,

        "geo": {
            "citation_status": citation,
            "geo_score": geo_score(citation),
            "query_used": query
        },

        "bot_strategy": bot_strategy(url),

        "tracker": {
            "url": url,
            "geo_score": geo_score(citation),
            "priority": "HIGH" if len(issues) > 1 else "MEDIUM"
        }
    }
