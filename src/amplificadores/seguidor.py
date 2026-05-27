# Seguidor de Voltaje (Buffer): el caso mas simple del no inversor.
# Ganancia = 1, lo que significa que la salida es identica a la entrada.
# Su utilidad no es amplificar sino aislar etapas: tiene impedancia de
# entrada muy alta e impedancia de salida muy baja.

import numpy as np
from .base import AmplificadorBase


class SeguidorVoltaje(AmplificadorBase):
    """
    Buffer de impedancia. Av = 1 siempre, sin importar nada.
    Fisicamente equivale a un no inversor con R2 = 0 y R1 = infinito.
    Tiene el mayor ancho de banda de todas las configuraciones porque
    GBW = BW * |Av| y con |Av| = 1, BW = GBW completo.

    R1 y R2 no son configurables — no tienen sentido fisico en este circuito.

    Args:
        gbw : producto ganancia-ancho de banda del op-amp (default 1 MHz)
        vcc : voltaje de alimentacion (default 15 V)
    """

    def __init__(self, gbw: float = 1e6, vcc: float = 15.0):
        # Llamamos al padre con R1 muy grande (simula infinito) y R2 = 0.
        # En este punto __bloqueado todavia no existe, entonces los setters
        # de r1/r2 de esta subclase dejan pasar los valores sin protestar.
        super().__init__("Seguidor de Voltaje (Buffer)", r1=1e12, r2=0.0, gbw=gbw, vcc=vcc)
        # A partir de aqui bloqueamos los setters para que nadie cambie R1/R2
        self.__bloqueado = True

    # ------------------------------------------------------------------
    # Sobrescribimos los setters de R1 y R2 para que sean de solo lectura
    # despues de que el objeto se crea. Usar getattr con default False
    # es el truco para que el bloqueo no aplique durante el __init__.
    # ------------------------------------------------------------------

    @property
    def r1(self) -> float:
        return super().r1

    @r1.setter
    def r1(self, valor: float):
        # Si __bloqueado ya existe y es True, rechazamos cualquier cambio
        if getattr(self, '_SeguidorVoltaje__bloqueado', False):
            raise ValueError("SeguidorVoltaje: R1 no es configurable (fijo en infinito).")
        # Si todavia no esta bloqueado (durante __init__), usamos el setter del padre
        AmplificadorBase.r1.fset(self, valor)

    @property
    def r2(self) -> float:
        return super().r2

    @r2.setter
    def r2(self, valor: float):
        if getattr(self, '_SeguidorVoltaje__bloqueado', False):
            raise ValueError("SeguidorVoltaje: R2 no es configurable (fijo en 0).")
        AmplificadorBase.r2.fset(self, valor)

    def calcular_ganancia(self) -> float:
        """
        La ganancia del seguidor es siempre 1, sin excepcion.
        No depende de R1 ni R2 — esa es la gracia del buffer.
        """
        return 1.0

    def calcular_salida(self, vin: float) -> float:
        """
        La salida replica la entrada. Solo recortamos si supera Vcc.

        Args:
            vin: voltaje de entrada en voltios

        Retorna:
            el mismo voltaje de entrada, acotado a [-Vcc, +Vcc]
        """
        return float(np.clip(vin, -self.vcc, self.vcc))

    def calcular_fc(self) -> float:
        """
        Sobrescribimos calcular_fc() porque la formula del padre (GBW / |Av|)
        daria GBW / 1 = GBW, que es correcto, pero queremos ser explicitos.
        El seguidor usa TODO el ancho de banda disponible del op-amp.
        """
        return self.gbw
