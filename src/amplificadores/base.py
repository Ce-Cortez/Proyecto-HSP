# Clase base abstracta para todos los amplificadores operacionales.
# Define los atributos y metodos comunes, y fuerza a las subclases
# a implementar su propia logica de ganancia y salida.

from abc import ABC, abstractmethod
import numpy as np


class AmplificadorBase(ABC):
    """
    Clase base de la que heredan los 4 tipos de amplificadores.
    No se puede instanciar directamente — solo sirve como plantilla.

    Atributos:
        nombre : nombre de la configuracion (lo define cada subclase)
        r1     : resistencia R1 en ohms (debe ser > 0)
        r2     : resistencia R2 en ohms (debe ser >= 0)
        gbw    : producto ganancia-ancho de banda del op-amp en Hz
        vcc    : voltaje de alimentacion en V (limita la salida)
    """

    def __init__(self, nombre: str, r1: float, r2: float, gbw: float = 1e6, vcc: float = 15.0):
        # El nombre lo pasa cada subclase, el usuario no lo toca directamente
        self.__nombre = nombre
        # Usamos los setters para que la validacion corra desde el inicio
        self.r1  = r1
        self.r2  = r2
        self.gbw = gbw
        self.vcc = vcc

    # ------------------------------------------------------------------
    # Properties — acceso controlado a los atributos privados
    # ------------------------------------------------------------------

    @property
    def nombre(self) -> str:
        # Solo lectura: el nombre no cambia despues de crear el objeto
        return self.__nombre

    @property
    def r1(self) -> float:
        return self.__r1

    @r1.setter
    def r1(self, valor: float):
        # R1 en el denominador de la formula de ganancia, no puede ser 0 o negativo
        if valor <= 0:
            raise ValueError(f"R1 debe ser mayor a 0, recibido: {valor}")
        self.__r1 = float(valor)

    @property
    def r2(self) -> float:
        return self.__r2

    @r2.setter
    def r2(self, valor: float):
        # R2 puede ser 0 (caso del SeguidorVoltaje), pero no negativo
        if valor < 0:
            raise ValueError(f"R2 debe ser mayor o igual a 0, recibido: {valor}")
        self.__r2 = float(valor)

    @property
    def gbw(self) -> float:
        return self.__gbw

    @gbw.setter
    def gbw(self, valor: float):
        # GBW es una caracteristica del chip, siempre positiva
        if valor <= 0:
            raise ValueError(f"GBW debe ser mayor a 0, recibido: {valor}")
        self.__gbw = float(valor)

    @property
    def vcc(self) -> float:
        return self.__vcc

    @vcc.setter
    def vcc(self, valor: float):
        # Vcc es el voltaje de alimentacion, no tiene sentido en negativo
        if valor <= 0:
            raise ValueError(f"Vcc debe ser mayor a 0, recibido: {valor}")
        self.__vcc = float(valor)

    # ------------------------------------------------------------------
    # Metodos abstractos — cada subclase DEBE implementar estos dos
    # ------------------------------------------------------------------

    @abstractmethod
    def calcular_ganancia(self) -> float:
        """
        Retorna la ganancia de voltaje Av en forma lineal (no en dB).
        Cada configuracion tiene su propia formula:
          Inversor    -> Av = -R2/R1
          No Inversor -> Av = 1 + R2/R1
          Seguidor    -> Av = 1
          Comparador  -> Av = inf
        """

    @abstractmethod
    def calcular_salida(self, vin: float) -> float:
        """
        Calcula el voltaje de salida dado un voltaje de entrada vin.
        La mayoria de las configs hace Vout = Av * Vin y recorta a +-Vcc.
        El Comparador lo hace diferente: salida digital 0 o Vcc.

        Args:
            vin: voltaje de entrada en voltios
        """

    # ------------------------------------------------------------------
    # Metodos concretos — estos ya estan implementados y las subclases
    # los heredan sin necesidad de redefinirlos (salvo excepciones)
    # ------------------------------------------------------------------

    def ganancia_db(self) -> float:
        """
        Convierte la ganancia lineal a decibeles.
        Usa valor absoluto para que el signo negativo del Inversor no rompa el log.
        Formula: Av_dB = 20 * log10(|Av|)
        """
        return 20 * np.log10(abs(self.calcular_ganancia()))

    def calcular_fc(self) -> float:
        """
        Calcula la frecuencia de corte a -3dB del amplificador.
        A mayor ganancia, menor ancho de banda — esa es la relacion inversa
        que impone el GBW del op-amp.
        Formula: fc = GBW / |Av|
        """
        return self.__gbw / abs(self.calcular_ganancia())

    def calcular_ancho_banda(self) -> float:
        """
        Retorna el ancho de banda util del amplificador en Hz.
        Para este modelo de primer orden es igual a fc.
        Existe como metodo propio para claridad semantica en el simulador.
        """
        return self.calcular_fc()

    def respuesta_frecuencia(
        self, f_min: float = 1, f_max: float = 1e7, n_puntos: int = 500
    ) -> tuple:
        """
        Genera los arrays necesarios para dibujar el diagrama de Bode.
        Usa un modelo de filtro pasa-bajas de primer orden:

            H(f) = Av / (1 + j * f / fc)

        Donde j es la unidad imaginaria. Numpy maneja aritmetica compleja
        directamente, lo que hace el calculo de magnitud y fase muy limpio.

        Args:
            f_min    : frecuencia minima del rango (Hz), por defecto 1 Hz
            f_max    : frecuencia maxima del rango (Hz), por defecto 10 MHz
            n_puntos : cuantos puntos generar en la curva

        Retorna:
            freqs       : array de frecuencias en Hz en escala logaritmica
            magnitud_db : magnitud de H(f) en dB para cada frecuencia
            fase_deg    : fase de H(f) en grados para cada frecuencia
        """
        av = self.calcular_ganancia()
        fc = self.calcular_fc()

        # Espacio logaritmico para que las decadas queden bien distribuidas en la grafica
        freqs = np.logspace(np.log10(f_min), np.log10(f_max), n_puntos)

        # H es un array de numeros complejos — numpy lo maneja sin problema
        H = av / (1 + 1j * freqs / fc)

        # np.abs da el modulo, np.angle da la fase en radianes (deg=True lo convierte)
        magnitud_db = 20 * np.log10(np.abs(H))
        fase_deg    = np.angle(H, deg=True)

        return freqs, magnitud_db, fase_deg

    def __str__(self) -> str:
        # Resumen legible para imprimir en consola durante la simulacion
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
