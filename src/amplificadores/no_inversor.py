# Amplificador No Inversor: amplifica la senal sin cambiar su fase.
# La ganancia minima es 1 (cuando R2=0), a diferencia del inversor que puede
# tener ganancia menor a 1 si R2 < R1.

import numpy as np
from .base import AmplificadorBase


class AmpNoInversor(AmplificadorBase):
    """
    Implementa la configuracion no inversora del op-amp.
    La senal de entrada va directo al terminal positivo del op-amp,
    por eso conserva la fase y la ganancia siempre es >= 1.

    Args:
        r1  : resistencia conectada a tierra en ohms
        r2  : resistencia de retroalimentacion en ohms
        gbw : producto ganancia-ancho de banda del op-amp (default 1 MHz)
        vcc : voltaje de alimentacion (default 15 V)
    """

    def __init__(self, r1: float, r2: float, gbw: float = 1e6, vcc: float = 15.0):
        super().__init__("Amplificador No Inversor", r1=r1, r2=r2, gbw=gbw, vcc=vcc)

    def calcular_ganancia(self) -> float:
        """
        Calcula la ganancia de voltaje del amplificador no inversor.
        El "+1" viene del hecho de que la senal de entrada ya esta en la salida
        mas la parte amplificada por la red de retroalimentacion.
        Formula: Av = 1 + R2 / R1
        """
        return 1 + self.r2 / self.r1

    def calcular_salida(self, vin: float) -> float:
        """
        Calcula el voltaje de salida para una entrada vin.
        Igual que el inversor, recortamos si el resultado supera la alimentacion.

        Args:
            vin: voltaje de entrada en voltios

        Retorna:
            voltaje de salida en voltios, acotado a [-Vcc, +Vcc]
        """
        vout = self.calcular_ganancia() * vin
        return float(np.clip(vout, -self.vcc, self.vcc))
