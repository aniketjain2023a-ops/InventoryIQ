


import streamlit as st
from modules.auth import authenticate_user, login_user

st.set_page_config(page_title="InventoryIQ Login", page_icon="🔐", layout="centered")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

st.title("🔐 InventoryIQ")
st.subheader("Login")

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submitted = st.form_submit_button("Login")

    if submitted:
        user = authenticate_user(username, password)

        if user:
            login_user(user["username"], user["role"])
            st.success(f"Login successful - {user['role']}")
            st.switch_page("app.py")
        else:
            st.error("Invalid username or password")

st.caption("Phase 2A - Temporary authentication. Database-backed users will be added next.")