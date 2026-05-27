# SimuladorCircuito: el orquestador de la simulacion.
# Su trabajo es recibir los amplificadores configurados, correr todos los
# analisis sobre cada uno y guardar los resultados en un diccionario
# que las demas clases pueden consultar.

from src.amplificadores.base import AmplificadorBase
from src.amplificadores.comparador import Comparador


class SimuladorCircuito:
    """
    Orquesta la ejecucion de analisis sobre multiples configuraciones de op-amp.
    Funciona como contenedor: se le agregan amplificadores y luego se le pide
    que ejecute todos los calculos de una sola vez.

    Los resultados quedan guardados internamente y se acceden via getters.
    """

    def __init__(self):
        # Lista ordenada de amplificadores — el orden de insercion es el orden de analisis
        self._amplificadores: list = []
        # Diccionario de resultados: clave = nombre del amp, valor = dict con todos los datos
        self._resultados: dict = {}

    def add_amplificador(self, amp: AmplificadorBase):
        """
        Registra un amplificador en el simulador.
        Valida que el objeto sea realmente un amplificador antes de agregarlo.

        Args:
            amp: instancia de cualquier subclase de AmplificadorBase
        """
        if not isinstance(amp, AmplificadorBase):
            raise TypeError(f"Se esperaba AmplificadorBase, recibido: {type(amp).__name__}")
        self._amplificadores.append(amp)

    def ejecutar_analisis_completo(self):
        """
        Recorre todos los amplificadores registrados y ejecuta el conjunto
        completo de analisis: ganancia, fc, ancho de banda y datos de Bode.

        El Comparador es un caso especial — no tiene fc ni Bode, entonces
        esos campos quedan como None en lugar de lanzar un error.

        Limpia los resultados previos en cada llamada para evitar que
        datos viejos se mezclen con los nuevos.
        """
        # Limpiamos resultados anteriores antes de correr
        self._resultados = {}

        for amp in self._amplificadores:
            # Detectamos el Comparador para saltarnos los calculos que no aplican
            es_comparador = isinstance(amp, Comparador)

            entrada = {
                "ganancia":    amp.calcular_ganancia(),
                # Para el Comparador ganancia_db y lo demas son None — no tienen sentido
                "ganancia_db": amp.ganancia_db() if not es_comparador else None,
                "fc":          amp.calcular_fc() if not es_comparador else None,
                "ancho_banda": amp.calcular_ancho_banda() if not es_comparador else None,
                "bode":        amp.respuesta_frecuencia() if not es_comparador else None,
            }

            # Usamos el nombre del amp como clave para facil acceso despues
            self._resultados[amp.nombre] = entrada

    def get_resultados(self) -> dict:
        """
        Retorna el diccionario completo de resultados.
        Estructura: {nombre_amp: {ganancia, ganancia_db, fc, ancho_banda, bode}}
        """
        return self._resultados

    def comparar_anchos_banda(self) -> dict:
        """
        Extrae solo los anchos de banda para comparacion entre configuraciones.
        Filtra el Comparador automaticamente porque su ancho_banda es None.

        Retorna:
            {nombre_amp: ancho_banda_hz} para todos los amps excepto el Comparador
        """
        return {
            nombre: datos["ancho_banda"]
            for nombre, datos in self._resultados.items()
            if datos["ancho_banda"] is not None
        }

    def resumen_ganancias(self) -> dict:
        """
        Extrae las ganancias de todos los amplificadores, incluyendo el Comparador.
        Util para imprimir una tabla comparativa rapida.

        Retorna:
            {nombre_amp: (ganancia_lineal, ganancia_db)}
        """
        return {
            nombre: (datos["ganancia"], datos["ganancia_db"])
            for nombre, datos in self._resultados.items()
        }

    def __str__(self) -> str:
        # Si no se ha corrido el analisis todavia, avisamos
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
