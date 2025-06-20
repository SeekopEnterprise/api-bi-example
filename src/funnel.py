import requests
import time

from os import getenv
from dotenv import load_dotenv

load_dotenv()

def get_env_var(key: str, default: str = "") -> str:
    value = getenv(key, default)
    if value == "":
        print(f"Advertencia: la variable de entorno '{key}' no está definida. Usando valor por defecto.")
    return value

EMAIL_USER = get_env_var("EMAIL_USER")
PWD_USER   = get_env_var("PWD_USER")
CLIENT_ID  = get_env_var("CLIENT_ID")
SECRET_KEY = get_env_var("SECRET_KEY")
MARCA      = get_env_var("MARCA")

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/prod/token"
URL_ENDPOINT_SERVICE = f"https://api.sicopweb.com/funnel/prod/indicadores/nacional/detalle"

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
    headers = {
        'Content-type': 'application/x-www-form-urlencoded'
    }

    # Realizar la petición POST
    response = requests.post( URL_AUTH_ENDPOINT, data=data, headers=headers)
    response.raise_for_status()
    # Verificar el código de estado de la respuesta

    # Obtener los datos de respuesta como un diccionario de Python
    respuesta_json = response.json()
        
    # Acceder a los datos devueltos
    token = respuesta_json['token']

    return token

def get_data(params, headers):
    response = requests.request('GET', URL_ENDPOINT_SERVICE, headers=headers, params=params)
    response.raise_for_status()
    return response

start_time = time.time()

user = UserCredentials(email=EMAIL_USER,pwd=PWD_USER)
client = ClientCredentials(client_id=CLIENT_ID,secret_key=SECRET_KEY)

print('Obteniendo token de acceso...')
# Obtenemos el token de acceso
token = get_access_token(user, client)

# Encabezados necesarios con token de acceso
headers = {
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {token}'
}

params_cac = {
    'origen':MARCA,
    'fbyfechaini':'20250401',
    'fbyfechafin':'20250422',
    'fbyatiende':'CAC'
}
params_dealer = {
    'origen':MARCA,
    'fbyfechaini':'20250401',
    'fbyfechafin':'20250422',
    'fbyatiende':'DEALER'
}
params_total = {
    'origen':MARCA,
    'fbyfechaini':'20250401',
    'fbyfechafin':'20250422',
}
# Primer peticion para obtener datos
current_page = 1
common_params = params_total
params = common_params | {
    'page': current_page
}

fulldata = []
print('Solicitando datos...')
try:
    response = get_data(params, headers)
    total_pages = int(response.headers.get('x-sicop-api-pages', 1))
    current_page = int(response.headers.get('x-sicop-api-current-page', 1))
except requests.exceptions.HTTPError as e:
    print(e)

#Parseamos el resultado
data = response.json()
fulldata.extend(data)
#Solo imprimir el total de elementos descargados en la iteraccion
print(f'Pagina: {current_page} de {total_pages}, Total Items: {len(data)}')

# Recorrido para obtener resto de paginas
while(current_page < total_pages):
    try:
        current_page = current_page + 1
        params = common_params | {
                'page': current_page
        }
        response = get_data(params, headers)
        current_page = int(response.headers.get('x-sicop-api-current-page', current_page))
        #Parseamos el resultado
        data = response.json()
        #Solo imprimir el total de elementos descargados en la iteraccion
        print(f'Pagina: {current_page} de {total_pages}, Total Items: {len(data)}')
        fulldata.extend(data)
    except requests.exceptions.HTTPError as e:
        print(e)

print(f'Total Items: {len(fulldata)}')

# Calculamos total de prospectos acumulados en fulldata
total_prospectos = 0
total_prospectos_digitales = 0
total_prospectos_inactivos = 0

for row in fulldata:
    total_prospectos += int(row['prospectos'])
    total_prospectos_digitales += int(row['leads'])
    total_prospectos_inactivos += float(row['prospectosinactivos'])

print(f'Prospectos: {total_prospectos}')
print(f'ProspectosDigitales: {total_prospectos_digitales}')
print(f'ProspectosInactivos: {total_prospectos_inactivos}')

total_time = time.time() - start_time

print(f'Tiempo Total: {total_time} s')