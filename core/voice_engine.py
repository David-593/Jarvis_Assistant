import sys
try:
    import pyaudiowpatch as pyaudio
    sys.modules['pyaudio'] = pyaudio
except ImportError:
    pass

import asyncio
import os
import edge_tts
from playsound import playsound
import speech_recognition as sr


class VoiceEngineHD:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Ajustes de sensibilidad
        self.recognizer.pause_threshold = 0.8
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 300
        
        # Configuración de voz
        self.voice = "es-MX-JorgeNeural"
        self.rate = "+13%"
        self.pitch = "-1Hz"

    def escuchar(self) -> str:
        """Escucha continua de audio desde el micrófono."""
        with sr.Microphone() as source:
            try:
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=15)
                texto = self.recognizer.recognize_google(audio, language="es-ES").strip()
                return texto
            except (sr.WaitTimeoutError, sr.UnknownValueError):
                return ""
            except Exception:
                return ""

    def hablar(self, texto: str):
        """Genera y reproduce el texto completo de forma fluida y continua."""
        if not texto.strip():
            return
        asyncio.run(self._generar_y_reproducir(texto))

    async def _generar_y_reproducir(self, texto: str):
        archivo_temp = "temp_voice.mp3"
        
        communicate = edge_tts.Communicate(
            text=texto,
            voice=self.voice,
            rate=self.rate,
            pitch=self.pitch
        )
        await communicate.save(archivo_temp)

        try:
            playsound(archivo_temp)
        finally:
            if os.path.exists(archivo_temp):
                os.remove(archivo_temp)

    def hablar_stream(self, text_stream):
        """Acumula todo el texto del stream de Gemini para reproducirlo de una sola vez."""
        texto_completo = ""
        for chunk in text_stream:
            texto_completo += chunk
        
        if texto_completo.strip():
            self.hablar(texto_completo.strip())