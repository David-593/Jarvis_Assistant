import time
from datetime import datetime
from google import genai
from google.genai import types
from config.settings import GEMINI_API_KEY
from tools.football_tool import consult_last_matches


class JarvisBrain:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)

        sys_instruction = (
            "Eres Jarvis, una IA sofisticada, eficiente y elegante al estilo de Iron Man. "
            "Tu usuario principal es Andrés, ubicado en Montecristi / Manta, Ecuador.\n\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. SI EL MENSAJE CONTIENE '[MODO_DESPERTAR]': Proporciona un saludo matutino elegante. "
            "Saluda por su nombre ('Buen día, Andrés'), indícale la hora actual y dale un breve resumen del clima local. "
            "Ejemplo: 'Buen día, Andrés. Son las 8:00 AM. El clima en Montecristi es de 25°C con cielo despejado. Sistemas listos.'\n"
            "2. PARA CUALQUIER OTRO COMANDO O SALUDO NORMAL (ej. 'hola', 'cómo estás'): Responde de forma concisa, "
            "directa y rápida (máximo 1 o 2 oraciones), SIN dar datos del clima ni la hora a menos que te los pida explícitamente.\n"
            "3. Si usas una herramienta, resume los datos esenciales sin rodeos."
        )

        self.chat = self.client.chats.create(
            model="gemini-3.5-flash-lite",
            config=types.GenerateContentConfig(
                system_instruction=sys_instruction,
                tools=[consult_last_matches],
                temperature=0.2,
            ),
        )

    def send_message_stream(self, message_user: str):
        start_time = time.time()
        msg_lower = message_user.lower()

        disparadores = ["despierta", "buen dia", "buenos dias", "buen día", "buenos días"]

        if any(d in msg_lower for d in disparadores):
            hora_actual = datetime.now().strftime("%I:%M %p")
            prompt_final = f"[MODO_DESPERTAR] (Hora actual del sistema: {hora_actual}). El usuario dijo: {message_user}"
        else:
            prompt_final = message_user

        try:
            response_stream = self.chat.send_message_stream(prompt_final)

            first_chunk = True
            for chunk in response_stream:
                if first_chunk and chunk.text:
                    elapsed = time.time() - start_time
                    print(f"\n[Primer fragmento recibido en: {elapsed:.2f}s]")
                    first_chunk = False

                if chunk.text:
                    yield chunk.text

        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                yield "Límite de peticiones alcanzado temporalmente. Espera unos momentos."
            else:
                yield f"Error en JarvisBrain: {err_str}"