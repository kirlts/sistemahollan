import firebase_admin
from firebase_admin import credentials, db
from utils import credenciales  # Asegúrate de que utils.py tenga las credenciales

# Inicializa Firebase
cred = credentials.Certificate(credenciales)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://ingsoftware-a561d-default-rtdb.firebaseio.com/'
})

ref = db.reference('/')

# Datos de los salones
datos = {
  "salones": {
    "salon1": {
      "nombre": "Salon A",
      "capacidad": 50,
      "ubicacion": "Planta baja",
      "precio": 100000
    },
    "salon2": {
      "nombre": "Salon B",
      "capacidad": 100,
      "ubicacion": "Primer piso",
      "precio": 200000
    }
  },
  "servicios": {
    "servicio1": {
      "nombre": "Decoración floral",
      "descripcion": "Arreglos florales para las mesas y el salón",
      "precio": 50000
    },
    "servicio2": {
      "nombre": "Música en vivo",
      "descripcion": "Banda de jazz para amenizar el evento",
      "precio": 100000
    },
    "servicio3": {
      "nombre": "Fotografía profesional",
      "descripcion": "Servicio de fotografía para capturar los mejores momentos",
      "precio": 80000
    }
  }
}

# Guarda los datos en la base de datos
ref.set(datos)