from fastapi import FastAPI, WebSocket
import asyncio
import gspread
from google.oauth2.service_account import Credentials
import json
import os
from . import init_genesis
from dotenv import load_dotenv
import pandas as pd

app = FastAPI()

print("Routes:")
for route in app.router.routes:
    print(route.path)

#os.environ['GOOGLE_CREDENTIALS'] = ''

load_dotenv()
"""
print(f"Env:")
for key, value in os.environ.items():
    print(f"{key}={value}")
print(f"end")
"""
print("Hello")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SERVICE_ACCOUNT_INFO = json.loads(GOOGLE_CREDENTIALS, strict=False)  # Store JSON in Render env vars
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)
print(f"Client email {SERVICE_ACCOUNT_INFO['client_email']}")
sadhak_sheet = client.open_by_key(init_genesis.SHEET_ID).worksheet(init_genesis.SADHAK_SHEET)
pg_sheet = client.open_by_key(init_genesis.SHEET_ID).worksheet(init_genesis.PG_SHEET)

# API Endpoint to sadhak sheet
@app.get("/get-sadhaks/")
def get_sadhaks():
    data = sadhak_sheet.get_all_records()
    df = pd.DataFrame(data)

    if "First name" in df.columns:  # Ensure column exists
        num_sadhaks = df["First name"].astype(str).str.strip().ne("").cumprod().sum()
        df = df.iloc[:num_sadhaks]  # Keep only non-empty rows

    return {"data": df.to_dict(orient="records")}  # ✅ Fix: Convert to JSON-compatible format

# API Endpoint to pg sheet
@app.get("/get-pgs/")
def get_pgs():
    data = pg_sheet.get_all_records()
    df = pd.DataFrame(data)

    if "PG" in df.columns:  # Ensure column exists
        num_pgs = df["PG"].astype(str).str.strip().ne("").cumprod().sum()
        df = df.iloc[:num_pgs]  # Keep only non-empty rows

    return {"data": df.to_dict(orient="records")}  # ✅ Fix: Convert to JSON-compatible format

@app.put("/add-sadhak/")
def add_sadhak():
    return {}

@app.put("/remove-sadhak/")
def remove_sadhak():
    return {}

@app.put("/move-sadhak/")
def move_sadhak():
    return {}

# WebSocket for Real-Time Updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    for i in range(10):  # Simulating a long-running task
        await websocket.send_text(f"Step {i+1}/10 completed")
        await asyncio.sleep(2)  # Simulated delay
    await websocket.send_text("Task completed!")
    await websocket.close()

# ✅ API Root Route (For Debugging)
@app.get("/")
def root():
    return {"message": "FastAPI backend is running!"}
