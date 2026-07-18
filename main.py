import os
import traceback
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Aryavarta Google Sheets Multimodal Engine", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = str(os.environ.get("GROQ_API_KEY", "")).strip()
groq_client = Groq(api_key=GROQ_API_KEY)

# ─── DATABASE LINK HOOK ───
# Ensure your unique Google Web App URL string is pasted accurately here:
GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbxZcBzUwmU42j7IxbdJKnjTBggMHpEfBiUeZRnRwnOM9LFYGveytTEwem2zD2NsgPHD/exec"

PRODUCTION_TEXT_MODEL = "llama-3.3-70b-versatile"
PRODUCTION_VISION_MODEL = "llama-3.2-11b-vision-preview"

class TicketInput(BaseModel):
    client_name: str
    fault_description: str
    image_base64: str = ""  # Captures optional encoded image payload arrays

class SundryInput(BaseModel):
    client_name: str
    raw_whatsapp_text: str

class PanelInput(BaseModel):
    client_name: str
    raw_requirements: str

@app.get("/")
def home():
    return {"status": "online", "mode": "multimodal_sheets_active"}

@app.post("/api/site-engineer")
@app.post("/api/site-engineer/")
def handle_site_engineer_service(data: TicketInput):
    try:
        system_instruction = (
            "You are an expert industrial automation panel troubleshooting assistant. "
            "Analyze the text issue description and any attached image closely. "
            "Identify burnt out breakers, loose wire indicators, or fault lights if present in the photo. "
            "Provide 3 highly concise, pinpoint accurate maintenance checks or terminal fixes for the engineer."
        )

        # Execution Condition A: If the engineer uploaded a machinery photograph
        if data.image_base64:
            messages_payload = [
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Client reported text info: {data.fault_description}"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{data.image_base64}"}
                        }
                    ]
                }
            ]
            completion = groq_client.chat.completions.create(
                messages=messages_payload,
                model=PRODUCTION_VISION_MODEL,
                temperature=0.1
            )
        # Execution Condition B: If the request is pure text
        else:
            completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": data.fault_description}
                ],
                model=PRODUCTION_TEXT_MODEL,
                temperature=0.1
            )
            
        ai_tip = completion.choices[0].message.content

        # Handoff straight to your active Google Sheet data grid row logs
        payload = {
            "service_type": "Site Engineer (Multimodal Analysis)",
            "client_name": str(data.client_name),
            "input_text": str(data.fault_description) + (" [Machinery Photo Attached]" if data.image_base64 else ""),
            "ai_output": str(ai_tip)
        }
        requests.post(GOOGLE_SHEET_WEBHOOK, json=payload)
        
        return {"status": "success", "ai_diagnostic": ai_tip}
    except Exception as e:
        error_details = f"Vision Engine Error: {str(e)} | Trace: {traceback.format_exc()}"
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
            model=PRODUCTION_TEXT_MODEL,
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
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/turnkey-panel")
@app.post("/api/turnkey-panel/")
def handle_turnkey_panel_service(data: PanelInput):
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Provide a brief engineering overview detailing the panel enclosure protection tier (IP55/IP65) and suggested component parameters based on requirements."},
                {"role": "user", "content": data.raw_requirements}
            ],
            model=PRODUCTION_TEXT_MODEL,
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
        raise HTTPException(status_code=400, detail=str(e))
