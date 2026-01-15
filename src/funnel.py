import asyncio
import time
from os import getenv

import aiohttp
import requests
from dotenv import load_dotenv

load_dotenv()


def get_env_var(key: str, default: str = "") -> str:
    value = getenv(key, default)
    if not value:
        print(f"Advertencia: la variable de entorno '{key}' no esta definida. Usando valor por defecto.")
    return value


EMAIL_USER = get_env_var("EMAIL_USER")
PWD_USER = get_env_var("PWD_USER")
CLIENT_ID = get_env_var("CLIENT_ID")
SECRET_KEY = get_env_var("SECRET_KEY")
MARCA = get_env_var("MARCA")

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/v3/token"
URL_ENDPOINT_SERVICE = "https://api.sicopweb.com/funnel/qa/indicadores/nacional/detalle"


class UserCredentials:

    def __init__(self, email: str, pwd: str):
        self.email = email
        self.pwd = pwd


class ClientCredentials:

    def __init__(self, client_id: str, secret_key: str):
        self.client_id = client_id
        self.secret_key = secret_key


def get_access_token(user_credentials: UserCredentials, client_credentials: ClientCredentials):
    data = {
        "email": user_credentials.email,
        "pwd": user_credentials.pwd,
        "client_id": client_credentials.client_id,
        "secret_key": client_credentials.secret_key,
    }

    headers = {
        "Content-type": "application/x-www-form-urlencoded",
    }

    response = requests.post(URL_AUTH_ENDPOINT, data=data, headers=headers)
    response.raise_for_status()

    respuesta_json = response.json()
    token = respuesta_json["token"]

    return token


async def fetch_page(session: aiohttp.ClientSession, headers: dict, params: dict, semaphore: asyncio.Semaphore):
    async with semaphore:
        async with session.get(URL_ENDPOINT_SERVICE, headers=headers, params=params) as response:
            response.raise_for_status()
            current_page = int(response.headers.get("x-sicop-api-current-page", params.get("page", 1)))
            total_pages = int(response.headers.get("x-sicop-api-pages", 1))
            data = await response.json()
            print(f"Pagina: {current_page} de {total_pages}, Total Items: {len(data)}")
            return current_page, total_pages, data


async def fetch_all_pages(headers: dict, common_params: dict, max_concurrency: int = 5):
    semaphore = asyncio.Semaphore(max_concurrency)
    async with aiohttp.ClientSession() as session:
        first_params = {**common_params, "page": 1}
        first_page, total_pages, first_data = await fetch_page(session, headers, first_params, semaphore)
        results = {first_page: first_data}

        if total_pages > 1:
            tasks = []
            for page in range(2, total_pages + 1):
                params = {**common_params, "page": page}
                tasks.append(asyncio.create_task(fetch_page(session, headers, params, semaphore)))

            for task in asyncio.as_completed(tasks):
                page, _, data = await task
                results[page] = data

        fulldata = []
        for page in sorted(results.keys()):
            fulldata.extend(results[page])

        return fulldata, total_pages


async def main():
    start_time = time.time()

    user = UserCredentials(email=EMAIL_USER, pwd=PWD_USER)
    client = ClientCredentials(client_id=CLIENT_ID, secret_key=SECRET_KEY)

    print("Obteniendo token de acceso...")
    token = get_access_token(user, client)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    params_cac = {
        "origen": MARCA,
        "fbyfechaini": "20260101",
        "fbyfechafin": "20260114",
        "fbyatiende": "CAC",
    }
    params_dealer = {
        "origen": MARCA,
        "fbyfechaini": "20260101",
        "fbyfechafin": "20260114",
        "fbyatiende": "DEALER",
    }
    params_total = {
        "origen": MARCA,
        "fbyfechaini": "20251202",
        "fbyfechafin": "20260102",
    }

    common_params = params_total

    print("Solicitando datos...")
    try:
        fulldata, total_pages = await fetch_all_pages(headers, common_params, max_concurrency=5)
    except (aiohttp.ClientError, asyncio.CancelledError) as e:
        print(f"Error al obtener datos: {e}")
        return

    print(f"Total Items: {len(fulldata)}")

    total_prospectos = 0
    total_prospectos_digitales = 0
    total_prospectos_inactivos = 0
    total_ventas = 0
    total_ventas_digitales = 0

    for row in fulldata:
        total_prospectos += int(row["prospectos"])
        total_prospectos_digitales += int(row["leads"])
        total_prospectos_inactivos += float(row["prospectosinactivos"])
        total_ventas += int(row["ventasentregadas"])
        total_ventas_digitales += int(row["ventasentregadasleads"])

    print(f"Prospectos: {total_prospectos}")
    print(f"ProspectosDigitales: {total_prospectos_digitales}")
    print(f"ProspectosInactivos: {total_prospectos_inactivos}")
    print(f"Ventas: {total_ventas}")
    print(f"VentasDigitales: {total_ventas_digitales}")

    total_time = time.time() - start_time
    print(f"Tiempo Total: {total_time} s")


if __name__ == "__main__":
    asyncio.run(main())
