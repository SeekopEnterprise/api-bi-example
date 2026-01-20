import json
import requests
import time
import logging
import csv
from datetime import datetime
from os import getenv
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

def get_env_var(key: str, default: str = "") -> str:
    value = getenv(key, default)
    if not value:
        print(f"Advertencia: la variable de entorno '{key}' no está definida. Usando valor por defecto.")
    return value

EMAIL_USER = get_env_var("EMAIL_USER")
PWD_USER   = get_env_var("PWD_USER")
CLIENT_ID  = get_env_var("CLIENT_ID")
SECRET_KEY = get_env_var("SECRET_KEY")
MARCA      = get_env_var("MARCA")

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/v3/token"
URL_ENDPOINT_SERVICE = f"https://api.sicopweb.com/bi/qa/rt/quickcount/{MARCA}"

class UserCredentials:
    def __init__(self, email: str, pwd: str):
        self.email = email
        self.pwd = pwd

class ClientCredentials:
    def __init__(self, client_id: str, secret_key: str):
        self.client_id = client_id
        self.secret_key = secret_key

def get_access_token(userCredentials: UserCredentials, clientCredentials: ClientCredentials):
    # Credenciales de acceso
    data = {
        'email': userCredentials.email,
        'pwd': userCredentials.pwd,
        'client_id': clientCredentials.client_id,
        'secret_key': clientCredentials.secret_key
    }
    # Encabezados de la solicitud
    headers = {"Content-type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(URL_AUTH_ENDPOINT, data=data, headers=headers)
        response.raise_for_status()
        respuesta_json = response.json()
        token = respuesta_json.get("token")
        if not token:
            raise ValueError("Token no presente en la respuesta")
        return token
    except Exception as e:
        logging.error(f"Error al obtener el token de acceso: {e}")
        return None

def get_data(request_body, headers):
    payload = json.dumps(request_body)
    response = requests.post(URL_ENDPOINT_SERVICE, headers=headers, data=payload)
    response.raise_for_status()
    return response

def export_to_csv(data_list, fbyfechaini, fbyfechafin, frecuencia):
    """Genera un archivo CSV con separador pipe (|) a partir de la lista de datos."""
    if not data_list:
        logging.warning("No hay datos para exportar a CSV.")
        return None
    
    # Formato del nombre: AAAA-MM-DD_quickcount_fbyfechaini_fbyfechafin_frecuencia
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    filename = f"{fecha_actual}_quickcount_{fbyfechaini}_{fbyfechafin}_{frecuencia}.csv"
    
    # Obtener headers de las keys del primer elemento
    headers = list(data_list[0].keys())
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, delimiter='|')
        writer.writeheader()
        writer.writerows(data_list)
    
    logging.info(f"Archivo CSV generado: {filename}")
    return filename

start_time = time.time()

user = UserCredentials(email=EMAIL_USER,pwd=PWD_USER)
client = ClientCredentials(client_id=CLIENT_ID,secret_key=SECRET_KEY)
#Obtenemos el token de acceso
token = get_access_token(user, client)

if not token:
    exit(1)

#Encabezados necesarios con token de acceso
headers = {
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {token}'
}

try:
    # Parámetros de consulta
    fbyfechaini = "20260101"
    fbyfechafin = "20260118"
    frecuencia = "DIARIA"
    
    # Primer peticion para obtener datos
    current_page = 1
    common_params = {
        "fbyfechaini": fbyfechaini,
        "fbyfechafin": fbyfechafin,
        "frecuencia": frecuencia,
        "typedate": "FUNNEL",
        "indicadores": ["prospectos","intentados","citas","contactados","descartados","rechazados","shows","programacionserviciopv","programacionserviciopvdomic","showenagencia","showendomicilio","intentocontacto","confirmacionserviciopv"],
        "gby":["zona","region","plaza","distribuidor","auto","fuente","subcampana"]
    }

    request_body = {**common_params, "page": current_page} 

    fulldata = []
    logging.info('Solicitando datos...')
    response = get_data(request_body, headers)
    total_pages = int(response.headers.get('x-sicop-api-pages', 1))
    current_page = int(response.headers.get('x-sicop-api-current-page', 1))

    #Parseamos el resultado
    response_data = response.json()
    if not isinstance(response_data, dict):
        raise ValueError("Respuesta inesperada: se esperaba un diccionario.")

    # Extraer el array "data" del diccionario de respuesta
    data_items = response_data.get("data", [])
    fulldata.extend(data_items)
    #Solo imprimir el total de elementos descargados en la iteraccion
    logging.info(f'Página: {current_page} de {total_pages}, Total Items: {len(data_items)}')
    
    # Recorrido para obtener resto de paginas
    while current_page < total_pages:
        current_page += 1
        # Actualizar el número de página en los parámetros
        common_params["page"] = current_page
        try:
            response = get_data(common_params, headers)
            response_data = response.json()
            if not isinstance(response_data, dict):
                raise ValueError("Respuesta inesperada en iteración de páginas.")
            
            # Extraer el array "data" del diccionario de respuesta
            data_items = response_data.get("data", [])
            #Solo imprimir el total de elementos descargados en la iteraccion
            logging.info(f'Página: {current_page} de {total_pages}, Total Items: {len(data_items)}')
            fulldata.extend(data_items)
        except Exception as e:
            logging.error(f"Error en la página {current_page}: {e}")

    logging.info(f'Total Items: {len(fulldata)}')
    
    # Generar archivo CSV con todos los datos
    csv_filename = export_to_csv(fulldata, fbyfechaini, fbyfechafin, frecuencia)

    # Calculamos total de prospectos acumulados en fulldata
    total_prospectos_nuevos = 0
    total_prospectos_modificados = 0
    total_citas = 0

    for row in fulldata:
        total_prospectos_nuevos += int(row['prospectosnuevos'])
        total_prospectos_modificados += int(row['prospectosmodificados'])
        total_citas += int(row['citas'])

    logging.info(f'ProspectosNuevos: {total_prospectos_nuevos}')
    logging.info(f'ProspectosPiso: {total_prospectos_modificados}')
    logging.info(f'Citas: {total_citas}')
except Exception as e:
    logging.error(f"Error General: {e}")

logging.info(f'Tiempo Total: {time.time() - start_time} s')