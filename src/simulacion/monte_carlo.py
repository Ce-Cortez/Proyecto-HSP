# Analizador de Monte Carlo: simula el efecto de las tolerancias reales
# de los componentes sobre la ganancia del circuito.
#
# La idea es: en la realidad, una resistencia de 1k ohm con tolerancia +-5%
# puede ser cualquier valor entre 950 y 1050 ohms. Si hacemos eso con miles
# de pares (R1, R2) aleatorios y calculamos la ganancia para cada par,
# obtenemos la distribucion estadistica de ganancia real del circuito.

import numpy as np
from src.amplificadores.base import AmplificadorBase
from src.amplificadores.inversor import AmpInversor
from src.amplificadores.no_inversor import AmpNoInversor
from src.amplificadores.seguidor import SeguidorVoltaje
from src.amplificadores.comparador import Comparador


class AnalizadorMonteCarlo:
    """
    Evalua la sensibilidad de la ganancia ante variaciones en R1 y R2.
    Las variaciones siguen una distribucion Normal (gaussiana), que modela
    bien la variabilidad real de manufactura de resistencias.

    Args:
        n_muestras: cuantos pares (R1, R2) aleatorios generar por corrida (default 1000)
    """

    def __init__(self, n_muestras: int = 1000):
        self._n_muestras = n_muestras
        # Guardamos resultados de todas las corridas para acceso posterior
        self._resultados_mc: dict = {}

    def _calcular_ganancias_vectorizado(
        self, amp: AmplificadorBase, r1_arr: np.ndarray, r2_arr: np.ndarray
    ) -> np.ndarray:
        """
        Calcula la ganancia para N pares (R1, R2) de una sola vez usando numpy.
        Esto es mucho mas rapido que crear 1000 objetos amplificador.
        Aplica la formula de la subclase directamente sobre los arrays.

        Args:
            amp    : amplificador de referencia (para saber que formula usar)
            r1_arr : array de N valores de R1 con variacion aleatoria
            r2_arr : array de N valores de R2 con variacion aleatoria

        Retorna:
            array de N valores de ganancia
        """
        if isinstance(amp, AmpInversor):
            # Av = -R2 / R1 aplicado elemento a elemento
            return -r2_arr / r1_arr
        elif isinstance(amp, AmpNoInversor):
            # Av = 1 + R2 / R1 aplicado elemento a elemento
            return 1 + r2_arr / r1_arr
        elif isinstance(amp, SeguidorVoltaje):
            # La ganancia del seguidor siempre es 1, sin importar R1 o R2
            # Confirmamos que las tolerancias en R1/R2 no afectan la ganancia
            return np.ones(len(r1_arr))
        else:
            raise ValueError(
                f"AnalizadorMonteCarlo: formula no definida para {type(amp).__name__}."
            )

    def ejecutar(self, amp: AmplificadorBase, tolerancias: list = None) -> dict:
        """
        Corre el analisis de Monte Carlo para un amplificador dado.
        Genera N pares (R1, R2) con distribucion Normal para cada nivel
        de tolerancia y calcula la ganancia resultante en cada caso.

        La probabilidad de fallo se calcula contra los limites de la
        tolerancia del 1% (la mas estricta) usada como especificacion de referencia.
        Si a mayor tolerancia mas muestras caen fuera de ese rango, P(fallo) sube.

        Args:
            amp         : amplificador a analizar (el Comparador no esta permitido)
            tolerancias : lista de tolerancias en fraccion, ej. [0.01, 0.05, 0.10]

        Retorna:
            dict indexado por tolerancia, cada entrada tiene:
            ganancias, media, std, prob_fallo
        """
        # El Comparador tiene ganancia infinita — Monte Carlo no tiene sentido ahi
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
            # Distribucion Normal: media = valor nominal, std = nominal * tolerancia
            r1_samples = np.random.normal(amp.r1, amp.r1 * tol, n)

            # R2 = 0 en SeguidorVoltaje — variacion de 0 da siempre cero, lo manejamos aparte
            r2_samples = (
                np.random.normal(amp.r2, amp.r2 * tol, n)
                if amp.r2 > 0
                else np.zeros(n)
            )

            # Calculamos ganancia para los N pares sin crear nuevos objetos
            ganancias = self._calcular_ganancias_vectorizado(amp, r1_samples, r2_samples)

            resultados_por_tol[tol] = {
                "ganancias":  ganancias,
                "media":      float(np.mean(ganancias)),
                "std":        float(np.std(ganancias)),
                "prob_fallo": None,  # se calcula en el paso 2
            }

        # --- Paso 2: calcular prob_fallo usando std al 1% como referencia ---
        # La idea: los limites de aceptacion los define la tolerancia mas fina (1%).
        # Todo lo que caiga fuera de media_1% +/- 3*std_1% se considera fallo.
        tol_base   = tolerancias[0]
        media_ref  = resultados_por_tol[tol_base]["media"]
        std_ref    = resultados_por_tol[tol_base]["std"]
        limite_inf = media_ref - 3 * std_ref
        limite_sup = media_ref + 3 * std_ref

        for tol in tolerancias:
            g = resultados_por_tol[tol]["ganancias"]
            # Contamos muestras que caen fuera del rango aceptable
            n_fuera = int(np.sum((g < limite_inf) | (g > limite_sup)))
            resultados_por_tol[tol]["prob_fallo"] = n_fuera / n

        # Guardamos resultados indexados por nombre del amplificador
        self._resultados_mc[amp.nombre] = resultados_por_tol
        return resultados_por_tol

    def curva_convergencia(
        self,
        amp: AmplificadorBase,
        tolerancia: float = 0.05,
        max_muestras: int = 1000,
    ) -> dict:
        """
        Muestra como la media y la sigma se estabilizan al aumentar N muestras.
        Con pocas muestras los valores saltan mucho — con muchas se estabilizan.
        Eso nos dice cuantas muestras son suficientes para confiar en los resultados.

        Generamos el pool completo de una sola vez y tomamos subconjuntos crecientes
        para ser eficientes — una sola llamada a numpy.random en lugar de N.

        Args:
            amp          : amplificador de referencia
            tolerancia   : nivel de tolerancia a usar para la variacion (fraccion)
            max_muestras : numero maximo de muestras en el eje X

        Retorna:
            dict con listas: n_muestras, medias, sigmas
        """
        # Puntos tipicos de la curva de convergencia
        conteos_base = [10, 20, 50, 100, 200, 500, 1000]
        # Agregamos max_muestras si no esta ya en la lista
        conteos = sorted(set(
            [c for c in conteos_base if c <= max_muestras] + [max_muestras]
        ))

        # Generamos todo el pool de una vez — mucho mas eficiente
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
            # Tomamos los primeros n elementos del pool completo
            subset = ganancias_full[:n]
            medias.append(float(np.mean(subset)))
            sigmas.append(float(np.std(subset)))

        return {
            "n_muestras": conteos,
            "medias":     medias,
            "sigmas":     sigmas,
        }

    def get_resultados(self) -> dict:
        """
        Retorna todos los resultados MC acumulados desde que se creo el objeto.
        Estructura: {nombre_amp: {tolerancia: {ganancias, media, std, prob_fallo}}}
        """
        return self._resultados_mc
