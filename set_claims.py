import firebase_admin
from utils import credenciales
from firebase_admin import credentials, auth, initialize_app

# Inicializa el Firebase Admin SDK
def inicializar_firebase():
    cred = credentials.Certificate(credenciales) # Obtener la información de la cuenta de servicio desde las variables de entorno
    firebase_app = initialize_app(cred)
    return firebase_app

firebase_app = inicializar_firebase()

# Define el UID del usuario
uid = "al1vVvY0pMXieIeKy2tVakeMNmI3"

# Establece los claims personalizados
auth.set_custom_user_claims(uid, {"rol": "client"})

# Lookup the user associated with the specified uid.
user = auth.get_user(uid)
# The claims can be accessed on the user record.
print(user.custom_claims.get('rol'))