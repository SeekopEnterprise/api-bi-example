import requests
import json
import mysql.connector
import os

USER_HOME = os.environ['userprofile']

EMAIL_USER = '<YOUR_EMAIL_USER>'
PWD_USER   = '<YOUR_PWD_USER>'
CLIENT_ID  = '<YOUR_CLIENT_ID>'
SECRET_KEY = '<YOUR_SECRET_KEY>'
MARCA      = '<YOUR_MARK>'

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/prod/token"
URL_ENDPOINT_SERVICE = f"https://api.sicopweb.com/bi/prod/indicadores20/{MARCA}/nacional"

def loadConf(conf_file:str):
    separator = "="
    keys = {}
    with open(conf_file) as f:
        for line in f:
            if separator in line:
                # Find the name and value by splitting the string
                name, value = line.split(separator, 1)
                # Assign key value pair to dict
                # strip() removes white space from the ends of strings
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

def truncate_data(connection):
    try:
        cursor = connection.cursor()
        cursor.execute("truncate table sicopdb.analisisdiariobdc")
        connection.commit()
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        connection.rollback()
    finally:
        cursor.close()

def batch_insert_with_dicts(connection, insert_query, data):
    try:
        cursor = connection.cursor()
        cursor.executemany(insert_query, data)
        connection.commit()
        print(f"{cursor.rowcount} filas fueron insertadas.")
    except mysql.connector.Error as e:
        print(f"Error: {e}")
        connection.rollback()
    finally:
        cursor.close()

user = UserCredentials(email=EMAIL_USER,pwd=PWD_USER)
client = ClientCredentials(client_id=CLIENT_ID,secret_key=SECRET_KEY)

#Obtenemos el token de acceso
token = get_access_token(user, client)

#Encabezados necesarios con token de acceso
headers = {
  'Content-Type': 'application/json',
  'Authorization': f'Bearer {token}'
}


try:
    conf = loadConf(USER_HOME + '/.mysql/prod.conf')

    user = conf.get('user')
    password = conf.get('password')
    host = 'localhost'
    port='3306'

    conn = mysql.connector.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database='sicopdb')
    
    insert_query = """
    insert into sicopdb.analisisdiariobdc(
        anio, mes, dia, fecha,
        codigomarca, zona, region, plaza, distribuidor,
        fuenteinformacion, subcampana, recibidos, intentados,
        intentadosminutos, tiempopromediointentados,
        contactados, asignados, citas,
        citasregistradas, `show`, confirmaciondecitas,
        ventas, ventasfacturadas
    )
    values(
        %(anio)s, %(mes)s, %(dia)s, %(fecha)s,
        %(codigomarca)s, %(zona)s, %(region)s, %(plaza)s, %(distribuidor)s,
        %(fuenteinformacion)s, %(subcampana)s, %(recibidos)s, %(intentados)s,
        %(intentadosminutos)s, %(tiempopromediointentados)s,
        %(contactados)s, %(asignados)s, %(citas)s,
        %(citasregistradas)s, %(show)s, %(confirmaciondecitas)s,
        %(ventas)s, %(ventasfacturadas)s
    )"""

    common_params = {
        "fbyfechaini": "20240901",
        "fbyfechafin": "20240921",
        "frecuencia": "DIARIA",
        "gby": "zona,region,plaza,distribuidor,auto,fuenteinformacion,subcampana"
    }

    # Primer peticion para obtener datos
    current_page = 1
    request_body = common_params | {
        "page": current_page
    }
    response = get_data(request_body, headers)
    total_pages = int(response.headers['x-sicop-api-pages'])
    current_page = int(response.headers['x-sicop-api-current-page'])
    #Parseamos el resultado
    data = response.json()
    truncate_data(conn)
    #Solo imprimir el total de elementos descargados en la iteraccion
    print(f'Pagina: {current_page} de {total_pages}, Total Items: {len(data)}')
    batch_insert_with_dicts(conn,insert_query,data)

    # Recorrido para obtener resto de paginas
    while(current_page < total_pages):
        current_page = current_page + 1
        request_body = common_params | {
            "page": current_page
        }
        response = get_data(request_body, headers)
        current_page = int(response.headers['x-sicop-api-current-page'])
        #Parseamos el resultado
        data = response.json()
        #Solo imprimir el total de elementos descargados en la iteraccion
        print(f'Pagina: {current_page} de {total_pages}, Total Items: {len(data)}')
        batch_insert_with_dicts(conn,insert_query,data)

except mysql.connector.Error as err:
    print(f"Error: {err}")
finally:
    conn.close()