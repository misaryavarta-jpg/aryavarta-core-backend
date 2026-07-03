import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from supabase import create_client, Client

# Initialize the central app framework
app = FastAPI(title="Aryavarta Automation Core Engine")

# Permit web dashboard connections across standard ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Extract environment keys with safety checks
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# CRITICAL ERROR PREVENTION: Fallback values if Render settings are blank
if not GROQ_API_KEY:
    GROQ_API_KEY = "gsk_DUMMY_KEY_REPLACE_THIS_IF_EMPTY"
if not SUPABASE_URL:
    SUPABASE_URL = "https://supabase.co"
if not SUPABASE_KEY:
    SUPABASE_KEY = "sb_publishable_DUMMY_KEY_REPLACE_THIS_IF_EMPTY"

# Initialize external connections cleanly
groq_client = Groq(api_key=GROQ_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
def health_check():
    return {
        "status": "online", 
        "groq_loaded": bool(os.environ.get("GROQ_API_KEY")),
        "supabase_url_loaded": bool(os.environ.get("SUPABASE_URL")),
        "supabase_key_loaded": bool(os.environ.get("SUPABASE_KEY"))
    }

@app.post("/api/site-engineer")
def handle_site_engineer_service(data: TicketInput):
    try:
        if "DUMMY" in GROQ_API_KEY or "DUMMY" in SUPABASE_KEY:
            raise ValueError("Your Render configuration variables are missing or empty! Please re-add them in your Environment tab.")

        system_prompt = (
            "You are an industrial panel diagnostic expert. Provide 3 quick checks for a site engineer based on the issue. "
            "Focus on wiring safety, terminal conditions, and voltage checks."
        )
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.fault_description}
            ],
            model="llama3-8b-8192",
            temperature=0.1
        )
        ai_tip = completion.choices.message.content

        db_record = {
            "client_name": data.client_name,
            "fault_description": data.fault_description,
            "ai_diagnostic_tip": ai_tip
        }
        supabase.table("site_tickets").insert([db_record]).execute()
        return {"status": "success", "ai_diagnostic": ai_tip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sundry-procurement")
def handle_sundry_service(data: SundryInput):
    try:
        system_prompt = (
            "You are a parser. Convert unstructured panel component messages into a strictly formatted JSON array. "
            "Example format: " '[{"item": "MCB", "spec": "16A", "qty": "5"}]. Do not add conversational text.'
        )
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.raw_whatsapp_text}
            ],
            model="llama3-8b-8192",
            temperature=0.0
        )
        ai_structured_bom = completion.choices.message.content

        db_record = {
            "client_name": data.client_name,
            "raw_whatsapp_text": data.raw_whatsapp_text,
            "structured_bom": ai_structured_bom
        }
        supabase.table("sundry_orders").insert([db_record]).execute()
        return {"status": "success", "structured_list": ai_structured_bom}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/turnkey-panel")
def handle_turnkey_panel_service(data: PanelInput):
    try:
        system_prompt = (
            "You are a master engineering agent for control panels. Output a bulleted technical design overview "
            "detailing panel type, recommended enclosure protection tier (IP55/IP65), and switchgear items required."
        )
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.raw_requirements}
            ],
            model="llama3-8b-8192",
            temperature=0.2
        )
        panel_specs = completion.choices.message.content

        db_record = {
            "client_name": data.client_name,
            "raw_requirements": data.raw_requirements,
            "generated_specifications": panel_specs
        }
        supabase.table("panel_designs").insert([db_record]).execute()
        return {"status": "success", "panel_blueprint": panel_specs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
