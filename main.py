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
        # FIX: Wrapped data inside brackets [] for new Supabase library standard syntax
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
        # FIX: Wrapped data inside brackets [] for new Supabase library standard syntax
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
        # FIX: Wrapped data inside brackets [] for new Supabase library standard syntax
        supabase.table("panel_designs").insert([db_record]).execute()
        return {"status": "success", "panel_blueprint": panel_specs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
