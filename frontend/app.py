import streamlit as st
import requests
import websocket

st.title("Group Membership Change Emails")

st.write("Click to start sending emails.")

# Internal FastAPI URL
FASTAPI_URL = "http://localhost:8080"

if st.button("Start Email Process"):
    ws = websocket.create_connection(f"{FASTAPI_URL.replace('http', 'ws')}/ws")  # Use internal WebSocket
    while True:
        message = ws.recv()
        if message == "Task completed!":
            st.success(message)
            break
        st.write(message)
    ws.close()
