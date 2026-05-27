import numpy as np
from src.amplificadores.base import AmplificadorBase
from src.amplificadores.inversor import AmpInversor
from src.amplificadores.no_inversor import AmpNoInversor
from src.amplificadores.seguidor import SeguidorVoltaje
from src.amplificadores.comparador import Comparador


class AnalizadorMonteCarlo:

    def __init__(self, n_muestras: int = 1000):
        self._n_muestras = n_muestras
        self._resultados_mc: dict = {}

    # ------------------------------------------------------------------
    # Helper privado: calculo vectorizado de ganancia
    # ------------------------------------------------------------------

    def _calcular_ganancias_vectorizado(
        self, amp: AmplificadorBase, r1_arr: np.ndarray, r2_arr: np.ndarray
    ) -> np.ndarray:
        """
        Calcula el array de ganancias para N pares (R1, R2) sin instanciar objetos.
        Aplica la formula de cada subclase directamente sobre arrays numpy.
        """
        if isinstance(amp, AmpInversor):
            return -r2_arr / r1_arr
        elif isinstance(amp, AmpNoInversor):
            return 1 + r2_arr / r1_arr
        elif isinstance(amp, SeguidorVoltaje):
            # Av = 1 siempre; independiente de R1/R2
            return np.ones(len(r1_arr))
        else:
            raise ValueError(
                f"AnalizadorMonteCarlo: formula no definida para {type(amp).__name__}."
            )

    # ------------------------------------------------------------------
    # Analisis Monte Carlo
    # ------------------------------------------------------------------

    def ejecutar(self, amp: AmplificadorBase, tolerancias: list = None) -> dict:
        """
        Evalua la distribucion de ganancia bajo variacion aleatoria de R1 y R2.

        Para cada nivel de tolerancia:
          - Genera n_muestras pares (R1, R2) con distribucion Normal
          - Calcula la ganancia para cada par (formula inline, sin nuevos objetos)
          - Computa media, std y prob_fallo

        prob_fallo: fraccion de muestras fuera de [media_1% +/- 3*std_1%].
        La tolerancia del 1% actua como limite de especificacion de referencia.

        Args:
            amp:        amplificador a analizar (no Comparador).
            tolerancias: lista de tolerancias en fraccion (ej. [0.01, 0.05, 0.10]).

        Returns:
            dict indexado por tolerancia con ganancias, media, std y prob_fallo.
        """
        if isinstance(amp, Comparador):
            raise ValueError(
                "AnalizadorMonteCarlo: Comparador no soportado (Av = infinito, MC no aplica)."
            )

        if tolerancias is None:
            tolerancias = [0.01, 0.05, 0.10]

        n = self._n_muestras
        resultados_por_tol = {}

        # --- Paso 1: generar muestras y calcular estadisticas por tolerancia ---
        for tol in tolerancias:
            r1_samples = np.random.normal(amp.r1, amp.r1 * tol, n)
            # R2 = 0 en SeguidorVoltaje: variacion nula (std = 0)
            r2_samples = (
                np.random.normal(amp.r2, amp.r2 * tol, n)
                if amp.r2 > 0
                else np.zeros(n)
            )
            ganancias = self._calcular_ganancias_vectorizado(amp, r1_samples, r2_samples)

            resultados_por_tol[tol] = {
                "ganancias": ganancias,
                "media":     float(np.mean(ganancias)),
                "std":       float(np.std(ganancias)),
                "prob_fallo": None,  # calculado en paso 2
            }

        # --- Paso 2: calcular prob_fallo usando std al 1% como spec de referencia ---
        tol_base = tolerancias[0]
        media_ref = resultados_por_tol[tol_base]["media"]
        std_ref   = resultados_por_tol[tol_base]["std"]
        limite_inf = media_ref - 3 * std_ref
        limite_sup = media_ref + 3 * std_ref

        for tol in tolerancias:
            g = resultados_por_tol[tol]["ganancias"]
            n_fuera = int(np.sum((g < limite_inf) | (g > limite_sup)))
            resultados_por_tol[tol]["prob_fallo"] = n_fuera / n

        self._resultados_mc[amp.nombre] = resultados_por_tol
        return resultados_por_tol

    # ------------------------------------------------------------------
    # Curva de convergencia
    # ------------------------------------------------------------------

    def curva_convergencia(
        self,
        amp: AmplificadorBase,
        tolerancia: float = 0.05,
        max_muestras: int = 1000,
    ) -> dict:
        """
        Muestra como convergen la media y sigma al aumentar el numero de muestras.

        Genera un pool completo de max_muestras una sola vez y toma subconjuntos
        crecientes [:n] para cada punto de la curva. Eficiente: una sola llamada
        a numpy.random.

        Args:
            amp:          amplificador de referencia.
            tolerancia:   nivel de tolerancia para la variacion (fraccion).
            max_muestras: techo del eje X de la curva.

        Returns:
            dict con listas n_muestras, medias y sigmas.
        """
        conteos_base = [10, 20, 50, 100, 200, 500, 1000]
        conteos = sorted(set(
            [c for c in conteos_base if c <= max_muestras] + [max_muestras]
        ))

        # Generar pool completo una sola vez
        r1_full = np.random.normal(amp.r1, amp.r1 * tolerancia, max_muestras)
        r2_full = (
            np.random.normal(amp.r2, amp.r2 * tolerancia, max_muestras)
            if amp.r2 > 0
            else np.zeros(max_muestras)
        )
        ganancias_full = self._calcular_ganancias_vectorizado(amp, r1_full, r2_full)

        medias = []
        sigmas = []

        for n in conteos:
            subset = ganancias_full[:n]
            medias.append(float(np.mean(subset)))
            sigmas.append(float(np.std(subset)))

        return {
            "n_muestras": conteos,
            "medias":     medias,
            "sigmas":     sigmas,
        }

    # ------------------------------------------------------------------
    # Getter
    # ------------------------------------------------------------------

    def get_resultados(self) -> dict:
        """Retorna todos los resultados MC almacenados, indexados por nombre de amp."""
        return self._resultados_mc
