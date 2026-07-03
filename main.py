import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
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

# Initialize via the native OpenAI compatibility client required for GPT-OSS models
groq_client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)
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
    return {"status": "online"}

@app.post("/api/site-engineer")
def handle_site_engineer_service(data: TicketInput):
    try:
        # Fixed: Using responses.create with correct .output_text attribute extraction
        response = groq_client.responses.create(
            model="openai/gpt-oss-20b",
            input=f"System Instruction: You are an industrial panel diagnostic expert. Provide 3 quick, concise troubleshooting checks for a field technician. User Issue: {data.fault_description}"
        )
        ai_tip = str(response.output_text)

        supabase.table("site_tickets").insert([
            {
                "client_name": str(data.client_name),
                "fault_description": str(data.fault_description),
                "ai_diagnostic_tip": ai_tip
            }
        ]).execute()
        
        return {"status": "success", "ai_diagnostic": ai_tip}

    except Exception as e:
        error_details = f"System Crash: {str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_details)

@app.post("/api/sundry-procurement")
def handle_sundry_service(data: SundryInput):
    try:
        response = groq_client.responses.create(
            model="openai/gpt-oss-20b",
            input=f"System Instruction: Read the unstructured message containing electrical components and convert it into a strictly formatted table list detailing item, spec and quantity. Message: {data.raw_whatsapp_text}"
        )
        ai_structured_bom = str(response.output_text)

        supabase.table("sundry_orders").insert([
            {
                "client_name": str(data.client_name),
                "raw_whatsapp_text": str(data.raw_whatsapp_text),
                "structured_bom": ai_structured_bom
            }
        ]).execute()
        
        return {"status": "success", "structured_list": ai_structured_bom}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/turnkey-panel")
def handle_turnkey_panel_service(data: PanelInput):
    try:
        response = groq_client.responses.create(
            model="openai/gpt-oss-20b",
            input=f"System Instruction: Provide a brief engineering overview detailing the panel enclosure protection tier (IP55/IP65) and suggested component parameters. Criteria: {data.raw_requirements}"
        )
        panel_specs = str(response.output_text)

        supabase.table("panel_designs").insert([
            {
                "client_name": str(data.client_name),
                "raw_requirements": str(data.raw_requirements),
                "generated_specifications": panel_specs
            }
        ]).execute()
        
        return {"status": "success", "panel_blueprint": panel_specs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
