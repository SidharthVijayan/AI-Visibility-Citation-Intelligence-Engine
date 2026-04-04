import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from tavily import TavilyClient

app = FastAPI()

# Allow your Chrome Extension to talk to this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HARDCODED KEYS (No .env needed) ---
TAVILY_API_KEY = "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"
GROQ_API_KEY = "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"

tavily = TavilyClient(api_key=TAVILY_API_KEY)

class AnalyzeRequest(BaseModel):
    url: str

def ask_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    # This check prevents the 'choices' KeyError
    if response.status_code != 200:
        print(f"Groq Error: {response.text}")
        return "AI Analysis temporarily unavailable."
    return response.json()['choices'][0]['message']['content']

@app.post("/analyze")
async def analyze_url(request: AnalyzeRequest):
    try:
        # 1. Search for the URL's presence online
        search_result = tavily.search(query=f"site:{request.url} visibility and citations", search_depth="advanced")
        context = str(search_result.get('results', []))
        
        # 2. Get AI Reasoning from Groq
        reasoning = ask_groq(f"Based on: {context}, why would an AI cite {request.url}? Provide a short SEO summary.")
        
        # 3. Simple scoring logic
        seo_score = 85 if "results" in context else 40
        geo_score = 75 if ".ae" in request.url or "UAE" in context else 30

        return {
            "seo_score": seo_score,
            "geo_score": geo_score,
            "reasoning": reasoning
        }
    except Exception as e:
        print(f"Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
