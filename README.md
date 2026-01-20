# Cliente para consumo de API

Este es un ejemplo sencillo de un cliente en Python para consumo del API de indicadores de BI.

## Instalacion

Se  recomienda usar un entorno virtual para no afectar la instalación general de Python

```bash
api-bi-example$ python -m venv .venv
```

Activar el entorno virtual

```bash
api-bi-example$ ./.venv/scripts/activate
```

Instalar primero los paquetes indicados en **requirements.txt**

```bash
api-bi-example$ pip install -r requirements.txt
```

## Ejecucion

Crear un archivo llamado .env

``` bash
api-bi-example$ echo. > .env
```

Edita del archivo y declara las siguientes variables, asignando las credenciales proporcionadas por el equipo de SEEKOP

- EMAIL_USER
- PWD_USER
- CLIENT_ID
- SECRET_KEY
- MARCA

Ejemplo:

``` bash
EMAIL_USER = 'USUARIO'
PWD_USER   = 'PASSWORD'
CLIENT_ID  = 'ID'
SECRET_KEY = 'SECRET_KEY'
MARCA      = 'MIMARCA'
```

Una vez actualizadas solo ejecuta:

```bash
api-bi-example$ python src/app.py
```

## Flujo de consumo

1. Obtener token de acceso desde el servicio de autenticación.
2. Crear encabezado **Authorization** con el valor del token de acceso obtenido
3. Crear el payload de la petición.
4. Ejecutar una primera consulta para obtener encabezados con informacion de paginación
5. Si hay más de una página como resultado se debe iterar usando un loop para obtener el resto de la informacion, cambiando de página con el parámetro **page**
