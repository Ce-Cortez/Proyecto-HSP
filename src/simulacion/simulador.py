from src.amplificadores.base import AmplificadorBase
from src.amplificadores.comparador import Comparador


class SimuladorCircuito:

    def __init__(self):
        self._amplificadores: list = []
        self._resultados: dict = {}

    # ------------------------------------------------------------------
    # Registro de amplificadores
    # ------------------------------------------------------------------

    def add_amplificador(self, amp: AmplificadorBase):
        if not isinstance(amp, AmplificadorBase):
            raise TypeError(f"Se esperaba AmplificadorBase, recibido: {type(amp).__name__}")
        self._amplificadores.append(amp)

    # ------------------------------------------------------------------
    # Analisis principal
    # ------------------------------------------------------------------

    def ejecutar_analisis_completo(self):
        """
        Ejecuta todos los analisis sobre cada amplificador registrado.
        Resetea _resultados en cada llamada para evitar datos obsoletos.
        Comparador omite fc, ancho_banda y bode (no aplican).
        """
        self._resultados = {}

        for amp in self._amplificadores:
            es_comparador = isinstance(amp, Comparador)

            entrada = {
                "ganancia":    amp.calcular_ganancia(),
                "ganancia_db": amp.ganancia_db() if not es_comparador else None,
                "fc":          amp.calcular_fc() if not es_comparador else None,
                "ancho_banda": amp.calcular_ancho_banda() if not es_comparador else None,
                "bode":        amp.respuesta_frecuencia() if not es_comparador else None,
            }

            self._resultados[amp.nombre] = entrada

    # ------------------------------------------------------------------
    # Consultas sobre resultados
    # ------------------------------------------------------------------

    def get_resultados(self) -> dict:
        """Retorna el dict completo de resultados indexado por nombre de amp."""
        return self._resultados

    def comparar_anchos_banda(self) -> dict:
        """
        Retorna {nombre: ancho_banda} para todos los amps excepto Comparador.
        Usado por VisualizadorResultados para la grafica comparativa.
        """
        return {
            nombre: datos["ancho_banda"]
            for nombre, datos in self._resultados.items()
            if datos["ancho_banda"] is not None
        }

    def resumen_ganancias(self) -> dict:
        """
        Retorna {nombre: (ganancia, ganancia_db)} para todos los amps.
        Comparador incluido (ganancia = inf).
        """
        return {
            nombre: (datos["ganancia"], datos["ganancia_db"])
            for nombre, datos in self._resultados.items()
        }

    # ------------------------------------------------------------------
    # Utilidad
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        if not self._resultados:
            return "SimuladorCircuito: sin resultados. Ejecutar ejecutar_analisis_completo()."

        lineas = ["=" * 55, f"  RESUMEN DE SIMULACION ({len(self._amplificadores)} configuraciones)", "=" * 55]
        for nombre, datos in self._resultados.items():
            lineas.append(f"\n  {nombre}")
            lineas.append(f"    Ganancia Av : {datos['ganancia']}")
            if datos["ganancia_db"] is not None:
                lineas.append(f"    Ganancia dB : {datos['ganancia_db']:.2f} dB")
            if datos["fc"] is not None:
                lineas.append(f"    Frec. corte : {datos['fc']:.2f} Hz")
            if datos["ancho_banda"] is not None:
                lineas.append(f"    Ancho banda : {datos['ancho_banda']:.2f} Hz")
        lineas.append("\n" + "=" * 55)
        return "\n".join(lineas)
