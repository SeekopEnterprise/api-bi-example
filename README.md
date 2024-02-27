# Cliente para consumo de API

Este es un ejemplo sencillo de un cliente en Python para consumo del API de indicadores de BI.

## Instalacion

Se  recomienda usar un entorno virtual para no afectar la instalación general de Python

```bash
api-bi-example$ python3 -m venv .venv
```

Instalar primero los paquetes indicados en **requirements.txt**

```bash
api-bi-example$ pip install -r requirements.txt
```

## Flujo de consumo

1. Obtener token de acceso desde el servicio de autenticación.
2. Crear encabezado **Authorization** con el valor del token de acceso obtenido
3. Crear el payload de la petición.
4. Ejecutar una primera consulta para obtener encabezados con informacion de paginación
5. Si hay de una página como resultado se debe iterar usando un loop para obtener el resto de la informacion, cambiando de página con el parámetro **page**
