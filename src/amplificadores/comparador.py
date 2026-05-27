import numpy as np
from .base import AmplificadorBase


class Comparador(AmplificadorBase):
    """
    Comparador de voltaje. Salida digital rail-to-rail.
    Compara Vin contra Vref: Vout = Vcc si Vin > Vref, 0V si Vin <= Vref.
    Sin retroalimentacion (lazo abierto): Av = infinito.
    Bode y frecuencia de corte no aplican para esta configuracion.
    """

    def __init__(self, vref: float = 0.0, gbw: float = 1e6, vcc: float = 15.0):
        super().__init__("Comparador", r1=1.0, r2=0.0, gbw=gbw, vcc=vcc)
        self.__vref = float(vref)

    # ------------------------------------------------------------------
    # Property: Vref
    # ------------------------------------------------------------------

    @property
    def vref(self) -> float:
        return self.__vref

    @vref.setter
    def vref(self, valor: float):
        self.__vref = float(valor)

    # ------------------------------------------------------------------
    # Implementacion de metodos abstractos
    # ------------------------------------------------------------------

    def calcular_ganancia(self) -> float:
        """Av = infinito (lazo abierto, sin retroalimentacion)."""
        return float('inf')

    def calcular_salida(self, vin: float) -> float:
        """Vout = Vcc si Vin > Vref, 0V si Vin <= Vref (salida digital)."""
        return self.vcc if vin > self.__vref else 0.0

    # ------------------------------------------------------------------
    # Overrides: fc y Bode no aplican para comparador
    # ------------------------------------------------------------------

    def calcular_fc(self) -> float:
        raise NotImplementedError(
            "Comparador: calcular_fc() no aplica. "
            "El comparador opera en lazo abierto sin frecuencia de corte definida."
        )

    def calcular_ancho_banda(self) -> float:
        raise NotImplementedError(
            "Comparador: calcular_ancho_banda() no aplica. "
            "El comparador opera en lazo abierto sin ancho de banda definido."
        )

    def respuesta_frecuencia(self, f_min=1, f_max=1e7, n_puntos=500):
        raise NotImplementedError(
            "Comparador: respuesta_frecuencia() no aplica. "
            "El diagrama de Bode no es valido para salidas digitales."
        )

    # ------------------------------------------------------------------
    # Metodos especificos del comparador
    # ------------------------------------------------------------------

    def calcular_tiempo_respuesta(self) -> float:
        """Estimacion del retardo de propagacion: t = 1 / GBW."""
        return 1.0 / self.gbw

    def calcular_histeresis(self, delta_v: float) -> dict:
        """
        Calcula umbrales de histeresis simetricos alrededor de Vref.

        Args:
            delta_v: ventana de histeresis en voltios.

        Returns:
            dict con umbral_alto, umbral_bajo y ventana.
        """
        return {
            "umbral_alto": self.__vref + delta_v / 2,
            "umbral_bajo": self.__vref - delta_v / 2,
            "ventana":     delta_v,
        }

    def respuesta_con_ruido(self, vin: float, ruido_std: float, n_muestras: int = 1000) -> dict:
        """
        Evalua la salida del comparador con ruido gaussiano sumado a Vin.

        Args:
            vin:        voltaje de entrada nominal.
            ruido_std:  desviacion estandar del ruido en voltios.
            n_muestras: numero de muestras a evaluar.

        Returns:
            dict con prob_alto, prob_bajo y n_muestras.
        """
        muestras = np.random.normal(vin, ruido_std, n_muestras)
        salidas = np.array([self.calcular_salida(v) for v in muestras])
        n_alto = int(np.sum(salidas == self.vcc))
        return {
            "prob_alto":  n_alto / n_muestras,
            "prob_bajo":  (n_muestras - n_alto) / n_muestras,
            "n_muestras": n_muestras,
        }

    # ------------------------------------------------------------------
    # __str__ override (base llama calcular_fc que lanza error)
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return (
            f"{'='*45}\n"
            f"  {self.nombre}\n"
            f"{'='*45}\n"
            f"  Vref        : {self.__vref:>12.2f} V\n"
            f"  GBW         : {self.gbw:>12.0f} Hz\n"
            f"  Vcc         : {self.vcc:>12.1f} V\n"
            f"  Ganancia Av : {'infinita (lazo abierto)':>22}\n"
            f"  Tiempo resp.: {self.calcular_tiempo_respuesta():>12.2e} s\n"
            f"{'='*45}"
        )
