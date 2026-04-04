import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from tavily import TavilyClient

app = FastAPI()

# Enable CORS for Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- YOUR API KEYS ---
TAVILY_API_KEY = "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"
GROQ_API_KEY = "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"

tavily = TavilyClient(api_key=TAVILY_API_KEY)

class AnalyzeRequest(BaseModel):
    url: str

def ask_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.1-8b-instant", # Latest stable model
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            print(f"Groq Error: {response.text}")
            return "AI Analysis is currently unavailable."

        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        return "The AI could not generate a response."
    except Exception as e:
        print(f"Groq Connection Error: {str(e)}")
        return "Failed to connect to AI engine."

@app.post("/analyze")
async def analyze_url(request: AnalyzeRequest):
    try:
        print(f"--- New Analysis Request for: {request.url} ---")
        
        # 1. Search for visibility data
        search_result = tavily.search(query=f"site:{request.url} visibility and citations", search_depth="advanced")
        context = str(search_result.get('results', []))
        
        # 2. Get AI reasoning
        ai_prompt = f"Analyze this search context: {context}. Explain why an AI would cite {request.url} for a UAE-based brand."
        reasoning = ask_groq(ai_prompt)
        
        # 3. Scoring Logic
        seo_score = 85 if len(context) > 100 else 40
        geo_score = 90 if ".ae" in request.url or "UAE" in context.upper() else 35

        return {
            "seo_score": seo_score,
            "geo_score": geo_score,
            "reasoning": reasoning
        }
    except Exception as e:
        print(f"Internal Server Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
