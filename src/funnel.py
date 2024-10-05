import requests

EMAIL_USER = '<YOUR_EMAIL_USER>'
PWD_USER   = '<YOUR_PWD_USER>'
CLIENT_ID  = '<YOUR_CLIENT_ID>'
SECRET_KEY = '<YOUR_SECRET_KEY>'
MARCA      = '<YOUR_MARK>'

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/prod/token"
URL_ENDPOINT_SERVICE = f"https://api.sicopweb.com/funnel/dev/indicadores/nacional/detalle"

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
        "Content-type": "application/x-www-form-urlencoded"
    }

    # Realizar la petición POST
    response = requests.post( URL_AUTH_ENDPOINT, data=data, headers=headers)
    response.raise_for_status()
    # Verificar el código de estado de la respuesta

    # Obtener los datos de respuesta como un diccionario de Python
    respuesta_json = response.json()
        
    # Acceder a los datos devueltos
    token = respuesta_json["token"]

    return token

def get_data(params, headers):
    response = requests.request("GET", URL_ENDPOINT_SERVICE, headers=headers, params=params)
    return response

user = UserCredentials(email=EMAIL_USER,pwd=PWD_USER)
client = ClientCredentials(client_id=CLIENT_ID,secret_key=SECRET_KEY)

print("Obteniendo token de acceso...")
# Obtenemos el token de acceso
token = get_access_token(user, client)

# Encabezados necesarios con token de acceso
headers = {
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {token}'
}

# Parametros de peticion
params = {
    'origen':MARCA,
    'fbyfechaini':'20240901',
    'fbyfechafin':'20240930'
}

print("Solicitando datos...")
response = get_data(params, headers)

# Parseamos el resultado
data = response.json()
# Solo imprimir el total de elementos descargados en la iteraccion
print(f'Total Items: {len(data)}')

# Calculamos total de prospectos obtenidos
total_prospectos = 0
for row in data:
    total_prospectos += int(row['prospectos'])
print(f'Prospectos: {total_prospectos}')