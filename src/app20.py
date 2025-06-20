import json
import mysql.connector
import requests
import time
import logging
from os import getenv
from os.path import join
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno
load_dotenv()

USER_HOME = getenv("HOME") or getenv("USERPROFILE") or "."

def get_env_var(key: str, default: str = "") -> str:
    value = getenv(key, default)
    if not value:
        logging.warning(f"La variable de entorno '{key}' no está definida o vacía. Usando valor por defecto.")
    return value

EMAIL_USER = get_env_var("EMAIL_USER")
PWD_USER   = get_env_var("PWD_USER")
CLIENT_ID  = get_env_var("CLIENT_ID")
SECRET_KEY = get_env_var("SECRET_KEY")
MARCA      = get_env_var("MARCA")

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/prod/token"
URL_ENDPOINT_SERVICE = f"https://api.sicopweb.com/bi/prod/indicadores20/{MARCA}/nacional"

def loadConf(conf_file: str):
    separator = "="
    keys = {}
    with open(conf_file) as f:
        for line in f:
            if separator in line:
                name, value = line.split(separator, 1)
                keys[name.strip()] = value.strip()
    return keys

class UserCredentials:
    def __init__(self, email: str, pwd: str):
        self.email = email
        self.pwd = pwd

class ClientCredentials:
    def __init__(self, client_id: str, secret_key: str):
        self.client_id = client_id
        self.secret_key = secret_key

def get_access_token(userCredentials: UserCredentials, clientCredentials: ClientCredentials):
    data = {
        'email': userCredentials.email,
        'pwd': userCredentials.pwd,
        'client_id': clientCredentials.client_id,
        'secret_key': clientCredentials.secret_key
    }
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

def truncate_data(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("TRUNCATE TABLE sicopdb.analisisdiariobdc")
        connection.commit()
    except mysql.connector.Error as e:
        logging.error(f"Error al truncar la tabla: {e}")
        connection.rollback()
    finally:
        cursor.close()

def batch_insert_with_dicts(connection, insert_query, data):
    try:
        cursor = connection.cursor()
        cursor.executemany(insert_query, data)
        connection.commit()
        logging.info(f"{cursor.rowcount} filas fueron insertadas.")
    except mysql.connector.Error as e:
        logging.error(f"Error al insertar datos: {e}")
        connection.rollback()
    finally:
        cursor.close()

start_time = time.time()

user = UserCredentials(email=EMAIL_USER, pwd=PWD_USER)
client = ClientCredentials(client_id=CLIENT_ID, secret_key=SECRET_KEY)
#Obtenemos el token de acceso
token = get_access_token(user, client)

if not token:
    exit(1)

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

try:
    conf_path = join(USER_HOME, '.mysql', 'prod.conf')
    conf = loadConf(conf_path)

    conn = mysql.connector.connect(
        user=conf.get('user'),
        password=conf.get('password'),
        host='localhost',
        port='3306',
        database='sicopdb'
    )

    insert_query = """
    INSERT INTO sicopdb.analisisdiariobdc(
        anio, mes, dia, fecha,
        codigomarca, zona, region, plaza, distribuidor,
        fuenteinformacion, subcampana, recibidos, intentados,
        intentadosminutos, tiempopromediointentados,
        contactados, asignados, citas,
        citasregistradas, `show`, confirmaciondecitas,
        ventas, ventasfacturadas
    )
    VALUES (
        %(anio)s, %(mes)s, %(dia)s, %(fecha)s,
        %(codigomarca)s, %(zona)s, %(region)s, %(plaza)s, %(distribuidor)s,
        %(fuenteinformacion)s, %(subcampana)s, %(recibidos)s, %(intentados)s,
        %(intentadosminutos)s, %(tiempopromediointentados)s,
        %(contactados)s, %(asignados)s, %(citas)s,
        %(citasregistradas)s, %(show)s, %(confirmaciondecitas)s,
        %(ventas)s, %(ventasfacturadas)s
    )"""

    common_params = {
        "fbyfechaini": "20250601",
        "fbyfechafin": "20250619",
        "frecuencia": "DIARIA",
        "gby": "zona,region,plaza,distribuidor,auto,fuenteinformacion,subcampana"
    }

    current_page = 1
    request_body = {**common_params, "page": current_page}

    response = get_data(request_body, headers)
    total_pages = int(response.headers.get('x-sicop-api-pages', 1))
    current_page = int(response.headers.get('x-sicop-api-current-page', 1))

    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Respuesta inesperada: se esperaba una lista de diccionarios.")

    truncate_data(conn)
    logging.info(f'Página: {current_page} de {total_pages}, Total Items: {len(data)}')
    batch_insert_with_dicts(conn, insert_query, data)

    while current_page < total_pages:
        current_page += 1
        request_body = {**common_params, "page": current_page}
        try:
            response = get_data(request_body, headers)
            current_page = int(response.headers.get('x-sicop-api-current-page', current_page))
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("Respuesta inesperada en iteración de páginas.")
            logging.info(f'Página: {current_page} de {total_pages}, Total Items: {len(data)}')
            batch_insert_with_dicts(conn, insert_query, data)
        except Exception as e:
            logging.error(f"Error en la página {current_page}: {e}")

except mysql.connector.Error as err:
    logging.error(f"Error de conexión a base de datos: {err}")
finally:
    if 'conn' in locals() and conn.is_connected():
        conn.close()

logging.info(f'Tiempo Total: {time.time() - start_time} s')
