import os
import requests
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

# Initialize App
app = FastAPI(title="Aryavarta Safe Engine", redirect_slashes=False)

# Allow ALL connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
groq_client = Groq(api_key=GROQ_API_KEY)

# ⬇️ PASTE YOUR GOOGLE WEB APP URL HERE ⬇️
GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbxZcBzUwmU42j7IxbdJKnjTBggMHpEfBiUeZRnRwnOM9LFYGveytTEwem2zD2NsgPHD/exec"

# STABLE MODEL (Classic ID that never crashes)
MODEL_ID = "llama3-70b-8192"

class StandardInput(BaseModel):
    client_name: str
    # Flexible fields to prevent validation errors
    fault_description: str = ""
    raw_whatsapp_text: str = ""
    raw_requirements: str = ""
    image_base64: str = ""

@app.get("/")
def home():
    return {"status": "online", "message": "Aryavarta Backend Active"}

def run_ai_and_store(service, client, text):
    try:
        # 1. AI Generation
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"You are an expert for {service}. Be concise."},
                {"role": "user", "content": text}
            ],
            model=MODEL_ID,
            temperature=0.1
        )
        ai_output = completion.choices[0].message.content

        # 2. Google Sheets Storage
        try:
            requests.post(GOOGLE_SHEET_WEBHOOK, json={
                "service_type": service,
                "client_name": client,
                "input_text": text,
                "ai_output": ai_output
            }, timeout=5)
        except Exception as e:
            print(f"Sheet Error: {e}")

        return ai_output
    except Exception as e:
        return f"System Error: {str(e)}"

@app.post("/api/site-engineer")
@app.post("/api/site-engineer/")
def site_engineer(data: StandardInput):
    text = data.fault_description
    if data.image_base64:
        text += " [Image Attached]"
    result = run_ai_and_store("Site Engineer", data.client_name, text)
    return {"status": "success", "ai_diagnostic": result}

@app.post("/api/sundry-procurement")
@app.post("/api/sundry-procurement/")
def sundry(data: StandardInput):
    result = run_ai_and_store("Sundry Procurement", data.client_name, data.raw_whatsapp_text)
    return {"status": "success", "structured_list": result}

@app.post("/api/turnkey-panel")
@app.post("/api/turnkey-panel/")
def turnkey(data: StandardInput):
    result = run_ai_and_store("Turnkey Panel", data.client_name, data.raw_requirements)
    return {"status": "success", "panel_blueprint": result}
