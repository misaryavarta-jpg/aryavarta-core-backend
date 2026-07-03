import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from supabase import create_client, Client

app = FastAPI(title="Aryavarta Deep Diagnostics Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Extract and aggressively sanitize keys
GROQ_API_KEY = str(os.environ.get("GROQ_API_KEY", "")).strip()
SUPABASE_URL = str(os.environ.get("SUPABASE_URL", "")).strip()
SUPABASE_KEY = str(os.environ.get("SUPABASE_KEY", "")).strip()

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
    return {
        "status": "online",
        "has_groq": bool(GROQ_API_KEY and not GROQ_API_KEY.startswith("None")),
        "has_sub_url": bool(SUPABASE_URL and not SUPABASE_URL.startswith("None")),
        "has_sub_key": bool(SUPABASE_KEY and not SUPABASE_KEY.startswith("None"))
    }

@app.post("/api/site-engineer")
def handle_site_engineer_service(data: TicketInput):
    try:
        # Pre-execution key checks
        if not GROQ_API_KEY or len(GROQ_API_KEY) < 10:
            raise ValueError("GROQ_API_KEY is missing, empty, or unreadable inside Render environment settings.")
        if not SUPABASE_URL or "supabase.co" not in SUPABASE_URL:
            raise ValueError("SUPABASE_URL environment variable is missing or formatted incorrectly.")
        if not SUPABASE_KEY or len(SUPABASE_KEY) < 20:
            raise ValueError("SUPABASE_KEY environment variable is empty or completely unreadable.")

        # Initialize clients on-demand inside the endpoint to capture initialization crashes
        g_client = Groq(api_key=GROQ_API_KEY)
        s_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        completion = g_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Provide 3 concise panel troubleshooting tips based on the issue."},
                {"role": "user", "content": data.fault_description}
            ],
            model="llama3-8b-8192",
            temperature=0.1
        )
        ai_tip = completion.choices.message.content

        # Execute insertion matching both old and new array-standard syntaxes
        s_client.table("site_tickets").insert([
            {
                "client_name": str(data.client_name),
                "fault_description": str(data.fault_description),
                "ai_diagnostic_tip": str(ai_tip)
            }
        ]).execute()
        
        return {"status": "success", "ai_diagnostic": ai_tip}

    except Exception as e:
        # CRITICAL FIX: Intercept the 500 error and output the EXACT systemic error text message back to the frontend console
        error_details = f"System Crash: {str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_details)

@app.post("/api/sundry-procurement")
def handle_sundry_service(data: SundryInput):
    try:
        if not GROQ_API_KEY or not SUPABASE_URL:
            raise ValueError("Missing essential service connection credentials in Render.")
        g_client = Groq(api_key=GROQ_API_KEY)
        s_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        completion = g_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Convert components into a clean formatted string table list."},
                {"role": "user", "content": data.raw_whatsapp_text}
            ],
            model="llama3-8b-8192",
            temperature=0.0
        )
        ai_structured_bom = completion.choices.message.content

        s_client.table("sundry_orders").insert([
            {
                "client_name": str(data.client_name),
                "raw_whatsapp_text": str(data.raw_whatsapp_text),
                "structured_bom": str(ai_structured_bom)
            }
        ]).execute()
        
        return {"status": "success", "structured_list": ai_structured_bom}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/turnkey-panel")
def handle_turnkey_panel_service(data: PanelInput):
    try:
        if not GROQ_API_KEY or not SUPABASE_URL:
            raise ValueError("Missing essential service connection credentials in Render.")
        g_client = Groq(api_key=GROQ_API_KEY)
        s_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        completion = g_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Provide basic panel enclosure specifications and ratings."},
                {"role": "user", "content": data.raw_requirements}
            ],
            model="llama3-8b-8192",
            temperature=0.2
        )
        panel_specs = completion.choices.message.content

        s_client.table("panel_designs").insert([
            {
                "client_name": str(data.client_name),
                "raw_requirements": str(data.raw_requirements),
                "generated_specifications": str(panel_specs)
            }
        ]).execute()
        
        return {"status": "success", "panel_blueprint": panel_specs}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
