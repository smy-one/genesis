import streamlit as st
import websocket

st.title("Group Membership Change Emails")

st.write("Click to start sending emails.")

if st.button("Start Email Process"):
    ws = websocket.create_connection("wss://your-render-url/ws")  # Replace with actual URL
    while True:
        message = ws.recv()
        if message == "Task completed!":
            st.success(message)
            break
        st.write(message)
    ws.close()
