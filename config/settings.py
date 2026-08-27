import os
from dotenv import load_dotenv

#cargamos las variables de entorno desde el .env
load_dotenv()

#leemos la variable de entorno GEMINI_API_KEY
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#condicion para verificar que la variable exista
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY no está configurada en el archivo .env")


#leemos la variable de entorno FOOTBALL_DATA_API_KEY
FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

#condicion para verificar que la variable exista
if not FOOTBALL_DATA_API_KEY:
    raise ValueError("FOOTBALL_DATA_API_KEY no está configurada en el archivo .env")