import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from supabase import create_client, Client

app = FastAPI(title="Aryavarta Core Stabilization Backend")

# Inject high-security browser headers to pass firewalls cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

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
def home():
    return {"status": "active"}

@app.post("/api/site-engineer")
def handle_site_engineer_service(data: TicketInput):
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Provide 3 concise engineering safety checks for a panel technician based on this issue."},
                {"role": "user", "content": data.fault_description}
            ],
            model="llama3-8b-8192",
            temperature=0.1
        )
        ai_tip = completion.choices.message.content

        # Direct dictionary insertion for maximum compatibility across Python versions
        supabase.table("site_tickets").insert({
            "client_name": str(data.client_name),
            "fault_description": str(data.fault_description),
            "ai_diagnostic_tip": str(ai_tip)
        }).execute()
        
        return {"status": "success", "ai_diagnostic": ai_tip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sundry-procurement")
def handle_sundry_service(data: SundryInput):
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Convert raw text components into a JSON array string block like: Item, Spec, Qty."},
                {"role": "user", "content": data.raw_whatsapp_text}
            ],
            model="llama3-8b-8192",
            temperature=0.0
        )
        ai_structured_bom = completion.choices.message.content

        supabase.table("sundry_orders").insert({
            "client_name": str(data.client_name),
            "raw_whatsapp_text": str(data.raw_whatsapp_text),
            "structured_bom": str(ai_structured_bom)
        }).execute()
        
        return {"status": "success", "structured_list": ai_structured_bom}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/turnkey-panel")
def handle_turnkey_panel_service(data: PanelInput):
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Provide a brief bulleted panel design blueprint containing enclosure IP tiers and breaker choices."},
                {"role": "user", "content": data.raw_requirements}
            ],
            model="llama3-8b-8192",
            temperature=0.2
        )
        panel_specs = completion.choices.message.content

        supabase.table("panel_designs").insert({
            "client_name": str(data.client_name),
            "raw_requirements": str(data.raw_requirements),
            "generated_specifications": str(panel_specs)
        }).execute()
        
        return {"status": "success", "panel_blueprint": panel_specs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
