import streamlit as st
import requests
import pandas as pd
import time

# FastAPI Backend URL (use localhost for local dev, Render URL in production)
FASTAPI_URL = "http://localhost:8080"  # Change to "https://your-app.onrender.com" when deployed
st.set_page_config(layout="wide")
if "selected_row" not in st.session_state:
    st.session_state.selected_row = None
if "added_sadhak" not in st.session_state:
    st.session_state.added_sadhak = None

# 🔥 Auto-refresh every 30 seconds using Streamlit's rerun trick
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = time.time()

def row_selected():
    selected_indexes = st.session_state.data_editor["edited_rows"]
    if selected_indexes:  # Check if any row was edited
        st.session_state.selected_index = list(selected_indexes.keys())[0]

@st.dialog("Confirm change")
def change(action: str):
    st.write(f"Are you sure you want to {action}?")
    reason = st.text_input("Because...")
    if st.button("Submit"):
        # Make that change
        st.session_state.change = {"action": action}
        st.rerun()

@st.dialog("Confirm add sadhak pg email", width="large")
def confirm_add_email(sadhak_dict):
    st.session_state.added_sadhak = None
    st.write(f"Send new sadhak email for {sadhak_dict['first_name']} {sadhak_dict['last_name']}?")
    st.write("Confirm this email:")
    email_recipients = st.text_input("Recipients")
    email_subject = st.text_input("Subject")
    email_body = st.text_area("Body", height=300)
    if st.button("Send email"):
        st.write("Email sent")

def add_sadhak(sadhak_dict):
    st.write(f"Adding {sadhak_dict['first_name']} {sadhak_dict['last_name']}...")
    # Call backend to save sadhak
    st.write(f"Done.")

@st.dialog("Add Sadhak")
def enter_new_sadhak():
    sadhak_dict = {}
    st.session_state.added_sadhak = None
    st.write(f"Add new sadhak to the retreat")
    sadhak_dict["first_name"] = st.text_input("First name")
    sadhak_dict["last_name"] = st.text_input("Last name")
    sadhak_dict["email"] = st.text_input("Email")
    sadhak_dict["phone"] = st.text_input("Phone")
    sadhak_dict["city_country"] = st.text_input("Location")
    sadhak_dict["referrer"] = st.text_input("Invited by")
    sadhak_dict["age"] = st.selectbox(
        "Age",
        ["17-34", "35-55", "Over 56"],
        index=1,
    )
    sadhak_dict["gender"] = st.selectbox("Gender", ["Female", "Male", "Non-binary", "Prefer not to say"], index=0)
    pgs = st.session_state.pgs
    sadhak_dict["pg"] = st.selectbox(
        "Prana group",
        tuple(pgs["PG"] + " - " + pgs["time"] + " - " + pgs['pp1'] + " & " + pgs['pp2']),
        index=0,
    )
    if st.button("Add sadhak"):
        add_sadhak(sadhak_dict)
        st.session_state.added_sadhak = sadhak_dict
        st.rerun()

def load_data():
    # Get pgs
    response = requests.get(f"{FASTAPI_URL}/get-pgs/")
    if response.status_code != 200:
        st.error(f"Failed to load data: {response.status_code}")
    json_data = response.json()["data"]
    if not json_data:
        st.warning("The Google Sheet is empty.")

    pgs = pd.DataFrame(json_data)
    st.session_state.pgs = pgs

    # Get sadhaks
    response = requests.get(f"{FASTAPI_URL}/get-sadhaks/")
    if response.status_code != 200:
        st.error(f"Failed to load data: {response.status_code}")
    json_data = response.json()["data"]
    if not json_data:
        st.warning("The Google Sheet is empty.")

    # Create a two-column layout
    col1, spacer, col2 = st.columns([2, 0.25, 2])  # Adjust widths as needed

    # Left Column: Display Table
    with col1:
        with st.container():
            df = pd.DataFrame(json_data)
            df["Name"] = df["First name"] + " " + df["Last name"]
            sorted_df = pd.DataFrame()
            sorted_df["Name"] = df['First name'] + " " + df["Last name"]
            sorted_df[["PG", "pg time"]] = df[["PG", "pg time"]]
            # Merge `data` with `pgs` on the `PG` column
            sorted_df = sorted_df.merge(pgs, on="PG", how="left")
            sorted_df = sorted_df.sort_values(by="PG", ascending=True).reset_index(drop=True)
            sorted_df.insert(0, "Select", False)  # Add checkbox column at the start

            # Use st.data_editor to allow row selection
            edited_data = st.data_editor(
                sorted_df,
                column_config={"Select": st.column_config.CheckboxColumn("Select")},
                disabled=["Name", "PG", "pg time"],  # Make other columns read-only
                hide_index=True,
                key="data_table",
                height=850,
            )

            # Find the selected row index
            selected_rows = edited_data[edited_data["Select"]].index.tolist()
            print(f"selected_row={selected_rows}")
            # Ensure session state stores an integer
            if selected_rows:
                st.session_state.selected_row = int(selected_rows[0])  # 🔥 Convert to integer

    with col2:
        # Display details if a row is selected
        if isinstance(st.session_state.selected_row, int) and 0 <= st.session_state.selected_row < len(sorted_df):
            selected_data = sorted_df.iloc[st.session_state.selected_row]

            # Lookup user details from details_data DataFrame
            user_details = df[df["Name"] == selected_data["Name"]]

            st.header(f"{selected_data['Name']}")
            st.subheader(f"{selected_data['PG']} - {selected_data['pg time']}")

            if not user_details.empty:
                user_info = user_details.iloc[0]  # Get first matching row
                st.write(f"**Email:** {user_info['Email']}")
                st.write(f"**Phone:** {user_info['Phone number']}")
                st.write(f"**Location:** {user_info['City/Country']}")

            # Action buttons
            if st.button("Drop out"):
                change(f"Drop {selected_data['Name']}")

            col1, col2 = st.columns([1, 2])  # Adjust widths as needed
            with col1:
                new_pg = st.selectbox(
                    "Move to: ",
                    tuple(pgs["PG"]),
                    index=None,
                    placeholder="Select new prana group...",
                )
                if new_pg:
                    change(f"Move {selected_data['Name']} to {new_pg}")

        else:
            st.write("No row selected. Click a checkbox in the table above.")

if time.time() - st.session_state.last_refresh_time > 30:  # Auto-refresh every 30s
    st.session_state.last_refresh_time = time.time()
    print("Autorefreshing data")
    st.rerun()

st.title("Genesis")
st.write("A system for managing SMY retreat prana groups")

button1, button2, button3, button4 = st.columns([1, 1, 1, 5])  # Adjust widths as needed
with button1:
    if st.button("Refresh"):
        st.rerun()
with button2:
    if st.button("Add Sadhak"):
        enter_new_sadhak()
if st.session_state.added_sadhak:
    confirm_add_email(st.session_state.added_sadhak)
with button3:
    if st.button("Email all prana groups"):
        change("Email all prana groups")

load_data()
