# Amplificador Inversor: la configuracion mas basica del op-amp con retroalimentacion.
# Invierte la fase de la senal de entrada y la amplifica segun la razon R2/R1.

import numpy as np
from .base import AmplificadorBase


class AmpInversor(AmplificadorBase):
    """
    Implementa la configuracion inversora del op-amp.
    La ganancia es negativa por definicion — eso significa que si la entrada
    sube, la salida baja, y viceversa (inversion de fase de 180 grados).

    Args:
        r1  : resistencia de entrada en ohms
        r2  : resistencia de retroalimentacion en ohms
        gbw : producto ganancia-ancho de banda del op-amp (default 1 MHz)
        vcc : voltaje de alimentacion (default 15 V)
    """

    def __init__(self, r1: float, r2: float, gbw: float = 1e6, vcc: float = 15.0):
        # Pasamos el nombre fijo y dejamos que la clase base maneje el resto
        super().__init__("Amplificador Inversor", r1=r1, r2=r2, gbw=gbw, vcc=vcc)

    def calcular_ganancia(self) -> float:
        """
        Calcula la ganancia de voltaje del amplificador inversor.
        El signo negativo indica inversion de fase, no que el amplificador
        'pierda' senal — en dB se usa el valor absoluto.
        Formula: Av = -R2 / R1
        """
        return -self.r2 / self.r1

    def calcular_salida(self, vin: float) -> float:
        """
        Calcula el voltaje de salida para una entrada vin.
        Si el resultado supera +-Vcc, el op-amp satura y recortamos al limite.

        Args:
            vin: voltaje de entrada en voltios

        Retorna:
            voltaje de salida en voltios, acotado a [-Vcc, +Vcc]
        """
        vout = self.calcular_ganancia() * vin
        # np.clip recorta el valor al rango [min, max] — maneja saturacion del op-amp
        return float(np.clip(vout, -self.vcc, self.vcc))
