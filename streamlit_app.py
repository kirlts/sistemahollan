import streamlit as st
import uuid
from firebase_admin import credentials, initialize_app, db, auth
from auth import sign_in, sign_out
from utils import credenciales
from datetime import datetime

@st.cache_resource
def inicializar_firebase():
    cred = credentials.Certificate(credenciales)
    firebase_app = initialize_app(cred, {
        'databaseURL': 'https://ingsoftware-a561d-default-rtdb.firebaseio.com/' 
    })
    return firebase_app

def mostrar_disponibilidad(fecha, hora_inicio, hora_fin):
    # Convierte las horas a objetos time
    hora_inicio_dt = datetime.strptime(hora_inicio, '%H:%M').time()
    hora_fin_dt = datetime.strptime(hora_fin, '%H:%M').time()

    # Obtén la referencia a la tabla "reservas"
    ref_reservas = db.reference('reservas')
    
    try:  # Agregar bloque try-except
        reservas = ref_reservas.get()
        if reservas is None:
            reservas = {}  # Inicializar reservas como un diccionario vacío si no existe
        
        # Obtén la referencia a la tabla "salones"
        ref_salones = db.reference('salones')
        salones = ref_salones.get()

        # Muestra la disponibilidad en la página principal
        st.header('Disponibilidad de Salones')
        salones_disponibles = {}  # Diccionario para almacenar los salones disponibles

        for salon_id, salon in salones.items():
            disponible = True  # Asume que el salón está disponible inicialmente

            for reserva_id, reserva in reservas.items():
                if reserva['fecha'] == datetime.strptime(fecha, '%d-%m-%Y').strftime('%Y%m%d') and reserva['salon_key'] == salon_id:
                    # Verifica si la reserva se solapa con la franja horaria solicitada
                    hora_inicio_reserva = datetime.strptime(reserva['hora_inicio'], '%H:%M').time()
                    hora_fin_reserva = datetime.strptime(reserva['hora_fin'], '%H:%M').time()
                    if hora_inicio_dt < hora_fin_reserva and hora_fin_dt > hora_inicio_reserva:
                        disponible = False
                        break  # Si se solapa, el salón no está disponible

            if disponible:
                salones_disponibles[salon_id] = salon
                with st.expander(f"{salon['nombre']}"):
                    st.write(f"**Ubicación:** {salon['ubicacion']}")
                    st.write(f"**Capacidad:** {salon['capacidad']}")

        return salones_disponibles

    except Exception as e:
        st.error(f"Error al obtener las reservas: {e}")
        return {}  # Retornar un diccionario vacío en caso de error

def calcular_presupuesto(salon, servicios_seleccionados):
    precio_salon = salon['precio'] if salon else 0
    precio_servicios = sum([servicio['precio'] for servicio in servicios_seleccionados.values()])
    return precio_salon + precio_servicios

def mostrar_servicios():
    ref = db.reference('servicios')
    servicios = ref.get()

    st.subheader('Servicios Adicionales')

    # Inicializar el estado de los checkboxes si no existe
    if 'servicios_seleccionados' not in st.session_state:
        st.session_state.servicios_seleccionados = {}

    for servicio_id, servicio in servicios.items():
        if st.checkbox(f"{servicio['nombre']} - {servicio['descripcion']} (${servicio['precio']})", key=f"servicio_{servicio_id}"):
            st.session_state.servicios_seleccionados[servicio_id] = servicio
        else:
            # Eliminar el servicio si se desmarca el checkbox
            st.session_state.servicios_seleccionados.pop(servicio_id, None)

    return st.session_state.servicios_seleccionados

def generar_id_unico(): return str(uuid.uuid4())

def confirmar_reserva(salon_key, fecha, hora_inicio, hora_fin, servicios_seleccionados, email_cliente, asistentes, tipo_evento, presupuesto_total, notas_adicionales): 

    # Crea un nuevo ID de reserva
    reserva_id = generar_id_unico()

    # Convierte la fecha al formato YYYYMMDD
    fecha_yyyymmdd = datetime.strptime(fecha, '%d-%m-%Y').strftime('%Y%m%d') 

    # Verificar si se seleccionaron servicios adicionales
    if not servicios_seleccionados:
        servicios_seleccionados = {"servicio_no": {"nombre": "No", "descripcion": "Sin servicio adicional", "precio": 0}}  # Servicio "No" por defecto

    # Crea la reserva en la tabla de "reservas"
    ref_reservas = db.reference('reservas')  # Referencia a la tabla "reservas"
    ref_reservas.child(reserva_id).set({
        "salon_key": salon_key,
        "fecha": fecha_yyyymmdd,
        "hora_inicio": hora_inicio,
        "hora_fin": hora_fin,
        "cliente": email_cliente,
        "servicios": servicios_seleccionados,
        "asistentes": asistentes,
        "tipo_evento": tipo_evento,
        "notas_adicionales": notas_adicionales,
        "presupuesto": presupuesto_total,
        "pagada": "No"
    })

    st.success(f"Reserva confirmada con ID: {reserva_id}")

