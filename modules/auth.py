

import hashlib
import streamlit as st


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# Temporary Phase 2A users
USERS = {
    "admin": {
        "password": hash_password("admin123"),
        "role": "Admin",
    },
    "manager": {
        "password": hash_password("manager123"),
        "role": "Manager",
    },
    "viewer": {
        "password": hash_password("viewer123"),
        "role": "Viewer",
    },
}


def authenticate_user(username: str, password: str):
    user = USERS.get(username)

    if not user:
        return None

    if user["password"] == hash_password(password):
        return {
            "username": username,
            "role": user["role"],
        }

    return None



def login_user(username: str, role: str):
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.role = role



def logout_user():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""



def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)



def get_current_role() -> str:
    return st.session_state.get("role", "Viewer")



def require_role(*allowed_roles):
    role = get_current_role()
    return role in allowed_roles