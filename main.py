import sys
import threading
import re
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication, QMainWindow

from ui.hud_gui import StarkHUDWidget
from core.llm_engine import JarvisBrain
from core.voice_engine import VoiceEngineHD as VoiceEngine


class VoiceWorker(QObject):
    """Maneja las señales para comunicarse de forma segura con el hilo principal de Qt."""
    close_app_signal = Signal()


def voice_loop(worker, jarvis, voice):
    while True:
        try:
            text_raw = voice.escuchar()
            if not text_raw:
                continue

            text_clean = re.sub(r'[^\w\s]', '', text_raw.lower()).strip()

            if "jarvis" not in text_clean:
                continue

            palabras_salida = ["salir", "exit", "cerrar", "chao", "descansa"]
            if any(palabra in text_clean for palabra in palabras_salida):
                print("\n[Jarvis]: Cerrando sesión...")
                voice.hablar("Cerrando sesión. Hasta luego, Andrés.")
                worker.close_app_signal.emit()
                break

            # Generación por Streaming para reducir la latencia al mínimo
            stream_respuesta = jarvis.send_message_stream(text_raw)
            voice.hablar_stream(stream_respuesta)

        except Exception as e:
            print(f"[Error en el hilo de voz]: {e}")


def main():
    print("==========================================")
    print("   JARVIS OS // STARK INDUSTRIES HUD      ")
    print("        (Escuchando comandos...)          ")
    print("==========================================")

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("JARVIS OS // STARK INDUSTRIES HUD")
    window.resize(900, 900)

    hud_widget = StarkHUDWidget(window)
    window.setCentralWidget(hud_widget)
    window.show()

    jarvis = JarvisBrain()
    voice = VoiceEngine()

    worker = VoiceWorker()
    worker.close_app_signal.connect(app.quit)

    thread = threading.Thread(target=voice_loop, args=(worker, jarvis, voice), daemon=True)
    thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()