firebase_app = inicializar_firebase()
if 'firebase_app' not in st.session_state: st.session_state['firebase_app'] = firebase_app

# --- Streamlit UI ---
st.title("Banquetería Hollan")
st.write("Sistema de gestión integral para la Banquetería Hollan")

# --- Autenticación ---
if 'user_info' not in st.session_state:
    st.write("Por favor, inicia sesión o crea una cuenta para continuar.")

    col1,col2,col3 = st.columns([1,2,1])
    auth_form = col2.form(key='Authentication form',clear_on_submit=False)
    email = auth_form.text_input(label='Email')
    password = auth_form.text_input(label='Contraseña',type='password')
    auth_notification = col2.empty()

    # --- Botón para crear cuenta ---
    if col2.button("Crear Cuenta"):
        st.session_state.mostrar_formulario_registro = True
        st.rerun()

    if 'mostrar_formulario_registro' in st.session_state and st.session_state.mostrar_formulario_registro:
        with st.form("registro_form"):
            st.header("Crear una nueva cuenta")
            email_registro = st.text_input("Correo electrónico:")
            password_registro = st.text_input("Contraseña:", type="password")

            if st.form_submit_button("Registrarse"):
                try:
                    # Crear usuario en Firebase Authentication
                    user = auth.create_user(
                        email=email_registro,
                        password=password_registro
                    )

                    # Establecer el rol del usuario como "client"
                    auth.set_custom_user_claims(user.uid, {"rol": "client"})

                    st.success("¡Cuenta creada con éxito! Ahora puedes iniciar sesión.")
                    st.session_state.mostrar_formulario_registro = False  # Ocultar formulario de registro
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al crear la cuenta: {e}")

    if auth_form.form_submit_button(label='Iniciar Sesión',use_container_width=True,type='primary'):
        with auth_notification, st.spinner('Iniciando Sesión'):
            sign_in(email,password)
    if 'auth_success' in st.session_state:
        auth_notification.success(st.session_state.auth_success)
        del st.session_state.auth_success
    elif 'auth_warning' in st.session_state:
        auth_notification.warning(st.session_state.auth_warning)
        del st.session_state.auth_warning

