import requests
import time

EMAIL_USER = '<YOUR_EMAIL_USER>'
PWD_USER   = '<YOUR_PWD_USER>'
CLIENT_ID  = '<YOUR_CLIENT_ID>'
SECRET_KEY = '<YOUR_SECRET_KEY>'
MARCA      = '<YOUR_MARK>'

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/prod/token"
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
    return response

start_time = time.time()

user = UserCredentials(email=EMAIL_USER,pwd=PWD_USER)
client = ClientCredentials(client_id=CLIENT_ID,secret_key=SECRET_KEY)

print('Get Access Token...')
# Obtenemos el token de acceso
token = get_access_token(user, client)

# Encabezados necesarios con token de acceso
headers = {
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {token}'
}

# Primer peticion para obtener datos
current_page = 1
common_params = {
    'origen':MARCA,
    'fbyfechaini':'20241201',
    'fbyfechafin':'20241231'
}
params = common_params | {
    'page': current_page
}

fulldata = []
print('Request data...')
response = get_data(params, headers)
total_pages = int(response.headers['x-sicop-api-pages'])
current_page = int(response.headers['x-sicop-api-current-page'])

#Parseamos el resultado
data = response.json()
fulldata.extend(data)
#Solo imprimir el total de elementos descargados en la iteraccion
print(f'Page: {current_page} of {total_pages}, Total records: {len(data)}')

# Recorrido para obtener resto de paginas
while(current_page < total_pages):
    current_page = current_page + 1
    params = common_params | {
            'page': current_page
    }
    response = get_data(params, headers)
    current_page = int(response.headers['x-sicop-api-current-page'])
    #Parseamos el resultado
    data = response.json()
    #Solo imprimir el total de elementos descargados en la iteraccion
    print(f'Page: {current_page} de {total_pages}, Total records: {len(data)}')
    fulldata.extend(data)

print(f'Total records: {len(fulldata)}')

# Calculamos total de prospectos acumulados en fulldata
total_leads = 0
total_digital_leads = 0
total_walkin_leads = 0
total_street_leads = 0
total_database_leads = 0

for row in fulldata:
    total_leads += int(row['prospectos'])
    total_walkin_leads += int(row['prospectospiso'])
    total_street_leads += int(row['prospectoscalle'])
    total_database_leads += int(row['prospectoscartera'])
    total_digital_leads += int(row['leads'])

print(f'Total Leads: {total_leads}')
print(f'Total Walk-in Leads: {total_walkin_leads}')
print(f'Total Street Leads: {total_street_leads}')
print(f'Total Database Leads: {total_database_leads}')
print(f'Total Digital Leads: {total_digital_leads}')


total_time = time.time() - start_time

print(f'Total time: {total_time} s')