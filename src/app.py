import requests
import json

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/prod/token"
URL_ENDPOINT_SERVICE = "https://api.sicopweb.com/bi/prod/indicadores/renault/nacional"

EMAIL_USER = '<YOUR_EMAIL_USER>'
PWD_USER   = '<YOUR_PWD_USER>'
CLIENT_ID  = '<YOUR_CLIENT_ID>'
SECRET_KEY = '<YOUR_SECRET_KEY>'

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

def get_data(request_body, headers):
    payload = json.dumps(request_body)
    response = requests.request("POST", URL_ENDPOINT_SERVICE, headers=headers, data=payload)
    return response

user = UserCredentials(email=EMAIL_USER,pwd=PWD_USER)
client = ClientCredentials(client_id=CLIENT_ID,secret_key=SECRET_KEY)

#Obtenemos el token de acceso
token = get_access_token(user, client)

#Encabezados necesarios con token de acceso
headers = {
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {token}'
}

# Primer peticion para obtener datos
current_page = 1
request_body = {
  "fbyfechaini": "20240201",
  "fbyfechafin": "20240225",
  "frecuencia": "DIARIA",
  "page": current_page,
  "gby": "zona,region,plaza,distribuidor,auto,fuenteinformacion"
}
response = get_data(request_body, headers)
total_pages = int(response.headers['x-sicop-api-pages'])
current_page = int(response.headers['x-sicop-api-current-page'])
#Parseamos el resultado
data = response.json()
#Solo imprimir el total de elementos descargados en la iteraccion
print(f'Pagina: {current_page} de {total_pages}, Total Items: {len(data)}')

# Recorrido para obtener resto de paginas
while(current_page < total_pages):
    current_page = current_page + 1
    request_body = {
        "fbyfechaini": "20240201",
        "fbyfechafin": "20240225",
        "frecuencia": "DIARIA",
        "page": current_page,
        "gby": "zona,region,plaza,distribuidor,auto,fuenteinformacion"
    }
    response = get_data(request_body, headers)
    current_page = int(response.headers['x-sicop-api-current-page'])
    #Parseamos el resultado
    data = response.json()
    #Solo imprimir el total de elementos descargados en la iteraccion
    print(f'Pagina: {current_page} de {total_pages}, Total Items: {len(data)}')