import json
import requests
import time
import logging
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
URL_ENDPOINT_SERVICE = f"https://api.sicopweb.com/bi/prod/indicadores/{MARCA}/nacional"

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
    # Primer peticion para obtener datos
    current_page = 1
    common_params = {
        "fbyfechaini": "20250701",
        "fbyfechafin": "20250731",
        "frecuencia": "DIARIA",
        "gby": "zona,region,plaza,distribuidor,auto,fuenteinformacion,subcampana"
    }
    params = {**common_params, "page": current_page}

    fulldata = []
    logging.info('Solicitando datos...')
    response = get_data(params, headers)
    total_pages = int(response.headers.get('x-sicop-api-pages', 1))
    current_page = int(response.headers.get('x-sicop-api-current-page', 1))

    #Parseamos el resultado
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Respuesta inesperada: se esperaba una lista de diccionarios.")

    fulldata.extend(data)
    #Solo imprimir el total de elementos descargados en la iteraccion
    logging.info(f'Página: {current_page} de {total_pages}, Total Items: {len(data)}')
    # Recorrido para obtener resto de paginas
    while(current_page < total_pages):
        current_page += 1
        params = {**common_params, "page": current_page}
        try:
            response = get_data(params, headers)
            current_page = int(response.headers.get('x-sicop-api-current-page', current_page))
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("Respuesta inesperada en iteración de páginas.")
            #Solo imprimir el total de elementos descargados en la iteraccion
            logging.info(f'Página: {current_page} de {total_pages}, Total Items: {len(data)}')
            fulldata.extend(data)
        except Exception as e:
            logging.error(f"Error en la página {current_page}: {e}")

    logging.info(f'Total Items: {len(fulldata)}')

    # Calculamos total de prospectos acumulados en fulldata
    total_prospectos = 0
    total_prospectos_piso = 0
    total_prospectos_digitales = 0

    for row in fulldata:
        total_prospectos += int(row['prospectos'])
        total_prospectos_piso += int(row['prospectospiso'])
        total_prospectos_digitales += int(row['leads'])

    logging.info(f'Prospectos: {total_prospectos}')
    logging.info(f'ProspectosPiso: {total_prospectos_piso}')
    logging.info(f'ProspectosDigitales: {total_prospectos_digitales}')
except Exception as e:
    logging.error(f"Error General: {e}")

logging.info(f'Tiempo Total: {time.time() - start_time} s')