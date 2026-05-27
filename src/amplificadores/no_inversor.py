import numpy as np
from .base import AmplificadorBase


class AmpNoInversor(AmplificadorBase):

    def __init__(self, r1: float, r2: float, gbw: float = 1e6, vcc: float = 15.0):
        super().__init__("Amplificador No Inversor", r1=r1, r2=r2, gbw=gbw, vcc=vcc)

    def calcular_ganancia(self) -> float:
        """Av = 1 + R2 / R1  (positivo: conserva fase de la senal)."""
        return 1 + self.r2 / self.r1

    def calcular_salida(self, vin: float) -> float:
        """Vout = Av * Vin, limitado al rango [-Vcc, +Vcc]."""
        vout = self.calcular_ganancia() * vin
        return float(np.clip(vout, -self.vcc, self.vcc))
