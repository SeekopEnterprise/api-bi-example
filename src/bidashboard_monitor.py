import json
import logging
import re
import sys
import time
from datetime import date, timedelta
from os import getenv
from typing import Optional
from urllib.parse import quote

import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

URL_AUTH_ENDPOINT = "https://api.sicopweb.com/auth/v3/token"
URL_DASHBOARD_BASE = (
    "https://analytics.sicopweb.com/pentaho/api/repos/"
    "%3Ahome%3AReportesSicopBI%3AReporteBIGeneral_token%3AReporteBIGeneral.wcdf/generatedContent"
)

DASHBOARD_PARAMS_STATIC = {
    "userid": "***REDACTED-USERID***",
    "password": "***REDACTED-CREDENTIAL-ROTATED***",
    "basedwh": "dwhchrysler",
    "marca": "TODOS",
    "auto": "TODOS",
    "nivelacceso": "6",
    "nivelinformacion": "NACIONAL",
    "fuente": "TODOS",
    "segmento": "TODOS",
    "subcampana": "TODOS",
    "grupocomercial": "TODOS",
    "tipocontacto": "TOTAL",
    "tipofecha": "MES_NEGOCIO",
}

ERROR_PATTERNS = (
    "Sorry, something went wrong",
    "Please try again or contact your system administrator",
    "errorPage",
    "Login",
)

REQUEST_TIMEOUT_SECONDS = 30


class UserCredentials:
    def __init__(self, email: str, pwd: str):
        self.email = email
        self.pwd = pwd


class ClientCredentials:
    def __init__(self, client_id: str, secret_key: str):
        self.client_id = client_id
        self.secret_key = secret_key


def get_access_token(user: UserCredentials, client: ClientCredentials) -> Optional[str]:
    data = {
        "email": user.email,
        "pwd": user.pwd,
        "client_id": client.client_id,
        "secret_key": client.secret_key,
    }
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(URL_AUTH_ENDPOINT, data=data, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        token = response.json().get("token")
        if not token:
            raise ValueError("Token no presente en la respuesta")
        return token
    except Exception as e:
        logging.error(f"Error al obtener bi_token: {e}")
        return None


def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    value = getenv(key, default)
    if required and not value:
        logging.error(f"Variable de entorno obligatoria '{key}' no está definida.")
        return None
    return value


def load_config() -> Optional[dict]:
    email = get_env_var("BI_MONITOR_EMAIL", required=True)
    pwd = get_env_var("BI_MONITOR_PWD", required=True)
    client_id = get_env_var("BI_MONITOR_CLIENT_ID", required=True)
    secret_key = get_env_var("BI_MONITOR_SECRET_KEY", required=True)

    if not all([email, pwd, client_id, secret_key]):
        return None

    nodes_csv = get_env_var("BI_MONITOR_NODES", default="node1,node3,node4") or ""
    nodes = {n.strip() for n in nodes_csv.split(",") if n.strip()}
    if not nodes:
        logging.error("BI_MONITOR_NODES no contiene nodos válidos.")
        return None

    try:
        max_attempts = int(get_env_var("BI_MONITOR_MAX_ATTEMPTS", default="15") or "15")
        same_node_threshold = int(get_env_var("BI_MONITOR_SAME_NODE_THRESHOLD", default="5") or "5")
        fail_streak_threshold = int(get_env_var("BI_MONITOR_FAIL_STREAK_THRESHOLD", default="3") or "3")
    except ValueError as e:
        logging.error(f"Valor numérico inválido en config: {e}")
        return None

    return {
        "email": email,
        "pwd": pwd,
        "client_id": client_id,
        "secret_key": secret_key,
        "nodes": nodes,
        "max_attempts": max_attempts,
        "same_node_threshold": same_node_threshold,
        "fail_streak_threshold": fail_streak_threshold,
    }


def compute_date_range(today: Optional[date] = None) -> tuple[str, str]:
    """Devuelve (fechainicio, fechafin) en formato YYYY-MM-DD.

    fechafin = ayer; fechainicio = primer día del mes de ayer.
    """
    today = today or date.today()
    ayer = today - timedelta(days=1)
    fechainicio = ayer.replace(day=1)
    return fechainicio.isoformat(), ayer.isoformat()


def build_dashboard_url(bi_token: str, fechainicio: str, fechafin: str) -> str:
    params = {
        **DASHBOARD_PARAMS_STATIC,
        "fechainicio": fechainicio,
        "fechafin": fechafin,
        "bi_token": bi_token,
    }
    query = "&".join(f"{k}={quote(str(v), safe='')}" for k, v in params.items())
    return f"{URL_DASHBOARD_BASE}?{query}"


JSESSIONID_NODE_RE = re.compile(r"([^;\s]+\.(node\d+))")


def extract_node(jsessionid_value: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Recibe el valor de la cookie JSESSIONID (ej. 'F9B96B9021FE390A9D86417EDB5A1AA9.node1').

    Devuelve (jsessionid_completo, node) o (None, None) si no matchea el patrón esperado.
    """
    if not jsessionid_value:
        return None, None
    match = JSESSIONID_NODE_RE.search(jsessionid_value)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def main() -> int:
    config = load_config()
    if config is None:
        return 2
    logging.info(f"Config cargada. Nodos objetivo: {sorted(config['nodes'])}")
    fechainicio, fechafin = compute_date_range()
    logging.info(f"Rango de fechas: {fechainicio} a {fechafin}")
    user = UserCredentials(email=config["email"], pwd=config["pwd"])
    client = ClientCredentials(client_id=config["client_id"], secret_key=config["secret_key"])
    bi_token = get_access_token(user, client)
    if not bi_token:
        return 2
    logging.info(f"bi_token obtenido (longitud={len(bi_token)})")
    dashboard_url = build_dashboard_url(bi_token, fechainicio, fechafin)
    logging.info(f"URL construida (longitud={len(dashboard_url)})")
    logging.debug(f"URL completa: {dashboard_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
