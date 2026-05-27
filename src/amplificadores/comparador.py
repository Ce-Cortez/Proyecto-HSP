# Comparador: la configuracion mas diferente de todas.
# Opera en lazo abierto (sin retroalimentacion), lo que le da ganancia infinita.
# La salida no es analoga sino digital: o esta en Vcc o en 0V.
# Compara la entrada Vin contra un voltaje de referencia Vref y decide cual es mayor.

import numpy as np
from .base import AmplificadorBase


class Comparador(AmplificadorBase):
    """
    Comparador de voltaje con salida digital rail-to-rail.
    Si Vin > Vref -> salida = Vcc
    Si Vin <= Vref -> salida = 0V

    Como opera en lazo abierto, no tiene frecuencia de corte ni Bode definidos.
    Esos metodos lanzan NotImplementedError si alguien intenta llamarlos.

    Args:
        vref : voltaje de referencia contra el que se compara Vin (default 0 V)
        gbw  : producto ganancia-ancho de banda (se usa para estimar tiempo de respuesta)
        vcc  : voltaje de alimentacion, que define el nivel alto de la salida
    """

    def __init__(self, vref: float = 0.0, gbw: float = 1e6, vcc: float = 15.0):
        # R1 y R2 no tienen rol en el comparador, los ponemos en valores neutros
        super().__init__("Comparador", r1=1.0, r2=0.0, gbw=gbw, vcc=vcc)
        self.__vref = float(vref)

    @property
    def vref(self) -> float:
        return self.__vref

    @vref.setter
    def vref(self, valor: float):
        # Vref si es configurable — puede ser cualquier voltaje dentro de la alimentacion
        self.__vref = float(valor)

    def calcular_ganancia(self) -> float:
        """
        En lazo abierto la ganancia es teoricamente infinita.
        Retornamos float('inf') para representar ese estado.
        Esto es lo que hace que el comparador sature instantaneamente.
        """
        return float('inf')

    def calcular_salida(self, vin: float) -> float:
        """
        Toma la decision de comparacion y retorna la salida digital.
        No hay valores intermedios — o es Vcc o es 0V.

        Args:
            vin: voltaje de entrada a comparar contra Vref

        Retorna:
            Vcc si vin > vref, 0.0 si vin <= vref
        """
        return self.vcc if vin > self.__vref else 0.0

    # ------------------------------------------------------------------
    # Estos metodos no tienen sentido para el comparador.
    # Los sobrescribimos para dar un mensaje de error claro en lugar
    # de dejar que el codigo falle de forma confusa.
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

    def calcular_tiempo_respuesta(self) -> float:
        """
        Estimacion simplificada del retardo de propagacion del comparador.
        En la realidad depende del slew rate y otros factores del chip,
        pero para este modelo usamos 1/GBW como aproximacion.

        Retorna:
            tiempo de respuesta estimado en segundos
        """
        return 1.0 / self.gbw

    def calcular_histeresis(self, delta_v: float) -> dict:
        """
        Calcula los umbrales de histeresis simetricos alrededor de Vref.
        La histeresis evita que el comparador oscile cuando la senal
        esta muy cerca de Vref (por ejemplo con ruido superpuesto).

        Args:
            delta_v: ancho total de la ventana de histeresis en voltios

        Retorna:
            dict con umbral_alto, umbral_bajo y ventana
        """
        return {
            "umbral_alto": self.__vref + delta_v / 2,  # el comparador conmuta hacia arriba aqui
            "umbral_bajo": self.__vref - delta_v / 2,  # el comparador conmuta hacia abajo aqui
            "ventana":     delta_v,
        }

    def respuesta_con_ruido(self, vin: float, ruido_std: float, n_muestras: int = 1000) -> dict:
        """
        Simula cuantas veces el comparador dispara alto o bajo cuando
        la entrada tiene ruido gaussiano superpuesto.
        Util para saber que tan confiable es el comparador cerca de Vref.

        Args:
            vin        : voltaje de entrada nominal (sin ruido)
            ruido_std  : desviacion estandar del ruido en voltios
            n_muestras : cuantas muestras de ruido generar

        Retorna:
            dict con prob_alto (fraccion de veces que salio Vcc),
            prob_bajo (fraccion de veces que salio 0V) y n_muestras
        """
        # Generamos n_muestras versiones ruidosas del voltaje de entrada
        muestras = np.random.normal(vin, ruido_std, n_muestras)

        # Evaluamos la salida del comparador para cada muestra
        salidas = np.array([self.calcular_salida(v) for v in muestras])

        # Contamos cuantas veces la salida fue Vcc
        n_alto = int(np.sum(salidas == self.vcc))

        return {
            "prob_alto":  n_alto / n_muestras,
            "prob_bajo":  (n_muestras - n_alto) / n_muestras,
            "n_muestras": n_muestras,
        }

    def __str__(self) -> str:
        # Sobrescribimos __str__ porque el de la clase base llama calcular_fc()
        # que lanzaria NotImplementedError en el comparador
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
