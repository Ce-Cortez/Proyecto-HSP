import numpy as np
from .base import AmplificadorBase


class AmpInversor(AmplificadorBase):

    def __init__(self, r1: float, r2: float, gbw: float = 1e6, vcc: float = 15.0):
        super().__init__("Amplificador Inversor", r1=r1, r2=r2, gbw=gbw, vcc=vcc)

    def calcular_ganancia(self) -> float:
        """Av = -R2 / R1  (negativo: invierte fase de la senal)."""
        return -self.r2 / self.r1

    def calcular_salida(self, vin: float) -> float:
        """Vout = Av * Vin, limitado al rango [-Vcc, +Vcc]."""
        vout = self.calcular_ganancia() * vin
        return float(np.clip(vout, -self.vcc, self.vcc))
