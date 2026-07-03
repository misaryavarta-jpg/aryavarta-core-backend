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

# Initialize free third-party API configurations safely from environments
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Define incoming structural data definitions
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
    """ Keeps the free-tier server active and responsive """
    return {"status": "online", "message": "Aryavarta systems running smoothly."}

# =====================================================================
# SERVICE 1: SITE ENGINEER ROUTE WITH INTELLIGENT FIELD CO-PILOT
# =====================================================================
@app.post("/api/site-engineer")
def handle_site_engineer_service(data: TicketInput):
    try:
        system_prompt = (
            "You are an industrial panel diagnostic expert. Based on the fault description, "
            "provide 3 high-priority, concise checks for a site engineer to run immediately. "
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
        # Fixed list formatting for modern library stability
        supabase.table("site_tickets").insert([db_record]).execute()
        return {"status": "success", "ai_diagnostic": ai_tip}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# SERVICE 2: SUNDRY CONVERSION VIA FAST DATA READER AGENT
# =====================================================================
@app.post("/api/sundry-procurement")
def handle_sundry_service(data: SundryInput):
    try:
        system_prompt = (
            "You are a parser. Read the unstructured message containing panel components "
            "and convert it into a strictly formatted JSON array block. Example format: "
            '[{"item": "MCB", "spec": "16A Single Phase", "qty": "5"}]. Do not add conversational text.'
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
        # Fixed list formatting for modern library stability
        supabase.table("sundry_orders").insert([db_record]).execute()
        return {"status": "success", "structured_list": ai_structured_bom}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================================
# SERVICE 3: TURNKEY PANEL EXPERT ASSISTANT ROUTE
# =====================================================================
@app.post("/api/turnkey-panel")
def handle_turnkey_panel_service(data: PanelInput):
    try:
        system_prompt = (
            "You are a master engineering agent for industrial control panels. Given a client's "
            "raw manufacturing criteria, output a bulleted technical design overview detailing "
            "the suggested panel type, recommended structural enclosure protection tier (IP55/IP65), "
            "and critical safety component breakers required."
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
        # Fixed list formatting for modern library stability
        supabase.table("panel_designs").insert([db_record]).execute()
        return {"status": "success", "panel_blueprint": panel_specs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
