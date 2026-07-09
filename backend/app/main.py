import os
import json
from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. Database Setup (Immutable Audit Trail)
# ==========================================
DATABASE_URL = "sqlite:///./compliance_logs.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class IncidentLog(Base):
    __tablename__ = "incident_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Intake fields
    source_type = Column(String, index=True) # 'user' or 'auto'
    source_name = Column(String) # 'employee', 'firewall', 'antivirus', 'edr', 'soc'
    device_ip = Column(String, index=True)
    description = Column(String)
    base_severity = Column(String) # Low, Medium, High, Critical
    conversation_log = Column(Text, nullable=True) # JSON list of employee chat history
    
    # AI Processing fields
    is_processed = Column(Boolean, default=False)
    ai_summary = Column(Text, nullable=True)
    correlated_with_id = Column(Integer, nullable=True) # Links to another log if match found
    final_severity = Column(String, nullable=True)
    
    # Routing & Final Reporting fields (from Cybersec team)
    action_tasks = Column(Text, nullable=True) # JSON list of tasks
    affected_users = Column(Text, nullable=True) # JSON list of users
    final_admin_report = Column(Text, nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# 2. External Services Setup
# ==========================================

# Twilio Setup (Smart Escalation)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_account_sid")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_auth_token")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "+1234567890")
ADMIN_PHONE_NUMBER = os.getenv("ADMIN_PHONE_NUMBER", "+0987654321")

def send_sms_alert(message: str):
    """Helper function to send Twilio SMS to IT Admin."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=ADMIN_PHONE_NUMBER
        )
        print(f"SMS sent successfully: {msg.sid}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")

# AI Providers Setup
ACTIVE_AI_PROVIDER = os.getenv("ACTIVE_AI_PROVIDER", "google").lower()

# Google GenAI Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
try:
    from google import genai
    from google.genai import types
    gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except ImportError:
    gemini_client = None

# Groq Setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
try:
    from openai import OpenAI
    groq_client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1"
    ) if GROQ_API_KEY else None
except ImportError:
    groq_client = None

def generate_ai_summary(system_prompt: str, user_prompt: str) -> dict:
    """Helper function to switch between AI providers."""
    if ACTIVE_AI_PROVIDER == "groq":
        if not groq_client:
            raise HTTPException(status_code=500, detail="Groq API Key not configured")
        
        # Groq supports JSON mode
        response = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        return json.loads(response.choices[0].message.content)
        
    elif ACTIVE_AI_PROVIDER == "google":
        if not gemini_client:
            raise HTTPException(status_code=500, detail="Gemini API Key not configured")
            
        response = gemini_client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"),
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        return json.loads(response.text)
        
    else:
        raise HTTPException(status_code=500, detail=f"Unsupported AI provider: {ACTIVE_AI_PROVIDER}")

# ==========================================
# 3. FastAPI App & Models
# ==========================================

app = FastAPI(title="ALTREON - Cyber Triage MVP")

class ReportRequest(BaseModel):
    source_type: str # 'user' or 'auto'
    source_name: str # 'employee', 'firewall', 'antivirus', 'soc'
    device_ip: str
    description: str
    base_severity: str = "Pending" # Default to pending for users
    conversation_log: Optional[List[dict]] = None

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = [] # list of {"role": "user"/"assistant", "content": "..."}

class AIProcessRequest(BaseModel):
    incident_id: int

class RouteRequest(BaseModel):
    incident_id: int
    action_tasks: List[str]
    affected_users: List[str]
    final_admin_report: str

# ==========================================
# Endpoints
# ==========================================

@app.post("/report")
def receive_report(request: ReportRequest, db: Session = Depends(get_db)):
    """
    1. Input & Intake: Receives raw reports from users or auto-systems (AV, Firewall, SOC).
    """
    incident = IncidentLog(
        timestamp=datetime.utcnow(),
        source_type=request.source_type.lower(),
        source_name=request.source_name,
        device_ip=request.device_ip,
        description=request.description,
        base_severity=request.base_severity,
        conversation_log=json.dumps(request.conversation_log) if request.conversation_log else None
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    return {
        "status": "success",
        "message": "Report logged successfully",
        "incident_id": incident.id
    }

@app.post("/webhook/auto")
def auto_alert_webhook(request: ReportRequest, db: Session = Depends(get_db)):
    """
    Webhook for auto alerts (SOC/Firewall/Antivirus) to push reports.
    """
    return receive_report(request, db)

@app.post("/employee/chat")
def employee_chat(request: ChatRequest):
    """
    Employee talks to AI to report an incident. 
    AI asks questions, gives 3 choices, loops 3 times to get data.
    """
    system_prompt = """You are a helpful IT security assistant. 
An employee is reporting a problem. Your goal is to gather:
1. What happened?
2. When did it happen?
3. What is their device IP or hostname?
Ask ONE question at a time. Provide exactly 3 multiple-choice options for the user to pick from, or let them type.
If you have gathered enough information (typically after 3 interactions), set "is_complete": true and output the structured data.
Output STRICTLY in JSON format:
{
  "response": "string (your message to the user)",
  "choices": ["choice 1", "choice 2", "choice 3"],
  "is_complete": boolean,
  "extracted_data": {
     "device_ip": "string or unknown",
     "description": "string summary of the issue"
  }
}"""
    conversation_context = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in request.history])
    user_prompt = f"History:\n{conversation_context}\n\nUser: {request.message}"
    
    try:
        ai_response_json = generate_ai_summary(system_prompt, user_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
        
    return ai_response_json

@app.post("/ai/process")
def process_ai(request: AIProcessRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    2. AI Processing & Matching: 
    AI checks logs database to match new logs with old logs, combines them, 
    and generates a Report Summary + Logs.
    """
    incident = db.query(IncidentLog).filter(IncidentLog.id == request.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.is_processed:
        return {"status": "already_processed", "incident_id": incident.id, "summary": incident.ai_summary}

    if ACTIVE_AI_PROVIDER == "groq" and not groq_client:
        raise HTTPException(status_code=500, detail="Groq API Key not configured")
    elif ACTIVE_AI_PROVIDER == "google" and not gemini_client:
        raise HTTPException(status_code=500, detail="Gemini API Key not configured")

    # Look for historical context (same IP within last 24 hours, excluding this one)
    time_window = datetime.utcnow() - timedelta(hours=24)
    historical_logs = db.query(IncidentLog).filter(
        IncidentLog.device_ip == incident.device_ip,
        IncidentLog.id != incident.id,
        IncidentLog.timestamp >= time_window
    ).all()

    historical_context = ""
    correlated_id = None
    if historical_logs:
        correlated_id = historical_logs[-1].id # Link to the most recent previous log
        historical_context = "Historical Logs for this IP:\n" + "\n".join(
            [f"- ID {log.id} [{log.source_type}/{log.source_name}]: {log.description} (Severity: {log.base_severity})" for log in historical_logs]
        )
        final_severity = "CRITICAL" # Correlated alerts automatically bump to critical
    else:
        historical_context = "No recent historical logs for this IP found."
        final_severity = incident.base_severity if incident.base_severity != "Pending" else "Medium"

    # Call AI
    system_prompt = f"""You are a top-tier SOC Analyst AI Engine.
You are reviewing a new incident report and checking it against historical logs.
Your job is to generate a 'Report Summary + Logs' that combines the new report with any matched history.
Output STRICTLY in JSON format matching this exact schema:
{{
  "executive_summary": "string (clear summary of what happened)",
  "technical_details": "string (technical breakdown)",
  "recommended_actions": ["string", "string"]
}}"""

    conversation_text = ""
    if incident.conversation_log:
        conversation_text = f"\n- Employee Chat Log: {incident.conversation_log}"

    user_prompt = f"""
New Incident Report:
- ID: {incident.id}
- Source: {incident.source_type} ({incident.source_name})
- IP: {incident.device_ip}
- Description: {incident.description}
- Base Severity: {incident.base_severity}{conversation_text}

{historical_context}
"""

    try:
        ai_response_json = generate_ai_summary(system_prompt, user_prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    # Update the DB record
    incident.is_processed = True
    incident.ai_summary = json.dumps(ai_response_json)
    incident.correlated_with_id = correlated_id
    incident.final_severity = final_severity
    db.commit()
    db.refresh(incident)

    # 3. Data Distribution (Simulated push to Dashboards/Cybersec via SMS if critical)
    if final_severity == "CRITICAL" or final_severity.lower() == "high":
        sms_message = f"URGENT: ALTREON Report {incident.id} processed for {incident.device_ip}. Severity: {final_severity}."
        background_tasks.add_task(send_sms_alert, sms_message)

    return {
        "status": "success",
        "incident_id": incident.id,
        "correlated": bool(correlated_id),
        "final_severity": final_severity,
        "ai_summary": ai_response_json
    }

@app.post("/route")
def route_incident(request: RouteRequest, db: Session = Depends(get_db)):
    """
    4. Final Actions & Routing:
    Cybersecurity Team assigns tasks to reporter/affected employees, 
    and generates the final report for the Admin.
    """
    incident = db.query(IncidentLog).filter(IncidentLog.id == request.incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    incident.action_tasks = json.dumps(request.action_tasks)
    incident.affected_users = json.dumps(request.affected_users)
    incident.final_admin_report = request.final_admin_report
    
    db.commit()
    db.refresh(incident)
    
    return {
        "status": "success",
        "message": "Incident routing and final reporting completed.",
        "incident_id": incident.id
    }

@app.get("/incident/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the full result of an incident, including AI processing and final routing.
    """
    incident = db.query(IncidentLog).filter(IncidentLog.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    return {
        "id": incident.id,
        "timestamp": incident.timestamp,
        "source": f"{incident.source_type} ({incident.source_name})",
        "device_ip": incident.device_ip,
        "description": incident.description,
        "initial_severity": incident.base_severity,
        "final_severity": incident.final_severity,
        "is_processed": incident.is_processed,
        "correlated_with_id": incident.correlated_with_id,
        "ai_summary": json.loads(incident.ai_summary) if incident.ai_summary else None,
        "routing_info": {
            "action_tasks": json.loads(incident.action_tasks) if incident.action_tasks else None,
            "affected_users": json.loads(incident.affected_users) if incident.affected_users else None,
            "final_admin_report": incident.final_admin_report
        }
    }

@app.get("/reports/employee/{source_name}")
def get_employee_reports(source_name: str, db: Session = Depends(get_db)):
    """Get all reports submitted by a specific employee/source."""
    incidents = db.query(IncidentLog).filter(IncidentLog.source_name == source_name).all()
    return incidents

@app.get("/reports/cybersec/pending")
def get_pending_reports(db: Session = Depends(get_db)):
    """Get all incidents that need Cybersec attention (processed by AI but not routed)."""
    incidents = db.query(IncidentLog).filter(IncidentLog.is_processed == True, IncidentLog.final_admin_report == None).all()
    return incidents

@app.get("/reports/admin/all")
def get_admin_reports(db: Session = Depends(get_db)):
    """Get all incidents for the admin dashboard."""
    incidents = db.query(IncidentLog).all()
    return incidents
