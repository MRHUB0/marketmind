import firebase_admin
from firebase_admin import credentials, firestore, auth
import streamlit as st
import json
import os
import datetime

# Firebase init
firebase_json = json.loads(os.getenv("FIREBASE_ADMIN_JSON"))
firebase_json["private_key"] = firebase_json["private_key"].replace("\\n", "\n")
cred = credentials.Certificate(firebase_json)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

def login_with_firebase():
    st.subheader("Login with Google")
    email = st.text_input("Email")
    uid = st.text_input("User UID (for now, enter manually or simulate)")
    if email and uid:
        return {"email": email, "uid": uid}
    return None

def save_insight(uid, ticker, content):
    doc_ref = db.collection("users").document(uid).collection("insights").document()
    doc_ref.set({
        "ticker": ticker.upper(),
        "content": content,
        "timestamp": datetime.datetime.utcnow()
    })

def check_usage(uid):
    docs = db.collection("users").document(uid).collection("insights").stream()
    return len(list(docs))
