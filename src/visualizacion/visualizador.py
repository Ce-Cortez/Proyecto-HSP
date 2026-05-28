# Visualizador de resultados: genera todas las graficas del proyecto.
# Cada metodo produce una figura diferente y la guarda como .png en outputs/graficas/.
# Si guardar=False, muestra la figura en pantalla en lugar de guardarla.

import os
import numpy as np
import matplotlib.pyplot as plt

from src.amplificadores.base import AmplificadorBase

# Estilo visual consistente para todas las graficas
plt.style.use('ggplot')


class VisualizadorResultados:
    """
    Genera y guarda todas las graficas del simulador.
    Recibe datos del SimuladorCircuito y del AnalizadorMonteCarlo
    y los convierte en imagenes listas para el reporte.

    Args:
        output_dir: carpeta donde se guardan los .png (se crea si no existe)
    """

    def __init__(self, output_dir: str = "outputs/graficas", chip_nombre: str = ""):
        self._output_dir = output_dir
        # Prefijo que se antepone a cada nombre de archivo (ej. "LM741_")
        self._prefijo = f"{chip_nombre}_" if chip_nombre else ""
        # Creamos la carpeta raiz y cada subcarpeta por tipo de grafica
        for sub in ("bode", "monte_carlo", "convergencia", "comparacion", "heatmaps"):
            os.makedirs(os.path.join(output_dir, sub), exist_ok=True)

    def _guardar_o_mostrar(self, nombre_archivo: str, guardar: bool, subfolder: str = ""):
        """
        Cierre estandar de cada figura: aplica layout ajustado y
        guarda o muestra segun el parametro guardar.
        Siempre llama plt.close() para liberar memoria.

        Args:
            nombre_archivo : nombre del archivo .png a guardar
            guardar        : True = guardar en disco, False = mostrar en pantalla
            subfolder      : subcarpeta dentro de output_dir (ej. "bode", "monte_carlo")
        """
        plt.tight_layout()
        if guardar:
            ruta = os.path.join(self._output_dir, subfolder, nombre_archivo)
            plt.savefig(ruta, dpi=150, bbox_inches='tight')
            print(f"  Guardado: {ruta}")
        else:
            plt.show()
        # Cerramos la figura para que no se acumule en memoria
        plt.close()

    def plot_bode(self, amp: AmplificadorBase, guardar: bool = True):
        """
        Genera el diagrama de Bode del amplificador: magnitud y fase vs frecuencia.
        Panel superior: magnitud en dB (muestra como cae la ganancia con la frecuencia).
        Panel inferior: fase en grados (muestra el desfase que introduce el amp).
        La linea roja punteada marca la frecuencia de corte fc.

        Args:
            amp     : amplificador a graficar (debe tener respuesta_frecuencia())
            guardar : True guarda el png, False lo muestra en pantalla
        """
        freqs, magnitud_db, fase_deg = amp.respuesta_frecuencia()
        fc = amp.calcular_fc()

        # Dos paneles que comparten el mismo eje X de frecuencia
        fig, (ax_mag, ax_fase) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
        fig.suptitle(f"Diagrama de Bode — {amp.nombre}", fontsize=13, fontweight='bold')

        # Panel superior: magnitud en dB
        ax_mag.semilogx(freqs, magnitud_db, linewidth=2, color='steelblue')
        # Linea vertical en fc — donde la ganancia cae 3 dB respecto al valor maximo
        ax_mag.axvline(fc, color='tomato', linestyle='--', linewidth=1.4,
                       label=f'fc = {fc:,.0f} Hz')
        # Linea horizontal en Av_dB - 3 para marcar visualmente el punto de -3dB
        ax_mag.axhline(amp.ganancia_db() - 3, color='gray', linestyle=':', linewidth=1,
                       label='-3 dB')
        ax_mag.set_ylabel("Magnitud (dB)")
        ax_mag.legend(fontsize=9)
        ax_mag.grid(True, which='both', alpha=0.4)

        # Panel inferior: fase en grados
        ax_fase.semilogx(freqs, fase_deg, linewidth=2, color='darkorange')
        ax_fase.axvline(fc, color='tomato', linestyle='--', linewidth=1.4)
        ax_fase.set_ylabel("Fase (grados)")
        ax_fase.set_xlabel("Frecuencia (Hz)")
        ax_fase.grid(True, which='both', alpha=0.4)

        nombre_archivo = f"{self._prefijo}bode_{amp.nombre.replace(' ', '_')}.png"
        self._guardar_o_mostrar(nombre_archivo, guardar, subfolder="bode")

    def plot_histograma_mc(self, resultados_mc: dict, amp_nombre: str, guardar: bool = True):
        """
        Muestra la distribucion de ganancia bajo variacion de tolerancias.
        Un subplot por nivel de tolerancia (1%, 5%, 10%) lado a lado.
        Las lineas verticales muestran la media y los limites de +-3 sigma.
        El titulo de cada subplot indica la probabilidad de fallo.

        Args:
            resultados_mc : dict de resultados MC indexado por tolerancia
            amp_nombre    : nombre del amplificador para el titulo
            guardar       : True guarda, False muestra
        """
        tolerancias = sorted(resultados_mc.keys())
        colores = ['steelblue', 'darkorange', 'seagreen']

        fig, axes = plt.subplots(1, 3, figsize=(14, 4))
        fig.suptitle(f"Monte Carlo — {amp_nombre}", fontsize=13, fontweight='bold')

        for ax, tol, color in zip(axes, tolerancias, colores):
            datos   = resultados_mc[tol]
            g       = datos['ganancias']
            media   = datos['media']
            std     = datos['std']
            p_fallo = datos['prob_fallo']

            # Histograma de la distribucion de ganancias
            ax.hist(g, bins=50, color=color, alpha=0.75, edgecolor='white')

            # Linea negra en la media
            ax.axvline(media, color='black', linestyle='-', linewidth=1.8,
                       label=f'Media = {media:.3f}')
            # Lineas rojas en media +/- 3 sigma (limites de especificacion)
            ax.axvline(media + 3*std, color='crimson', linestyle='--', linewidth=1.2,
                       label=f'+3s = {media+3*std:.3f}')
            ax.axvline(media - 3*std, color='crimson', linestyle='--', linewidth=1.2,
                       label=f'-3s = {media-3*std:.3f}')

            ax.set_title(f"Tolerancia +-{int(tol*100)}%\nP(fallo) = {p_fallo:.1%}", fontsize=10)
            ax.set_xlabel("Ganancia Av")
            ax.set_ylabel("Frecuencia")
            ax.legend(fontsize=7)

        nombre_archivo = f"{self._prefijo}mc_{amp_nombre.replace(' ', '_')}.png"
        self._guardar_o_mostrar(nombre_archivo, guardar, subfolder="monte_carlo")

    def plot_comparacion_ancho_banda(self, comparacion: dict, guardar: bool = True):
        """
        Grafica de barras horizontales comparando el ancho de banda de cada config.
        Usa escala logaritmica en X porque los valores difieren en ordenes de magnitud
        (ej. 10 kHz vs 1 MHz no se aprecian bien en escala lineal).
        Cada barra tiene un color distinto y muestra el valor en Hz al costado.

        Args:
            comparacion : dict {nombre_amp: ancho_banda_hz}
            guardar     : True guarda, False muestra
        """
        nombres = list(comparacion.keys())
        valores = list(comparacion.values())
        colores = ['steelblue', 'darkorange', 'seagreen', 'orchid'][:len(nombres)]

        fig, ax = plt.subplots(figsize=(9, 4))
        bars = ax.barh(nombres, valores, color=colores, edgecolor='white', height=0.5)

        # Escala log para que las diferencias grandes sean visibles
        ax.set_xscale('log')
        ax.set_xlabel("Ancho de Banda (Hz)")
        ax.set_title("Comparacion de Ancho de Banda", fontsize=13, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.4)

        # Etiqueta numerica al lado derecho de cada barra
        for bar, val in zip(bars, valores):
            ax.text(val * 1.05, bar.get_y() + bar.get_height() / 2,
                    f'{val:,.0f} Hz', va='center', fontsize=9)

        self._guardar_o_mostrar(f"{self._prefijo}comparacion_bw.png", guardar, subfolder="comparacion")

    def plot_convergencia(self, convergencia: dict, amp_nombre: str, guardar: bool = True):
        """
        Muestra como la media y la sigma del analisis MC se estabilizan
        al aumentar el numero de muestras. Con pocas muestras los valores
        son inestables — la curva muestra cuando ya son suficientemente confiables.

        Panel superior: media de ganancia vs N muestras.
        Panel inferior: sigma vs N muestras.
        La linea de referencia en el panel superior es el valor con N maximo.

        Args:
            convergencia : dict con n_muestras, medias, sigmas
            amp_nombre   : nombre del amplificador para el titulo
            guardar      : True guarda, False muestra
        """
        n      = convergencia['n_muestras']
        medias = convergencia['medias']
        sigmas = convergencia['sigmas']
        # Tomamos el ultimo valor de media como referencia (el mas estable)
        media_ref = medias[-1]

        fig, (ax_med, ax_sig) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
        fig.suptitle(f"Convergencia Monte Carlo — {amp_nombre}", fontsize=13, fontweight='bold')

        # Panel superior: como converge la media
        ax_med.semilogx(n, medias, 'o-', color='steelblue', linewidth=2, markersize=5)
        ax_med.axhline(media_ref, color='tomato', linestyle='--', linewidth=1.2,
                       label=f'Referencia = {media_ref:.4f}')
        ax_med.set_ylabel("Media de Ganancia")
        ax_med.legend(fontsize=9)
        ax_med.grid(True, which='both', alpha=0.4)

        # Panel inferior: como converge la sigma
        ax_sig.semilogx(n, sigmas, 's-', color='darkorange', linewidth=2, markersize=5)
        ax_sig.set_ylabel("Desv. Estandar (sigma)")
        ax_sig.set_xlabel("Numero de Muestras")
        ax_sig.grid(True, which='both', alpha=0.4)

        nombre_archivo = f"{self._prefijo}convergencia_{amp_nombre.replace(' ', '_')}.png"
        self._guardar_o_mostrar(nombre_archivo, guardar, subfolder="convergencia")

    def plot_heatmap_ganancia(
        self,
        amp_class,
        r1_range: np.ndarray,
        r2_range: np.ndarray,
        guardar: bool = True,
    ):
        """
        Mapa de calor 2D que muestra la ganancia en dB para todas las
        combinaciones posibles de R1 y R2 en los rangos dados.
        Muy util para visualizar como la ganancia cambia con los componentes
        y para elegir valores de resistencias en el diseno.

        Usa meshgrid de numpy para calcular toda la matriz de golpe,
        sin necesidad de iterar con loops.

        Args:
            amp_class : clase del amplificador (AmpInversor o AmpNoInversor)
            r1_range  : array de valores de R1 a barrer en ohms
            r2_range  : array de valores de R2 a barrer en ohms
            guardar   : True guarda, False muestra
        """
        # Meshgrid crea matrices 2D con todas las combinaciones de R1 y R2
        R1, R2 = np.meshgrid(r1_range, r2_range)

        # Aplicamos la formula de ganancia vectorizada segun la clase
        amp_name = amp_class.__name__
        if amp_name == 'AmpInversor':
            Av = -R2 / R1          # Av = -R2/R1
        elif amp_name == 'AmpNoInversor':
            Av = 1 + R2 / R1       # Av = 1 + R2/R1
        else:
            raise ValueError(f"Heatmap no soportado para {amp_name}.")

        # Convertimos a dB para la escala de color
        Av_db = 20 * np.log10(np.abs(Av))

        fig, ax = plt.subplots(figsize=(8, 6))
        # pcolormesh es mas rapido que imshow para datos no uniformes
        heatmap = ax.pcolormesh(r2_range, r1_range, Av_db, cmap='viridis', shading='auto')
        cbar = fig.colorbar(heatmap, ax=ax)
        cbar.set_label("Ganancia (dB)", fontsize=10)

        ax.set_xlabel("R2 (Ohm)")
        ax.set_ylabel("R1 (Ohm)")
        ax.set_title(
            f"Mapa de Calor — Ganancia vs R1/R2 ({amp_name})",
            fontsize=13, fontweight='bold'
        )

        nombre_archivo = f"{self._prefijo}heatmap_{amp_name}.png"
        self._guardar_o_mostrar(nombre_archivo, guardar, subfolder="heatmaps")
