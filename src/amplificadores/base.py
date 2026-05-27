from abc import ABC, abstractmethod
import numpy as np


class AmplificadorBase(ABC):

    def __init__(self, nombre: str, r1: float, r2: float, gbw: float = 1e6, vcc: float = 15.0):
        self.__nombre = nombre
        self.r1 = r1
        self.r2 = r2
        self.gbw = gbw
        self.vcc = vcc

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def r1(self) -> float:
        return self.__r1

    @r1.setter
    def r1(self, valor: float):
        if valor <= 0:
            raise ValueError(f"R1 debe ser mayor a 0, recibido: {valor}")
        self.__r1 = float(valor)

    @property
    def r2(self) -> float:
        return self.__r2

    @r2.setter
    def r2(self, valor: float):
        if valor < 0:
            raise ValueError(f"R2 debe ser mayor o igual a 0, recibido: {valor}")
        self.__r2 = float(valor)

    @property
    def gbw(self) -> float:
        return self.__gbw

    @gbw.setter
    def gbw(self, valor: float):
        if valor <= 0:
            raise ValueError(f"GBW debe ser mayor a 0, recibido: {valor}")
        self.__gbw = float(valor)

    @property
    def vcc(self) -> float:
        return self.__vcc

    @vcc.setter
    def vcc(self, valor: float):
        if valor <= 0:
            raise ValueError(f"Vcc debe ser mayor a 0, recibido: {valor}")
        self.__vcc = float(valor)

    # ------------------------------------------------------------------
    # Metodos abstractos — cada subclase debe implementarlos
    # ------------------------------------------------------------------

    @abstractmethod
    def calcular_ganancia(self) -> float:
        """Retorna la ganancia de voltaje Av (lineal, no en dB)."""

    @abstractmethod
    def calcular_salida(self, vin: float) -> float:
        """Retorna el voltaje de salida para un voltaje de entrada vin."""

    # ------------------------------------------------------------------
    # Metodos concretos — heredados por todas las subclases
    # ------------------------------------------------------------------

    def ganancia_db(self) -> float:
        """Retorna la ganancia en dB: 20 * log10(|Av|)."""
        return 20 * np.log10(abs(self.calcular_ganancia()))

    def calcular_fc(self) -> float:
        """Retorna la frecuencia de corte: fc = GBW / |Av|."""
        return self.__gbw / abs(self.calcular_ganancia())

    def calcular_ancho_banda(self) -> float:
        """Retorna el ancho de banda util del amplificador (igual a fc)."""
        return self.calcular_fc()

    def respuesta_frecuencia(
        self, f_min: float = 1, f_max: float = 1e7, n_puntos: int = 500
    ) -> tuple:
        """
        Genera datos del diagrama de Bode usando modelo de primer orden.

        H(f) = Av / (1 + j * f / fc)

        Retorna:
            freqs       : array de frecuencias en Hz (escala logaritmica)
            magnitud_db : magnitud de H(f) en dB
            fase_deg    : fase de H(f) en grados
        """
        av = self.calcular_ganancia()
        fc = self.calcular_fc()

        freqs = np.logspace(np.log10(f_min), np.log10(f_max), n_puntos)
        H = av / (1 + 1j * freqs / fc)

        magnitud_db = 20 * np.log10(np.abs(H))
        fase_deg = np.angle(H, deg=True)

        return freqs, magnitud_db, fase_deg

    def __str__(self) -> str:
        av = self.calcular_ganancia()
        fc = self.calcular_fc()
        return (
            f"{'='*45}\n"
            f"  {self.__nombre}\n"
            f"{'='*45}\n"
            f"  R1          : {self.__r1:>12.2f} Ohm\n"
            f"  R2          : {self.__r2:>12.2f} Ohm\n"
            f"  GBW         : {self.__gbw:>12.0f} Hz\n"
            f"  Vcc         : {self.__vcc:>12.1f} V\n"
            f"  Ganancia Av : {av:>12.4f}\n"
            f"  Ganancia dB : {self.ganancia_db():>12.2f} dB\n"
            f"  Frec. corte : {fc:>12.2f} Hz\n"
            f"{'='*45}"
        )
