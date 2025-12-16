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
        print(f"Warning: Environment variable '{key}' is not defined. Setting default value")
    return value

EMAIL_USER = get_env_var("EMAIL_USER")
PWD_USER   = get_env_var("PWD_USER")
CLIENT_ID  = get_env_var("CLIENT_ID")
SECRET_KEY = get_env_var("SECRET_KEY")
MARCA      = get_env_var("MARCA")

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/v3/token"
URL_ENDPOINT_SERVICE = f"https://api.sicopweb.com/funnel/v8/indicadores/nacional/detalle/general"

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

def get_data(params, headers):
    response = requests.request('GET', URL_ENDPOINT_SERVICE, headers=headers, params=params)
    response.raise_for_status()
    return response

start_time = time.time()

user = UserCredentials(email=EMAIL_USER,pwd=PWD_USER)
client = ClientCredentials(client_id=CLIENT_ID,secret_key=SECRET_KEY)
logging.info('Get Access Token...')
# Obtenemos el token de acceso
token = get_access_token(user, client)

if not token:
    exit(1)

# Encabezados necesarios con token de acceso
headers = {
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {token}'
}

try:
    # Primer peticion para obtener datos
    current_page = 1
    common_params = {
        'origen':MARCA,
        'fbyfechaini':'20251101', 
        'fbyfechafin':'20251130'
    }
    params = {**common_params, "page": current_page}

    fulldata = []
    total_pages = 0
    current_page = 0
    response = None
    total_records = 0

    logging.info('Request data...')
    response = get_data(params, headers)
    total_pages = int(response.headers.get('x-sicop-api-pages', 1))
    current_page = int(response.headers.get('x-sicop-api-current-page', 1))

    #Parseamos el resultado
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Unexpected response: response not is dictionary")
    
    total_records = len(data)
    fulldata.extend(data)

    #Solo imprimir el total de elementos descargados en la iteraccion
    logging.info(f'Page: {current_page} of {total_pages}, Total records: {total_records}')

    # Recorrido para obtener resto de paginas
    while(current_page < total_pages):
        current_page = current_page + 1
        params = {**common_params, "page": current_page}
        try:
            response = get_data(params, headers)
            current_page = int(response.headers.get('x-sicop-api-current-page', current_page))
            #Parseamos el resultado
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("Unexpected response in pages iterations")
            total_records = len(data)
            #Solo imprimir el total de elementos descargados en la iteraccion
            logging.info(f'Page: {current_page} de {total_pages}, Total records: {total_records}')
            fulldata.extend(data)
        except Exception as e:
            logging.error(f"Error in page {current_page}: {e}")

    logging.info(f'Total records: {len(fulldata)}')

    # Calculamos total de prospectos acumulados en fulldata
    total_leads = 0
    total_valid = 0
    total_shows = 0
    total_test_drive = 0
    total_quotes = 0
    total_sales = 0
    total_delivery = 0

    total_digital_leads = 0
    total_walkin_leads = 0
    total_street_leads = 0
    total_database_leads = 0

    total_digital_valid = 0
    total_walkin_valid = 0
    total_street_valid = 0
    total_database_valid = 0

    total_quotes = 0
    total_quotes_walkin = 0
    total_quotes_street = 0
    total_quotes_db = 0
    total_quotes_digital = 0

    total_quotes_unique = 0
    total_quotes_walkin_unique = 0
    total_quotes_street_unique = 0
    total_quotes_db_unique = 0
    total_quotes_digital_unique = 0

    total_inactive = 0.0
    total_digital_inactive = 0.0
    total_walkin_inactive = 0.0
    total_street_inactive = 0.0
    total_database_inactive = 0.0

    intentados = 0.0
    intentados_minutos = 0.0

    total_apartados = 0
    total_digital_apartados = 0
    total_walkin_apartados = 0
    total_street_apartados = 0
    total_database_apartados = 0

    total_citas = 0
    total_digital_citas = 0
    total_walkin_citas = 0
    total_street_citas = 0
    total_database_citas = 0

    for row in fulldata:
        total_leads += row['prospectos']
        total_valid += row['asignados']
        total_shows += row['shows']
        total_test_drive += row['prospectoscondemo']
        total_quotes += row['prospectosconcotizacion']
        total_sales += row['ventasfacturadas']
        total_delivery += row['ventasentregadas']

        total_walkin_leads += row['prospectospiso']
        total_street_leads += row['prospectoscalle']
        total_database_leads += row['prospectoscartera']
        total_digital_leads += row['leads']

        total_walkin_valid += row['asignadospiso']
        total_street_valid += row['asignadoscalle']
        total_database_valid += row['asignadoscartera']
        total_digital_valid += row['asignadosleads']

        total_quotes += row['cotizaciones']
        total_quotes_walkin += row['cotizacionespiso']
        total_quotes_street += row['cotizacionescalle']
        total_quotes_db += row['cotizacionescartera']
        total_quotes_digital += row['cotizacionesleads']

        total_quotes_unique += row['prospectosconcotizacion']
        total_quotes_walkin_unique += row['prospectosconcotizacionpiso']
        total_quotes_street_unique += row['prospectosconcotizacioncalle']
        total_quotes_db_unique += row['prospectosconcotizacioncartera']
        total_quotes_digital_unique += row['prospectosconcotizacionleads']

        total_inactive += float(row['prospectosinactivos'])
        total_walkin_inactive += float(row['prospectosinactivospiso'])
        total_street_inactive += float(row['prospectosinactivoscalle'])
        total_database_inactive += float(row['prospectosinactivoscartera'])
        total_digital_inactive += float(row['prospectosinactivosleads'])

        intentados += float(row['intentados'])
        if(row['intentadosminutos'] ):
            intentados_minutos += float(row['intentadosminutos'])

        total_apartados += row['apartados']
        total_walkin_apartados += row['apartadospiso']
        total_street_apartados += row['apartadoscalle']
        total_database_apartados += row['apartadoscartera']
        total_digital_apartados += row['apartadosleads']

        total_citas += row['citas']
        total_walkin_citas += row['citaspiso']
        total_street_citas += row['citascalle']
        total_database_citas += row['citascartera']
        total_digital_citas += row['citasleads']

    logging.info(f'===== DOWNLOAD INFO =====')
    logging.info(f'Total Leads: {total_leads}')
    logging.info(f'Total Valid: {total_valid}')
    logging.info(f'Total Shows: {total_shows}')
    logging.info(f'Total Test drive: {total_test_drive}')
    logging.info(f'Total Quotes: {total_quotes}')
    logging.info(f'Total Sales: {total_sales}')
    logging.info(f'Total Delivery: {total_delivery}')

