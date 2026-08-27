JARVIS OS — Asistente Personal de Voz con Interfaz HUD

Este proyecto consiste en el desarrollo de un asistente personal de voz interactivo en tiempo real, diseñado para ofrecer respuestas rápidas y fluidas mediante una interfaz gráfica tipo Sci-Fi inspirada en Stark Industries.


El objetivo principal fue construir una arquitectura capaz de procesar comandos de voz con baja latencia y mantener la fluidez de la interfaz gráfica sin bloqueos ni congelamientos durante el ciclo de vida del audio.


Estructura del Proyecto
El código está modularizado para separar la lógica del modelo de lenguaje, la síntesis de audio y el motor gráfico:


Plaintext

Jarvis-Assistant/

├── config/

│   └── settings.py # Configuración de credenciales y variables globales

├── core/

│   ├── llm_engine.py       # Integración con Gemini API, prompts y soporte de herramientas

│   └── voice_engine.py     # Captura de audio (STT) y generación de voz (TTS)

├── tools/

│   └── football_tool.py    # Integración de funciones personalizadas (Function Calling)

├── ui/

│   └── hud_gui.py          # Renderizado vectorial de la GUI con QPainter en PySide6

├── main.py                 # Orquestación del ciclo de vida y gestión de hilos

└── requirements.txt        # Librerías y dependencias

Guía de Instalación y Configuración

1. Requisitos del sistema
Python 3.10 o superior.

API Key de Google AI Studio.


2. Clonar el repositorio e instalar dependencias
Bash
# Clonar el proyecto
git clone https://github.com/TU-USUARIO/Jarvis-Assistant.git
cd Jarvis-Assistant

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (Windows)
.\venv\Scripts\activate

# Activar entorno virtual (Linux/macOS)
source venv/bin/activate

# Instalar librerías
pip install -r requirements.txt
3. Configurar API Key
Crea el archivo config/settings.py y define tu clave de acceso:

Python
GEMINI_API_KEY = "TU_API_KEY_AQUI"
Ejecución
Para iniciar el sistema, ejecuta el punto de entrada principal:

Bash
python main.py
Activación por voz: Di la palabra "Jarvis" en tu oración para enviarle un comando.

Comandos de salida: Di palabras clave como "salir", "cerrar" o "descansa" para terminar la ejecución de forma segura.

Tecnologías Utilizadas
Lenguaje: Python

Interfaz Gráfica: PySide6 (Qt for Python)

Inteligencia Artificial: Google GenAI SDK (gemini-3.5-flash-lite)

Reconocimiento de Voz (STT): speech_recognition, pyaudiowpatch / pyaudio

Síntesis de Voz (TTS): edge-tts, asyncio, playsound