else:
    # --- Usuario autenticado ---
    st.write('Bienvenido, ',st.session_state.user_info.get('email'))
    st.write('Tipo de usuario: ', st.session_state.user_info.get('rol'))

    # --- Botón de cerrar sesión en la barra lateral ---
    with st.sidebar:  
        if st.button('Cerrar sesión'):
            sign_out()  # Llama a la función sign_out de auth.py
            st.rerun()

    # --- Formulario para nueva reserva ---
    if 'mostrar_formulario' not in st.session_state:
        st.session_state.mostrar_formulario = False  # Inicializar la variable de estado
    if 'salon_seleccionado' not in st.session_state:  # Inicializar salon_seleccionado
        st.session_state.salon_seleccionado = None
    if 'ver_disponibilidad' not in st.session_state:  # Nueva variable de estado
        st.session_state.ver_disponibilidad = False
    
    # --- Botón "Ver mis reservas" solo para clientes ---
    if st.session_state.user_info.get('rol') == 'client':
        if st.button("Mis reservas"):
            if 'mostrar_mis_reservas' in st.session_state and st.session_state.mostrar_mis_reservas:
                st.session_state.mostrar_mis_reservas = False
                st.rerun()

            st.session_state.mostrar_mis_reservas = True
            st.rerun()
        
    # --- Mostrar mis reservas (solo para clientes) ---
    if 'mostrar_mis_reservas' in st.session_state and st.session_state.mostrar_mis_reservas:
        st.header("Mis Reservas")

        # Obtener las reservas del usuario desde la base de datos
        ref_reservas = db.reference('reservas')
        reservas = ref_reservas.get()


        try:  # Agregar bloque try-except
            reservas = ref_reservas.get()
            if reservas is None:  # Verificar si la tabla "reservas" está vacía o no existe
                st.info("No existen reservas.") 
            else:
                mis_reservas = { reserva_id: reserva for reserva_id, reserva in reservas.items() if reserva['cliente'] == st.session_state.user_info.get('email')}

                if mis_reservas:
                    # Ordenar las reservas por fecha y hora
                    reservas_ordenadas = sorted(mis_reservas.items(), key=lambda item: (item[1]['fecha'], item[1]['hora_inicio']))

                    for reserva_id, reserva in reservas_ordenadas:
                        fecha_formateada = datetime.strptime(reserva['fecha'], '%Y%m%d').strftime('%d-%m-%Y')
                        with st.expander(f"{reserva['salon_key']}, {fecha_formateada} {reserva['hora_inicio']} - {reserva['hora_fin']} - Reserva ID: {reserva_id}"):
                            st.write(f"**Salón:** {reserva['salon_key']}")
                            st.write(f"**Fecha:** {fecha_formateada}")
                            st.write(f"**Hora inicio:** {reserva['hora_inicio']}")
                            st.write(f"**Hora fin:** {reserva['hora_fin']}")
                            st.write(f"**Cliente:** {reserva['cliente']}")
                            st.write(f"**Asistentes:** {reserva['asistentes']}")
                            st.write(f"**Tipo de evento:** {reserva['tipo_evento']}")
                            st.write(f"**Servicios adicionales:**")
                            for servicio_id, servicio in reserva['servicios'].items():
                                st.write(f"   - {servicio['nombre']}") 
                            st.write(f"**Presupuesto total:** {reserva['presupuesto']}")
                            st.write(f"**Pagada:** {reserva['pagada']}")

                            # --- Botón "Pagar" ---

                            if reserva['pagada'] == "No": 
                                if st.button(f"Pagar reserva {reserva_id}"):
                                    # Actualizar el estado de "pagada" a True en la base de datos
                                    ref_reservas.child(reserva_id).update({"pagada": "Si"})
                                    st.success("Reserva pagada con éxito.")
                                    st.rerun()  # Recargar la página para reflejar el cambio

                            # --- Botón "Borrar Reserva" ---
                            if st.button(f"Borrar reserva {reserva_id}"):
                                ref_reservas.child(reserva_id).delete()
                                st.success("Reserva borrada con éxito.")
                                st.rerun()
                else:
                    st.info("No tienes reservas registradas.")
        except Exception as e:  # Capturar la excepción
            st.error(f"Error al obtener las reservas: {e}")
            st.info("No existen reservas.")  # Mostrar mensaje al usuario

    if st.button("Realizar una nueva reserva"):  # Botón para mostrar el formulario
            if 'mostrar_formulario' in st.session_state and st.session_state.mostrar_formulario:
                st.session_state.mostrar_formulario = False
                st.rerun()

            st.session_state.mostrar_formulario = True
            st.rerun() 

    if st.session_state.mostrar_formulario:  # Mostrar el formulario solo si la variable es True
            with st.form("nueva_reserva"):
                st.header("Realizar una nueva reserva")
                fecha = st.date_input("Fecha:", format="DD-MM-YYYY").strftime('%d-%m-%Y')  # Usar st.date_input()
                hora = st.text_input("Hora (HH:MM - HH:MM):", "")
                asistentes = st.number_input("Número de asistentes:", min_value=1, step=1)
                tipo_evento = st.selectbox("Tipo de evento:", ["Boda", "Cumpleaños", "Corporativo", "Otro"])

                # Agregar campo para notas adicionales
                notas_adicionales = st.text_area("Notas adicionales:")
                if not notas_adicionales:  # Si el usuario no escribe nada
                    notas_adicionales = "Sin detalles adicionales"

                submitted = st.form_submit_button("Ver disponibilidad")
                if submitted:
                    st.session_state.ver_disponibilidad = True  # Actualizar la variable de estado
                    st.rerun()  # Reiniciar para mostrar el formulario de salones
            if st.session_state.ver_disponibilidad:  # Mostrar el formulario de salones si se hizo clic en "Ver disponibilidad"
                try:
                    # Validar formato de fecha y hora
                    datetime.strptime(fecha, '%d-%m-%Y')
                    hora_inicio, hora_fin = hora.split(' - ')
                    datetime.strptime(hora_inicio, '%H:%M')
                    datetime.strptime(hora_fin, '%H:%M')

                    # Mostrar disponibilidad
                    salones_disponibles = mostrar_disponibilidad(fecha, hora_inicio, hora_fin)

                    if salones_disponibles:
                        # Mostrar servicios adicionales
                        servicios_seleccionados = mostrar_servicios()

                        # Seleccionar salón con radio buttons
                        st.subheader("Selecciona un salón:")
                        salon_seleccionado_key = st.radio(  # Obtener la clave del salón seleccionado
                            "Salones:",
                            list(salones_disponibles.keys()),
                            format_func=lambda key: f"{salones_disponibles[key]['nombre']} - {salones_disponibles[key]['ubicacion']} - Capacidad: {salones_disponibles[key]['capacidad']}",
                            key="salon_radio"
                        )   
                        st.session_state.salon_seleccionado = salones_disponibles[salon_seleccionado_key]  # Guardar el salón seleccionado en session_state  

                        # Mostrar presupuesto
                        presupuesto_total = calcular_presupuesto(st.session_state.salon_seleccionado, servicios_seleccionados)
                        st.write(f"**Presupuesto total:** ${presupuesto_total}")

                        if st.session_state.salon_seleccionado:  # Mostrar el botón solo si se ha seleccionado un salón
                            if st.button("Confirmar reserva"):
                                confirmar_reserva(salon_seleccionado_key, fecha, hora_inicio, hora_fin, servicios_seleccionados, st.session_state.user_info.get('email'), asistentes, tipo_evento, presupuesto_total, notas_adicionales)  # Pasar la clave del salón
         
                    else:
                        st.warning("No hay salones disponibles para la fecha y hora especificadas.")        

                except ValueError:
                    st.error("Formato de hora inválido.")
    
    # --- Mostrar botón "Gestionar reservas" solo para admin ---
    if st.session_state.user_info.get('rol') == 'admin': 
        if st.button("Gestionar reservas"):
            st.session_state.mostrar_gestion_reservas = True
            st.rerun()

    # --- Gestión de reservas ---
    if 'mostrar_gestion_reservas' in st.session_state and st.session_state.mostrar_gestion_reservas:
        st.header("Gestionar Reservas")

        # Obtener las reservas de la base de datos
        ref_reservas = db.reference('reservas')
        try:  # Agregar bloque try-except
            reservas = ref_reservas.get()
            if reservas is None:  # Verificar si la tabla "reservas" está vacía o no existe
                st.info("No existen reservas.")
            else:
                if reservas:
                    # Ordenar las reservas por fecha y hora
                    reservas_ordenadas = sorted(reservas.items(), key=lambda item: (item[1]['salon_key'], item[1]['fecha'], item[1]['hora_inicio'])) 

                    # Mostrar las reservas en una tabla
                    for reserva_id, reserva in reservas_ordenadas:

                        fecha_formateada = datetime.strptime(reserva['fecha'], '%Y%m%d').strftime('%d-%m-%Y')

                        with st.expander(f"{reserva['salon_key']}, {fecha_formateada} {reserva['hora_inicio']} - {reserva['hora_fin']} - Reserva ID: {reserva_id}"):
                            st.write(f"**Salón:** {reserva['salon_key']}")
                            st.write(f"**Fecha:** {fecha_formateada}")
                            st.write(f"**Hora inicio:** {reserva['hora_inicio']}")
                            st.write(f"**Hora fin:** {reserva['hora_fin']}")
                            st.write(f"**Cliente:** {reserva['cliente']}")
                            st.write(f"**Asistentes:** {reserva['asistentes']}")
                            st.write(f"**Tipo de evento:** {reserva['tipo_evento']}")
                            st.write(f"**Servicios:**")
                            for servicio_id, servicio in reserva['servicios'].items():
                                st.write(f"   - {servicio['nombre']}")
                            st.write(f"**Notas adicionales:** {reserva['notas_adicionales']}")  # Mostrar las notas adicionales

                            # Botones para editar y borrar
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(f"Editar reserva {reserva_id}"):
                                    # --- Lógica para editar la reserva ---
                                    print(f"Editando reserva {reserva_id}")

                                    with st.form(f"editar_reserva_{reserva_id}"):
                                        st.write("Editar reserva")

                                        # Campos editables del formulario
                                        salon_key = st.selectbox("Salón", ["salon1", "salon2"], index=["salon1", "salon2"].index(reserva['salon_key']))
                                        fecha = st.date_input("Fecha:", datetime.strptime(reserva['fecha'], '%Y%m%d'), format="DD-MM-YYYY")  
                                        hora_inicio = st.text_input("Hora inicio (HH:MM):", reserva['hora_inicio'])
                                        hora_fin = st.text_input("Hora fin (HH:MM):", reserva['hora_fin'])
                                        asistentes = st.number_input("Número de asistentes:", min_value=1, step=1, value=reserva['asistentes'])
                                        tipo_evento = st.selectbox("Tipo de evento:", ["Boda", "Cumpleaños", "Corporativo", "Otro"], index=["Boda", "Cumpleaños", "Corporativo", "Otro"].index(reserva['tipo_evento']))

                                        # Obtener los servicios disponibles
                                        ref_servicios = db.reference('servicios')
                                        servicios_disponibles = ref_servicios.get()

                                        # Agregar campo para editar notas adicionales
                                        notas_adicionales = st.text_area("Notas adicionales:", reserva['notas_adicionales'])
                                        if not notas_adicionales:
                                            notas_adicionales = "Sin detalles adicionales"

                                        # --- Inicializar servicios_seleccionados con los servicios de la reserva ---
                                        servicios_seleccionados_key = f"servicios_seleccionados_{reserva_id}"
                                        if servicios_seleccionados_key not in st.session_state:
                                            st.session_state[servicios_seleccionados_key] = reserva['servicios'].copy()

                                        servicios_seleccionados = st.session_state[servicios_seleccionados_key]

                                        # Mostrar los servicios como checkboxes
                                        for servicio_id, servicio in servicios_disponibles.items():
                                            # Marcar los checkboxes de los servicios que ya están en la reserva
                                            checkbox_key = f"servicio_{servicio_id}_{reserva_id}"
                                            checked = servicio_id in reserva['servicios']
                                            if st.checkbox(f"{servicio['nombre']} - {servicio['descripcion']} (${servicio['precio']})", key=checkbox_key, value=checked):
                                                servicios_seleccionados[servicio_id] = servicio
                                            else:
                                                servicios_seleccionados.pop(servicio_id, None)

                                        if st.form_submit_button("Guardar cambios"):
                                            print("Botón Guardar cambios presionado")
                                            # Validar formato de fecha y hora
                                            try:
                                                print("Dentro del bloque try")
                                                fecha_yyyymmdd = fecha.strftime('%Y%m%d')

                                                # --- Crear un diccionario con solo los campos modificados ---
                                                datos_actualizados = {}
                                                for campo in ["salon_key", "fecha", "hora_inicio", "hora_fin", "asistentes", "tipo_evento", "servicios", "notas_adicionales"]:
                                                    nuevo_valor = locals()[campo]  # Obtener el valor de la variable local
                                                    if campo == "servicios":
                                                        nuevo_valor = servicios_seleccionados  # Usar el valor de servicios_seleccionados
                                                    if nuevo_valor != reserva[campo]:
                                                        datos_actualizados[campo] = nuevo_valor

                                                print("Datos actualizados:", datos_actualizados)

                                                if datos_actualizados:  # Verificar si hay cambios
                                                    ref_reservas.child(reserva_id).update(datos_actualizados)
                                                    st.success("Reserva actualizada con éxito.")
                                                    # --- Actualizar st.session_state con los servicios seleccionados ---
                                                    st.session_state[servicios_seleccionados_key] = servicios_seleccionados
                                                    st.rerun()
                                                else:
                                                    st.warning("No se ha realizado ningún cambio en la reserva.")

                                            except ValueError:
                                                st.error("Formato de fecha u hora inválido.")
                                            except Exception as e:  # Capturar cualquier otra excepción
                                                print(f"Error al guardar cambios: {e}")

                            with col2:
                                if st.button(f"Borrar reserva {reserva_id}"):
                                    # Lógica para borrar la reserva
                                    ref_reservas.child(reserva_id).delete()
                                    st.success("Reserva borrada con éxito.")
                                    st.rerun()
                else:
                    st.info("No hay reservas registradas.")
        except Exception as e:  # Capturar la excepción
            st.error(f"Error al obtener las reservas: {e}")
            st.info("No existen reservas.")