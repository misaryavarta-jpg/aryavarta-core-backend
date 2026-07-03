import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from supabase import create_client, Client

app = FastAPI(title="Aryavarta Fixed Responses Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = str(os.environ.get("GROQ_API_KEY", "")).strip()
SUPABASE_URL = str(os.environ.get("SUPABASE_URL", "")).strip()
SUPABASE_KEY = str(os.environ.get("SUPABASE_KEY", "")).strip()

# Initialize connection frameworks securely
groq_client = Groq(api_key=GROQ_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# FIXED: Swapped out deprecated specdec ID for the standard long-term production ID
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
    return {"status": "online"}

@app.post("/api/site-engineer")
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
        ai_tip = completion.choices.message.content

        # Database rows insertion
        supabase.table("site_tickets").insert([
            {
                "client_name": str(data.client_name),
                "fault_description": str(data.fault_description),
                "ai_diagnostic_tip": str(ai_tip)
            }
        ]).execute()
        
        return {"status": "success", "ai_diagnostic": ai_tip}

    except Exception as e:
        error_details = f"System Crash: {str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_details)

@app.post("/api/sundry-procurement")
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
        ai_structured_bom = completion.choices.message.content

        supabase.table("sundry_orders").insert([
            {
                "client_name": str(data.client_name),
                "raw_whatsapp_text": str(data.raw_whatsapp_text),
                "structured_bom": str(ai_structured_bom)
            }
        ]).execute()
        
        return {"status": "success", "structured_list": ai_structured_bom}
    except Exception as e:
        error_details = f"System Crash: {str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_details)

@app.post("/api/turnkey-panel")
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
        panel_specs = completion.choices.message.content

        supabase.table("panel_designs").insert([
            {
                "client_name": str(data.client_name),
                "raw_requirements": str(data.raw_requirements),
                "generated_specifications": str(panel_specs)
            }
        ]).execute()
        
        return {"status": "success", "panel_blueprint": panel_specs}
    except Exception as e:
        error_details = f"System Crash: {str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_details)
