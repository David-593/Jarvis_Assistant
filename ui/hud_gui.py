import sys
import math
import random
from dataclasses import dataclass
from typing import List, Tuple

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QRadialGradient, QLinearGradient,
    QFont, QPainterPath,
)
from PySide6.QtWidgets import QWidget, QApplication, QMainWindow

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ----------------------------------------------------------------------
# Paleta de colores
# ----------------------------------------------------------------------
COL_CYAN = QColor(60, 235, 255)
COL_CYAN_DIM = QColor(20, 120, 140)
COL_AMBER = QColor(255, 170, 40)
COL_RED = QColor(255, 60, 60)
COL_TEXT = QColor(190, 245, 255)


@dataclass
class CircuitNode:
    x: float
    y: float
    r: float = 3.0
    pulse_phase: float = 0.0


@dataclass
class CircuitTrace:
    points: List[Tuple[float, float]]


class StarkHUDWidget(QWidget):
    """
    Widget de HUD estilo Iron Man / Stark Industries.

    Dibuja anillos concéntricos animados, trazados de circuitos con glow,
    nodos pulsantes, un núcleo central con estado del sistema y dos gauges
    circulares de telemetría (CPU / RAM). Si `psutil` está instalado, la
    telemetría refleja el uso real del sistema; en caso contrario, se
    simula con una caminata aleatoria suavizada.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 640)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        # --- Estado de animación ---
        self._angle_outer = 0.0
        self._angle_mid = 0.0
        self._angle_inner = 0.0
        self._scan_angle = 0.0
        self._pulse_t = 0.0

        # --- Telemetría (valores suavizados y objetivos) ---
        self.cpu_value = 0.0
        self.ram_value = 0.0
        self._cpu_target = 30.0
        self._ram_target = 45.0

        # --- Circuitos procedurales (generados una vez por tamaño) ---
        self._rng = random.Random(42)
        self._traces: List[CircuitTrace] = []
        self._nodes: List[CircuitNode] = []
        self._traces_dirty = True

        # --- Timers ---
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_animate)
        self._anim_timer.start(33)  # ~30 FPS

        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self._on_update_telemetry)
        self._data_timer.start(800)
        self._on_update_telemetry()

    # ------------------------------------------------------------------
    # Actualización de datos
    # ------------------------------------------------------------------
    def _on_update_telemetry(self):
        if HAS_PSUTIL:
            self._cpu_target = psutil.cpu_percent(interval=None)
            self._ram_target = psutil.virtual_memory().percent
        else:
            self._cpu_target = max(5, min(95, self._cpu_target + self._rng.uniform(-12, 12)))
            self._ram_target = max(5, min(95, self._ram_target + self._rng.uniform(-6, 6)))

    def _on_animate(self):
        self._angle_outer = (self._angle_outer + 0.25) % 360
        self._angle_mid = (self._angle_mid - 0.45) % 360
        self._angle_inner = (self._angle_inner + 0.9) % 360
        self._scan_angle = (self._scan_angle + 1.6) % 360
        self._pulse_t += 0.05

        # Interpolación suave (easing) hacia el valor objetivo
        self.cpu_value += (self._cpu_target - self.cpu_value) * 0.06
        self.ram_value += (self._ram_target - self.ram_value) * 0.06

        self.update()

    def resizeEvent(self, event):
        self._traces_dirty = True
        super().resizeEvent(event)

    # ------------------------------------------------------------------
    # Generación procedural de trazados de circuitos
    # ------------------------------------------------------------------
    def _build_circuits(self, cx, cy, r_min, r_max):
        self._traces.clear()
        self._nodes.clear()
        n_traces = 14
        for i in range(n_traces):
            base_angle = (360 / n_traces) * i + self._rng.uniform(-6, 6)
            rad = math.radians(base_angle)
            r0 = r_min + self._rng.uniform(0, 10)
            x0 = cx + r0 * math.cos(rad)
            y0 = cy + r0 * math.sin(rad)
            points: List[Tuple[float, float]] = [(x0, y0)]

            r = r0
            ang = base_angle
            segments = self._rng.randint(2, 4)
            for _ in range(segments):
                r += self._rng.uniform(18, 42)
                ang += self._rng.uniform(-18, 18)
                rad2 = math.radians(ang)
                x = cx + r * math.cos(rad2)
                y = cy + r * math.sin(rad2)
                # Giro tipo "circuito impreso" (quiebre horizontal/vertical)
                if self._rng.random() > 0.5:
                    mid = (points[-1][0], y)
                else:
                    mid = (x, points[-1][1])
                points.append(mid)
                points.append((x, y))
                if r > r_max:
                    break

            self._traces.append(CircuitTrace(points=points))
            for (px, py) in points[1::2]:
                self._nodes.append(
                    CircuitNode(px, py, r=self._rng.uniform(2, 4),
                                pulse_phase=self._rng.uniform(0, 6.28))
                )
        self._traces_dirty = False

    # ------------------------------------------------------------------
    # Helpers de dibujo "glow" (neón aditivo)
    # ------------------------------------------------------------------
    def _draw_glow_line(self, painter, p1: QPointF, p2: QPointF, color: QColor, width=1.4):
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        for i in range(4, 0, -1):
            c = QColor(color)
            c.setAlpha(int(28 * i))
            painter.setPen(QPen(c, width + i * 1.6, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(p1, p2)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(p1, p2)

    def _draw_glow_path(self, painter, path: QPainterPath, color: QColor, width=1.4):
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        for i in range(4, 0, -1):
            c = QColor(color)
            c.setAlpha(int(26 * i))
            painter.setPen(QPen(c, width + i * 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawPath(path)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(path)

    def _draw_glow_circle(self, painter, center: QPointF, radius: float, color: QColor,
                           width=1.4, filled=False):
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        for i in range(4, 0, -1):
            c = QColor(color)
            c.setAlpha(int(26 * i))
            painter.setPen(QPen(c, width + i * 1.6))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center, radius, radius)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setPen(QPen(color, width))
        painter.setBrush(QBrush(color) if filled else Qt.NoBrush)
        painter.drawEllipse(center, radius, radius)

    def _draw_glow_arc(self, painter, rect: QRectF, start_angle: float, span_angle: float,
                        color: QColor, width=6):
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        for i in range(4, 0, -1):
            c = QColor(color)
            c.setAlpha(int(22 * i))
            painter.setPen(QPen(c, width + i * 2.2, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(rect, int(start_angle * 16), int(span_angle * 16))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setPen(QPen(color, width, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(rect, int(start_angle * 16), int(span_angle * 16))

    # ------------------------------------------------------------------
    # Paint principal
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        base_r = min(w, h) * 0.42

        self._paint_background(painter, w, h, cx, cy)

        if self._traces_dirty:
            self._build_circuits(cx, cy, base_r * 0.55, base_r * 1.05)

        self._paint_circuits(painter)
        self._paint_rings(painter, cx, cy, base_r)
        self._paint_scan_sweep(painter, cx, cy, base_r)
        self._paint_center_core(painter, cx, cy, base_r)
        self._paint_gauge(painter, cx - base_r * 1.55, cy, base_r * 0.5,
                           self.cpu_value, "CPU", COL_CYAN)
        self._paint_gauge(painter, cx + base_r * 1.55, cy, base_r * 0.5,
                           self.ram_value, "RAM", COL_AMBER)
        self._paint_header_footer(painter, w, h)

        painter.end()

    # ------------------------------------------------------------------
    def _paint_background(self, painter, w, h, cx, cy):
        grad = QRadialGradient(cx, cy, max(w, h) * 0.75)
        grad.setColorAt(0.0, QColor(6, 16, 20))
        grad.setColorAt(0.55, QColor(3, 9, 12))
        grad.setColorAt(1.0, QColor(0, 0, 0))
        painter.fillRect(self.rect(), QBrush(grad))

        # Grid sutil de fondo
        painter.setPen(QPen(QColor(0, 100, 120, 18), 1))
        step = 28
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)

    def _paint_circuits(self, painter):
        for trace in self._traces:
            path = QPainterPath()
            path.moveTo(*trace.points[0])
            for pt in trace.points[1:]:
                path.lineTo(*pt)
            self._draw_glow_path(painter, path, COL_CYAN_DIM, width=1.2)

        for node in self._nodes:
            pulse = 0.5 + 0.5 * math.sin(self._pulse_t * 2 + node.pulse_phase)
            color = QColor(COL_CYAN)
            color.setAlpha(int(120 + 135 * pulse))
            self._draw_glow_circle(painter, QPointF(node.x, node.y),
                                    node.r * (0.8 + 0.4 * pulse), color,
                                    width=1.0, filled=True)

    def _paint_rings(self, painter, cx, cy, base_r):
        center = QPointF(cx, cy)

        # Anillo exterior segmentado (marcas tipo radar)
        self._paint_tick_ring(painter, center, base_r * 1.32, self._angle_outer,
                               n_ticks=72, tick_len=10, color=COL_CYAN_DIM, active_ratio=0.7)

        # Anillo medio con arcos discontinuos (rotación lenta inversa)
        self._paint_dashed_ring(painter, center, base_r * 1.12, self._angle_mid,
                                 n_dashes=24, gap_ratio=0.4, color=COL_CYAN, width=2.2)

        # Anillo interno con marcas finas
        self._paint_tick_ring(painter, center, base_r * 0.95, -self._angle_inner * 0.6,
                               n_ticks=48, tick_len=6, color=COL_CYAN_DIM, active_ratio=1.0)

        # Anillo interno rotando rápido
        self._paint_dashed_ring(painter, center, base_r * 0.78, self._angle_inner,
                                 n_dashes=40, gap_ratio=0.55, color=COL_CYAN, width=1.4)

    def _paint_tick_ring(self, painter, center: QPointF, radius, rot_offset,
                          n_ticks, tick_len, color, active_ratio=1.0):
        for i in range(n_ticks):
            if self._tick_active(i, active_ratio):
                ang = math.radians((360 / n_ticks) * i + rot_offset)
                x1 = center.x() + radius * math.cos(ang)
                y1 = center.y() + radius * math.sin(ang)
                x2 = center.x() + (radius - tick_len) * math.cos(ang)
                y2 = center.y() + (radius - tick_len) * math.sin(ang)
                self._draw_glow_line(painter, QPointF(x1, y1), QPointF(x2, y2),
                                      color, width=1.3)

    @staticmethod
    def _tick_active(i, ratio):
        # Determinístico: activa ~ratio de las marcas con patrón estable por índice
        return (i * 2654435761) % 1000 < ratio * 1000

    def _paint_dashed_ring(self, painter, center: QPointF, radius, rot_offset,
                            n_dashes, gap_ratio, color, width):
        span = (360 / n_dashes) * (1 - gap_ratio)
        rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        for i in range(n_dashes):
            start = (360 / n_dashes) * i + rot_offset
            self._draw_glow_arc(painter, rect, start, span, color, width=width)

    def _paint_scan_sweep(self, painter, cx, cy, base_r):
        painter.setCompositionMode(QPainter.CompositionMode_Plus)
        r = base_r * 1.32
        span = 26
        ang = math.radians(self._scan_angle)
        x2 = cx + r * math.cos(ang)
        y2 = cy + r * math.sin(ang)

        path = QPainterPath()
        path.moveTo(cx, cy)
        path.lineTo(x2, y2)
        path.arcTo(QRectF(cx - r, cy - r, r * 2, r * 2), -self._scan_angle, -span)
        path.lineTo(cx, cy)

        c = QColor(COL_CYAN)
        c.setAlpha(18)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(c))
        painter.drawPath(path)
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    def _paint_center_core(self, painter, cx, cy, base_r):
        center = QPointF(cx, cy)
        pulse = 0.5 + 0.5 * math.sin(self._pulse_t * 1.4)

        # Núcleo con gradiente radial
        core_r = base_r * 0.42
        grad = QRadialGradient(center, core_r)
        c1 = QColor(COL_CYAN)
        c1.setAlpha(60 + int(40 * pulse))
        grad.setColorAt(0.0, c1)
        grad.setColorAt(0.6, QColor(10, 40, 48, 40))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(center, core_r, core_r)

        self._draw_glow_circle(painter, center, base_r * 0.30, COL_CYAN, width=1.6)
        self._draw_glow_circle(painter, center, base_r * 0.24, COL_CYAN_DIM, width=1.0)

        # Estado del sistema (texto central)
        avg = (self.cpu_value + self.ram_value) / 2
        status = "OPTIMAL" if avg < 60 else ("ELEVATED" if avg < 85 else "CRITICAL")
        status_color = COL_CYAN if avg < 60 else (COL_AMBER if avg < 85 else COL_RED)

        font = QFont("Consolas", max(9, int(base_r * 0.055)))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(status_color))
        rect_text = QRectF(cx - base_r * 0.3, cy - base_r * 0.08, base_r * 0.6, base_r * 0.16)
        painter.drawText(rect_text, Qt.AlignCenter, status)

        small_font = QFont("Consolas", max(7, int(base_r * 0.03)))
        painter.setFont(small_font)
        painter.setPen(QPen(COL_CYAN_DIM))
        rect_sub = QRectF(cx - base_r * 0.35, cy + base_r * 0.06, base_r * 0.7, base_r * 0.1)
        painter.drawText(rect_sub, Qt.AlignCenter, "J.A.R.V.I.S. CORE LINK")

    # ------------------------------------------------------------------
    def _paint_gauge(self, painter, cx, cy, radius, value, label, color: QColor):
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)

        # Anillo base tenue
        painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 35),
                             radius * 0.16, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(rect, 90 * 16, -360 * 16)

        # Arco de progreso con glow
        span = -360 * (value / 100.0)
        self._draw_glow_arc(painter, rect, 90, span, color, width=radius * 0.16)

        # Marcas de graduación alrededor del gauge
        for i in range(20):
            ang = math.radians(90 + i * 18)
            r1 = radius * 1.12
            r2 = radius * 1.2
            x1 = cx + r1 * math.cos(ang)
            y1 = cy - r1 * math.sin(ang)
            x2 = cx + r2 * math.cos(ang)
            y2 = cy - r2 * math.sin(ang)
            active = i <= (value / 100.0) * 20
            c = QColor(color) if active else QColor(color.red(), color.green(), color.blue(), 40)
            painter.setPen(QPen(c, 1.4))
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        # Texto central del gauge
        font = QFont("Consolas", max(10, int(radius * 0.32)))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(COL_TEXT))
        val_rect = QRectF(cx - radius, cy - radius * 0.25, radius * 2, radius * 0.5)
        painter.drawText(val_rect, Qt.AlignCenter, f"{value:0.0f}%")

        label_font = QFont("Consolas", max(8, int(radius * 0.16)))
        painter.setFont(label_font)
        painter.setPen(QPen(color))
        label_rect = QRectF(cx - radius, cy + radius * 0.2, radius * 2, radius * 0.3)
        painter.drawText(label_rect, Qt.AlignCenter, label)

    # ------------------------------------------------------------------
    def _paint_header_footer(self, painter, w, h):
        font = QFont("Consolas", 10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(COL_CYAN))
        painter.drawText(QRectF(20, 14, w - 40, 24), Qt.AlignLeft | Qt.AlignVCenter,
                          "STARK INDUSTRIES // SYSTEM TELEMETRY")

        small_font = QFont("Consolas", 8)
        painter.setFont(small_font)
        painter.setPen(QPen(COL_CYAN_DIM))
        left_text = "MARK LVII // LIVE HOST TELEMETRY" if HAS_PSUTIL else \
            "MARK LVII // SIMULATED TELEMETRY"
        painter.drawText(QRectF(20, h - 30, w - 40, 20), Qt.AlignLeft | Qt.AlignVCenter,
                          left_text)
        painter.drawText(QRectF(20, h - 30, w - 40, 20), Qt.AlignRight | Qt.AlignVCenter,
                          f"CPU {self.cpu_value:0.1f}%   RAM {self.ram_value:0.1f}%")


class StarkHUDWindow(QMainWindow):
    """Ventana de demostración lista para ejecutar de forma independiente."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("STARK HUD - Telemetry Dashboard")
        self.resize(900, 900)
        self.setStyleSheet("background-color: black;")
        self.hud = StarkHUDWidget(self)
        self.setCentralWidget(self.hud)


def main():
    app = QApplication(sys.argv)
    window = StarkHUDWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()