import os
import traceback
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Aryavarta Google Sheets Engine", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = str(os.environ.get("GROQ_API_KEY", "")).strip()
groq_client = Groq(api_key=GROQ_API_KEY)

# PASTE YOUR GOOGLE APPS SCRIPT WEB APP URL LINK BETWEEN THE QUOTES
GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbxZcBzUwmU42j7IxbdJKnjTBggMHpEfBiUeZRnRwnOM9LFYGveytTEwem2zD2NsgPHD/exec"

PRODUCTION_MODEL = "llama-3.3-70b-versatile"

class TicketInput(BaseModel):
    client_name: str
    fault_description: str

class SundryInput(BaseModel):
    client_name: str
    raw_whatsapp_text: str

class PanelInput(BaseModel):
    client_name: str
    raw_requirements: str

@app.get("/")
def home():
    return {"status": "online", "mode": "google_sheets_active"}

@app.post("/api/site-engineer")
@app.post("/api/site-engineer/")
def handle_site_engineer_service(data: TicketInput):
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an industrial panel diagnostic expert. Provide 3 quick, concise troubleshooting checks for a field technician based on the issue description."},
                {"role": "user", "content": data.fault_description}
            ],
            model=PRODUCTION_MODEL,
            temperature=0.1
        )
        ai_tip = completion.choices[0].message.content

        # Direct pipeline connection handoff straight into Google Sheets
        payload = {
            "service_type": "Site Engineer Service",
            "client_name": str(data.client_name),
            "input_text": str(data.fault_description),
            "ai_output": str(ai_tip)
        }
        requests.post(GOOGLE_SHEET_WEBHOOK, json=payload)
        
        return {"status": "success", "ai_diagnostic": ai_tip}
    except Exception as e:
        error_details = f"Google Handoff Error: {str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_details)

@app.post("/api/sundry-procurement")
@app.post("/api/sundry-procurement/")
def handle_sundry_service(data: SundryInput):
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Read the unstructured message containing electrical components and convert it into a clean formatted string table list detailing item, spec and quantity."},
                {"role": "user", "content": data.raw_whatsapp_text}
            ],
            model=PRODUCTION_MODEL,
            temperature=0.0
        )
        ai_structured_bom = completion.choices[0].message.content

        payload = {
            "service_type": "Sundry Procurement Service",
            "client_name": str(data.client_name),
            "input_text": str(data.raw_whatsapp_text),
            "ai_output": str(ai_structured_bom)
        }
        requests.post(GOOGLE_SHEET_WEBHOOK, json=payload)
        
        return {"status": "success", "structured_list": ai_structured_bom}
    except Exception as e:
        error_details = f"Google Handoff Error: {str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_details)

@app.post("/api/turnkey-panel")
@app.post("/api/turnkey-panel/")
def handle_turnkey_panel_service(data: PanelInput):
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Provide a brief engineering overview detailing the panel enclosure protection tier (IP55/IP65) and suggested component parameters based on requirements."},
                {"role": "user", "content": data.raw_requirements}
            ],
            model=PRODUCTION_MODEL,
            temperature=0.2
        )
        panel_specs = completion.choices[0].message.content

        payload = {
            "service_type": "Turnkey Panel Service",
            "client_name": str(data.client_name),
            "input_text": str(data.raw_requirements),
            "ai_output": str(panel_specs)
        }
        requests.post(GOOGLE_SHEET_WEBHOOK, json=payload)
        
        return {"status": "success", "panel_blueprint": panel_specs}
    except Exception as e:
        error_details = f"Google Handoff Error: {str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_details)
