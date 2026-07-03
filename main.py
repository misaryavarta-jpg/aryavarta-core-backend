import os
import traceback
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Aryavarta Production System", redirect_slashes=False)

# Inject high-security browser headers to pass firewalls cleanly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = str(os.environ.get("GROQ_API_KEY", "")).strip()
groq_client = Groq(api_key=GROQ_API_KEY)

# Fully URL-Encoded Connection String using port 6543
RAW_URI = "postgresql://postgres.spmdcwhwqzaibhgdrzdx:u%2BTr6L_3%2Cxp%2ApmT@://supabase.com"
DB_CONNECTION_URI = str(RAW_URI).strip()

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
    return {"status": "online", "mode": "raw_db_writing_active"}

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
        # PERMANENT SYNTAX FIX: Explicitly extraction out of index [0] to protect against list errors
        ai_tip = completion.choices[0].message.content

        # Native psycopg2 connection using strict string URI parameters
        conn = psycopg2.connect(dsn=DB_CONNECTION_URI)
        cursor = conn.cursor()
        insert_query = "INSERT INTO public.site_tickets (client_name, fault_description, ai_diagnostic_tip) VALUES (%s, %s, %s);"
        cursor.execute(insert_query, (str(data.client_name), str(data.fault_description), str(ai_tip)))
        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "success", "ai_diagnostic": ai_tip}
    except Exception as e:
        error_details = f"Storage Engine Crash: {str(e)} | Trace: {traceback.format_exc()}"
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
        # PERMANENT SYNTAX FIX: Explicitly extraction out of index [0] to protect against list errors
        ai_structured_bom = completion.choices[0].message.content

        conn = psycopg2.connect(dsn=DB_CONNECTION_URI)
        cursor = conn.cursor()
        insert_query = "INSERT INTO public.sundry_orders (client_name, raw_whatsapp_text, structured_bom) VALUES (%s, %s, %s);"
        cursor.execute(insert_query, (str(data.client_name), str(data.raw_whatsapp_text), str(ai_structured_bom)))
        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "success", "structured_list": ai_structured_bom}
    except Exception as e:
        error_details = f"Storage Engine Crash: {str(e)} | Trace: {traceback.format_exc()}"
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
        # PERMANENT SYNTAX FIX: Explicitly extraction out of index [0] to protect against list errors
        panel_specs = completion.choices[0].message.content

        conn = psycopg2.connect(dsn=DB_CONNECTION_URI)
        cursor = conn.cursor()
        insert_query = "INSERT INTO public.panel_designs (client_name, raw_requirements, generated_specifications) VALUES (%s, %s, %s);"
        cursor.execute(insert_query, (str(data.client_name), str(data.raw_requirements), str(panel_specs)))
        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "success", "panel_blueprint": panel_specs}
    except Exception as e:
        error_details = f"Storage Engine Crash: {str(e)} | Trace: {traceback.format_exc()}"
        raise HTTPException(status_code=400, detail=error_details)