#    logging.info(f'Total Leads: {total_leads}')
#    logging.info(f'Total Walk-in Leads: {total_walkin_leads}')
#    logging.info(f'Total Street Leads: {total_street_leads}')
#    logging.info(f'Total Database Leads: {total_database_leads}')
#    logging.info(f'Total Digital Leads: {total_digital_leads}')

    logging.info(f'===== Asignados =====')
    logging.info(f'Total Valid: {total_valid}')
    logging.info(f'Total Walk-in Quotes: {total_walkin_valid}')
    logging.info(f'Total Street Quotes: {total_street_valid}')
    logging.info(f'Total Database Quotes: {total_database_leads}')
    logging.info(f'Total Digital Valid: {total_digital_valid}')

    logging.info(f'===== Cotizaciones =====')
    logging.info(f'Total Quotes: {total_quotes}')
    logging.info(f'Total Walk-in Quotes: {total_quotes_walkin}')
    logging.info(f'Total Street Quotes: {total_quotes_street}')
    logging.info(f'Total Database Quotes: {total_quotes_db}')
    logging.info(f'Total Digital Quotes: {total_quotes_digital}')

    logging.info(f'===== Prospectos con Cotizacion =====')
    logging.info(f'Total Quotes Unique: {total_quotes_unique}')
    logging.info(f'Total Walk-in Quotes  Unique: {total_quotes_walkin_unique}')
    logging.info(f'Total Street Quotes Unique: {total_quotes_street_unique}')
    logging.info(f'Total Database Quotes: Unique {total_quotes_db_unique}')
    logging.info(f'Total Digital Quotes Unique: {total_quotes_digital_unique}')

    logging.info(f'===== Inactivos =====')
    logging.info(f'Total Inactive: {total_inactive}')
    logging.info(f'Total Walk-in Inactive: {total_walkin_inactive}')
    logging.info(f'Total Street Inactive: {total_street_inactive}')
    logging.info(f'Total Database Inactive: {total_database_inactive}')
    logging.info(f'Total Digital Inactive: {total_digital_inactive}')

    logging.info(f'===== Intentados =====')
    logging.info(f'Intentados: {intentados}')
    logging.info(f'Intentados minutos: {intentados_minutos}')
    logging.info(f'Tiempo: {intentados_minutos/intentados}')

    logging.info(f'===== Apartados =====')
    logging.info(f'Total Apartados: {total_apartados}')
    logging.info(f'Total Walk-in Apartados: {total_walkin_apartados}')
    logging.info(f'Total Street Apartados: {total_street_apartados}')
    logging.info(f'Total Database Apartados: {total_database_apartados}')
    logging.info(f'Total Digital Apartados: {total_digital_apartados}')

    logging.info(f'===== Citas =====')
    logging.info(f'Total Citas: {total_citas}')
    logging.info(f'Total Walk-in Citas: {total_walkin_citas}')
    logging.info(f'Total Street Citas: {total_street_citas}')
    logging.info(f'Total Database Citas: {total_database_citas}')
    logging.info(f'Total Digital Citas: {total_digital_citas}')

except Exception as e:
    logging.error(f"General Error: {e}")

logging.info(f'Total time: {time.time() - start_time} s')