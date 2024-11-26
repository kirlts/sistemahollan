import requests
import json
import streamlit as st
from firebase_admin import auth
from dotenv import load_dotenv
import os

load_dotenv()

def sign_in_with_email_and_password(email, password):
    request_ref = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPassword?key={os.environ.get('FIREBASE_WEB_API_KEY')}"
    headers = {"content-type": "application/json; charset=UTF-8"}
    data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    request_object = requests.post(request_ref, headers=headers, data=data)
    print(request_object.json())

    print(f"Status Code: {request_object.status_code}")
    print(f"Response Text: {request_object.text}")

    raise_detailed_error(request_object)
    return request_object.json()

def get_account_info(id_token):
    request_ref = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/getAccountInfo?key={os.environ.get('FIREBASE_WEB_API_KEY')}"
    headers = {"content-type": "application/json; charset=UTF-8"}
    data = json.dumps({"idToken": id_token})
    request_object = requests.post(request_ref, headers=headers, data=data)
    raise_detailed_error(request_object)

    return request_object.json()

def raise_detailed_error(request_object):
    try:
        request_object.raise_for_status()
    except requests.exceptions.HTTPError as error:
        raise requests.exceptions.HTTPError(error, request_object.text)

def sign_in(email:str, password:str) -> None:
    try:
        # Attempt to sign in with email and password
        id_token = sign_in_with_email_and_password(email,password)['idToken']
        print("id token: ",id_token)

        # Get account information
        user_info = get_account_info(id_token)["users"][0]

        # --- Obtener el usuario autenticado ---
        user = auth.get_user_by_email(email)

        # --- Obtener el rol del claim personalizado, 'usuario' por defecto ---
        rol = user.custom_claims.get('rol', 'usuario') 

        # --- Guardar la información del usuario, incluyendo el rol ---
        st.session_state.user_info = {
            'email': email,
            'rol': rol 
        }

        st.rerun()

    except requests.exceptions.HTTPError as error:
        error_message = json.loads(error.args[1])['error']['message']
        if error_message in {"INVALID_EMAIL","EMAIL_NOT_FOUND","INVALID_PASSWORD","MISSING_PASSWORD"}:
            st.session_state.auth_warning = 'Error: Use a valid email and password'
        else:
            st.session_state.auth_warning = 'Error: Please try again later'

    except Exception as error:
        print(error)
        st.session_state.auth_warning = 'Error: Please try again later'

def sign_out() -> None:
    st.session_state.clear()
    st.session_state.auth_success = 'Has cerrado sesión'