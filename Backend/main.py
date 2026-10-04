from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from jose import jwt
import sqlite3
from dotenv import load_dotenv 
import os

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Database connection
connection = sqlite3.connect("healthcare.db", check_same_thread=False)
cursor = connection.cursor()

# Create patient table
cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    phone TEXT NOT NULL,
    department TEXT NOT NULL
)
""")

connection.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    details TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

connection.commit()


# Patient data structure

class Patient(BaseModel):
    name: str = Field(..., min_length=2)
    age: int = Field(..., ge=1, le=120)
    phone: str = Field(..., min_length=10)
    department: str = Field(..., min_length=2)
class LoginRequest(BaseModel):
    username: str
    password: str


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def verify_token(token: str):

    try:
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
        
        def require_admin(token: str):

         payload = verify_token(token)

    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return payload
def require_admin(token: str):

         payload = verify_token(token)

         if payload.get("role") != "admin":
          raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
         return payload


@app.post("/login")
def login(data: LoginRequest):

    if data.username == "admin" and data.password == "admin123":

        token = jwt.encode(
            {
                "sub": data.username,
                "role": "admin"
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        return {
            "message": "Login successful",
            "access_token": token,
            "role": "admin"
        }

    elif data.username == "staff" and data.password == "staff123":

        token = jwt.encode(
            {
                "sub": data.username,
                "role": "staff"
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        return {
            "message": "Login successful",
            "access_token": token,
            "role": "staff"
        }

    return {
        "message": "Invalid username or password"
    }
# Temporary patient storage
patients = []


# Home
@app.get("/")
def home():
    return {"message": "Smart Healthcare Queue Orchestrator is running"}


@app.post("/patients", dependencies=[Depends(require_admin)])
def register_patient(patient: Patient):
    cursor.execute(
        "INSERT INTO patients (name, age, phone, department) VALUES (?, ?, ?, ?)",
        (patient.name, patient.age, patient.phone, patient.department)
    )
    connection.commit()

    cursor.execute(
        "INSERT INTO audit_logs (action, details) VALUES (?, ?)",
        (
            "Patient Registered",
            f"Patient: {patient.name}, Department: {patient.department}"
        )
    )
    connection.commit()

    return {
        "message": "Patient saved successfully in database"
    }


# View registered patients
@app.get("/patients")
def get_patients():

    cursor.execute("SELECT * FROM patients")
    patient_records = cursor.fetchall()

    return patient_records

# Appointment data structure
class Appointment(BaseModel):
    patient_name: str = Field(..., min_length=2)
    department: str = Field(..., min_length=2)
    appointment_date: str = Field(..., min_length=1)
    appointment_time: str = Field(..., min_length=1)


# Temporary appointment storage
appointments = []

# Create appointment table
cursor.execute("""
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT NOT NULL,
    department TEXT NOT NULL,
    appointment_date TEXT NOT NULL,
    appointment_time TEXT NOT NULL
)
""")

connection.commit()


# Book an appointment
@app.post("/appointments")
def book_appointment(appointment: Appointment):

    cursor.execute("""
    INSERT INTO appointments
    (patient_name, department, appointment_date, appointment_time)
    VALUES (?, ?, ?, ?)
    """, (
        appointment.patient_name,
        appointment.department,
        appointment.appointment_date,
        appointment.appointment_time
    ))

    connection.commit()

    cursor.execute(
        "INSERT INTO audit_logs (action, details) VALUES (?, ?)",
        (
            "Appointment Booked",
            f"Patient: {appointment.patient_name}, "
            f"Department: {appointment.department}, "
            f"Date: {appointment.appointment_date}, "
            f"Time: {appointment.appointment_time}"
        )
    )

    connection.commit()

    return {
        "message": "Appointment saved successfully in database",
        "appointment": appointment
    }

# View all appointments
@app.get("/appointments")
def get_appointments():

    cursor.execute("SELECT * FROM appointments")
    appointment_records = cursor.fetchall()

    return appointment_records

# Walk-in token data structure
class WalkIn(BaseModel):
    patient_name: str = Field(..., min_length=2)
    department: str = Field(..., min_length=2)

# Temporary walk-in storage
walk_ins = []

# Create walk-in table
cursor.execute("""
CREATE TABLE IF NOT EXISTS walk_ins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token_number INTEGER NOT NULL,
    patient_name TEXT NOT NULL,
    department TEXT NOT NULL,
    status TEXT NOT NULL
)
""")

connection.commit()

# Generate a walk-in token
@app.post("/walkins")
def create_walkin(walkin: WalkIn):

    cursor.execute("SELECT COUNT(*) FROM walk_ins")
    count = cursor.fetchone()[0]

    token_number = count + 1

    cursor.execute("""
    INSERT INTO walk_ins
    (token_number, patient_name, department, status)
    VALUES (?, ?, ?, ?)
    """, (
        token_number,
        walkin.patient_name,
        walkin.department,
        "Waiting"
    ))

    connection.commit()

    cursor.execute(
        "INSERT INTO audit_logs (action, details) VALUES (?, ?)",
        (
            "Walk-in Added",
            f"Token: {token_number}, "
            f"Patient: {walkin.patient_name}, "
            f"Department: {walkin.department}"
        )
    )

    connection.commit()

    return {
        "message": "Walk-in token saved successfully in database",
        "walk_in": {
            "token_number": token_number,
            "patient_name": walkin.patient_name,
            "department": walkin.department,
            "status": "Waiting"
        }
    }


# View walk-in queue
@app.get("/walkins")
def get_walkins():

    cursor.execute("SELECT * FROM walk_ins")
    walkin_records = cursor.fetchall()

    return walkin_records

# Live queue
@app.get("/queue")
def get_queue():

    cursor.execute("""
    SELECT * FROM walk_ins
    WHERE status = 'Waiting'
    """)

    waiting_patients = cursor.fetchall()

    return {
        "queue": waiting_patients,
        "total_waiting": len(waiting_patients)
    }
    
    # Referral data structure
class Referral(BaseModel):
    patient_name: str = Field(..., min_length=2)
    from_department: str = Field(..., min_length=2)
    to_department: str = Field(..., min_length=2)
    reason: str = Field(..., min_length=3)


# Temporary referral storage
referrals = []

# Create a referral
@app.post("/referrals")
def create_referral(referral: Referral):
    referrals.append(referral)

    cursor.execute(
        "INSERT INTO audit_logs (action, details) VALUES (?, ?)",
        (
            "Referral Created",
            f"Patient: {referral.patient_name}, "
            f"From: {referral.from_department}, "
            f"To: {referral.to_department}, "
            f"Reason: {referral.reason}"
        )
    )

    connection.commit()

    return {
        "message": "Referral created successfully",
        "referral": referral
    }


# View all referrals
@app.get("/referrals")
def get_referrals():
    return referrals

# Referral priority data
class ReferralPriority(BaseModel):
    patient_name: str
    reason: str
    
    # Calculate referral priority
@app.post("/referral-priority")
def calculate_priority(referral: ReferralPriority):

    reason = referral.reason.lower()

    if "urgent" in reason or "emergency" in reason:
        priority = "Urgent"
    elif "serious" in reason or "immediate" in reason:
        priority = "High"
    else:
        priority = "Normal"

    return {
        "patient_name": referral.patient_name,
        "reason": referral.reason,
        "priority": priority
    }
    
    # Notification data structure
class Notification(BaseModel):
    patient_name: str
    message: str
    notification_type: str


# Temporary notification storage
notifications = []

# Create a notification
@app.post("/notifications")
def create_notification(notification: Notification):
    notifications.append(notification)

    return {
        "message": "Notification created successfully",
        "notification": notification
    }


# View all notifications
@app.get("/notifications")
def get_notifications():
    return notifications

import subprocess
import sys

@app.get("/forecast")
def get_forecast():

    result = subprocess.run(
        [
            sys.executable,
            r"E:\CAPSTRONE PROJECT\Ml__Service\capacity_forecasting.py"
        ],
        capture_output=True,
        text=True
    )

    return {
        "message": "Forecast generated successfully",
        "forecast_output": result.stdout,
        "error": result.stderr
    }