import os
import traceback
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Aryavarta Stable Engine", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = str(os.environ.get("GROQ_API_KEY", "")).strip()
groq_client = Groq(api_key=GROQ_API_KEY)

# PASTE YOUR GOOGLE SCRIPT URL HERE
GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbxZcBzUwmU42j7IxbdJKnjTBggMHpEfBiUeZRnRwnOM9LFYGveytTEwem2zD2NsgPHD/exec"

# UPDATED STABLE MODELS (No "Preview" versions)
# Llama 3.1 70B is the current long-term stable text model
PRODUCTION_TEXT_MODEL = "llama-3.1-70b-versatile"
# Llama 3.2 11B Vision Instruct is the official stable vision model
PRODUCTION_VISION_MODEL = "llama-3.2-11b-vision-instruct"

class TicketInput(BaseModel):
    client_name: str
    fault_description: str
    image_base64: str = ""

class SundryInput(BaseModel):
    client_name: str
    raw_whatsapp_text: str

class PanelInput(BaseModel):
    client_name: str
    raw_requirements: str

@app.get("/")
def home():
    return {"status": "online", "system": "active"}

@app.post("/api/site-engineer")
@app.post("/api/site-engineer/")
def handle_site_engineer_service(data: TicketInput):
    try:
        system_instruction = (
            "You are an industrial panel diagnostic expert. "
            "Analyze the issue description and any attached image. "
            "Provide 3 concise, pinpoint maintenance checks for the engineer."
        )

        if data.image_base64:
            # Vision Flow
            completion = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"Instruction: {system_instruction}\n\nIssue: {data.fault_description}"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data.image_base64}"}}
                        ]
                    }
                ],
                model=PRODUCTION_VISION_MODEL,
                temperature=0.1
            )
        else:
            # Text Flow
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": data.fault_description}
                ],
                model=PRODUCTION_TEXT_MODEL,
                temperature=0.1
            )
            
        ai_tip = completion.choices[0].message.content

        # Google Sheets Handoff
        try:
            requests.post(GOOGLE_SHEET_WEBHOOK, json={
                "service_type": "Site Engineer",
                "client_name": str(data.client_name),
                "input_text": str(data.fault_description) + (" [Image Uploaded]" if data.image_base64 else ""),
                "ai_output": str(ai_tip)
            }, timeout=5)
        except:
            pass # Don't crash if Google Sheets is slow
        
        return {"status": "success", "ai_diagnostic": ai_tip}

    except Exception as e:
        # Return error as text so frontend doesn't show "Connection Failed"
        return {"status": "error", "ai_diagnostic": f"System Error: {str(e)}"}

@app.post("/api/sundry-procurement")
@app.post("/api/sundry-procurement/")
def handle_sundry_service(data: SundryInput):
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Convert this request into a clean table list of items, specs, and quantities."},
                {"role": "user", "content": data.raw_whatsapp_text}
            ],
            model=PRODUCTION_TEXT_MODEL,
            temperature=0.0
        )
        ai_output = completion.choices[0].message.content

        requests.post(GOOGLE_SHEET_WEBHOOK, json={
            "service_type": "Sundry Procurement",
            "client_name": str(data.client_name),
            "input_text": str(data.raw_whatsapp_text),
            "ai_output": str(ai_output)
        })
        
        return {"status": "success", "structured_list": ai_output}
    except Exception as e:
        return {"status": "error", "structured_list": f"Error: {str(e)}"}

@app.post("/api/turnkey-panel")
@app.post("/api/turnkey-panel/")
def handle_turnkey_panel_service(data: PanelInput):
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Provide panel enclosure IP ratings and component specs for this requirement."},
                {"role": "user", "content": data.raw_requirements}
            ],
            model=PRODUCTION_TEXT_MODEL,
            temperature=0.2
        )
        ai_output = completion.choices[0].message.content

        requests.post(GOOGLE_SHEET_WEBHOOK, json={
            "service_type": "Turnkey Panel",
            "client_name": str(data.client_name),
            "input_text": str(data.raw_requirements),
            "ai_output": str(ai_output)
        })
        
        return {"status": "success", "panel_blueprint": ai_output}
    except Exception as e:
        return {"status": "error", "panel_blueprint": f"Error: {str(e)}"}
