import numpy as np
from .base import AmplificadorBase


class SeguidorVoltaje(AmplificadorBase):
    """
    Buffer de impedancia. Av = 1 siempre.
    R1 = infinito (1e12), R2 = 0. No configurables tras instanciar.
    Ancho de banda maximo entre todas las configuraciones (BW = GBW).
    """

    def __init__(self, gbw: float = 1e6, vcc: float = 15.0):
        # super().__init__ usa los setters de la base para r1/r2.
        # __bloqueado aun no existe aqui, por lo que los setters de esta
        # subclase dejan pasar los valores sin restriccion.
        super().__init__("Seguidor de Voltaje (Buffer)", r1=1e12, r2=0.0, gbw=gbw, vcc=vcc)
        # A partir de este punto los setters de r1/r2 bloquean cambios.
        self.__bloqueado = True

    # ------------------------------------------------------------------
    # Bloqueo de R1 y R2 (no tienen sentido fisico en un buffer)
    # ------------------------------------------------------------------

    @property
    def r1(self) -> float:
        return super().r1

    @r1.setter
    def r1(self, valor: float):
        if getattr(self, '_SeguidorVoltaje__bloqueado', False):
            raise ValueError("SeguidorVoltaje: R1 no es configurable (fijo en infinito).")
        AmplificadorBase.r1.fset(self, valor)

    @property
    def r2(self) -> float:
        return super().r2

    @r2.setter
    def r2(self, valor: float):
        if getattr(self, '_SeguidorVoltaje__bloqueado', False):
            raise ValueError("SeguidorVoltaje: R2 no es configurable (fijo en 0).")
        AmplificadorBase.r2.fset(self, valor)

    # ------------------------------------------------------------------
    # Implementacion de metodos abstractos
    # ------------------------------------------------------------------

    def calcular_ganancia(self) -> float:
        """Av = 1 (unitario siempre, independiente de R1/R2)."""
        return 1.0

    def calcular_salida(self, vin: float) -> float:
        """Vout = Vin, limitado al rango [-Vcc, +Vcc]."""
        return float(np.clip(vin, -self.vcc, self.vcc))

    # ------------------------------------------------------------------
    # Override de calcular_fc
    # ------------------------------------------------------------------

    def calcular_fc(self) -> float:
        """fc = GBW (Av = 1, por lo que el ancho de banda es maximo)."""
        return self.gbw
