import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from src.amplificadores.base import AmplificadorBase

plt.style.use('ggplot')


class VisualizadorResultados:

    def __init__(self, output_dir: str = "outputs/graficas"):
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Utilidades privadas
    # ------------------------------------------------------------------

    def _guardar_o_mostrar(self, nombre_archivo: str, guardar: bool):
        plt.tight_layout()
        if guardar:
            ruta = os.path.join(self._output_dir, nombre_archivo)
            plt.savefig(ruta, dpi=150, bbox_inches='tight')
            print(f"  Guardado: {ruta}")
        else:
            plt.show()
        plt.close()

    # ------------------------------------------------------------------
    # Diagrama de Bode
    # ------------------------------------------------------------------

    def plot_bode(self, amp: AmplificadorBase, guardar: bool = True):
        """
        Genera diagrama de Bode de 2 paneles: magnitud (dB) y fase (grados).
        Marca la frecuencia de corte fc con linea vertical punteada.
        """
        freqs, magnitud_db, fase_deg = amp.respuesta_frecuencia()
        fc = amp.calcular_fc()

        fig, (ax_mag, ax_fase) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
        fig.suptitle(f"Diagrama de Bode — {amp.nombre}", fontsize=13, fontweight='bold')

        # Panel superior: magnitud
        ax_mag.semilogx(freqs, magnitud_db, linewidth=2, color='steelblue')
        ax_mag.axvline(fc, color='tomato', linestyle='--', linewidth=1.4,
                       label=f'fc = {fc:,.0f} Hz')
        ax_mag.axhline(amp.ganancia_db() - 3, color='gray', linestyle=':', linewidth=1,
                       label='-3 dB')
        ax_mag.set_ylabel("Magnitud (dB)")
        ax_mag.legend(fontsize=9)
        ax_mag.grid(True, which='both', alpha=0.4)

        # Panel inferior: fase
        ax_fase.semilogx(freqs, fase_deg, linewidth=2, color='darkorange')
        ax_fase.axvline(fc, color='tomato', linestyle='--', linewidth=1.4)
        ax_fase.set_ylabel("Fase (grados)")
        ax_fase.set_xlabel("Frecuencia (Hz)")
        ax_fase.grid(True, which='both', alpha=0.4)

        nombre_archivo = f"bode_{amp.nombre.replace(' ', '_')}.png"
        self._guardar_o_mostrar(nombre_archivo, guardar)

    # ------------------------------------------------------------------
    # Histograma Monte Carlo
    # ------------------------------------------------------------------

    def plot_histograma_mc(self, resultados_mc: dict, amp_nombre: str, guardar: bool = True):
        """
        3 subplots (uno por tolerancia: 1%, 5%, 10%).
        Cada subplot muestra histograma de ganancia + lineas de media y +-3sigma.
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

            ax.hist(g, bins=50, color=color, alpha=0.75, edgecolor='white')
            ax.axvline(media,         color='black',  linestyle='-',  linewidth=1.8,
                       label=f'Media = {media:.3f}')
            ax.axvline(media + 3*std, color='crimson', linestyle='--', linewidth=1.2,
                       label=f'+3σ = {media+3*std:.3f}')
            ax.axvline(media - 3*std, color='crimson', linestyle='--', linewidth=1.2,
                       label=f'-3σ = {media-3*std:.3f}')

            ax.set_title(f"Tolerancia ±{int(tol*100)}%\nP(fallo) = {p_fallo:.1%}", fontsize=10)
            ax.set_xlabel("Ganancia Av")
            ax.set_ylabel("Frecuencia")
            ax.legend(fontsize=7)

        nombre_archivo = f"mc_{amp_nombre.replace(' ', '_')}.png"
        self._guardar_o_mostrar(nombre_archivo, guardar)

    # ------------------------------------------------------------------
    # Comparacion de ancho de banda
    # ------------------------------------------------------------------

    def plot_comparacion_ancho_banda(self, comparacion: dict, guardar: bool = True):
        """
        Grafica de barras horizontales comparando BW de todas las configuraciones.
        Escala logaritmica en X para visualizar diferencias de ordenes de magnitud.
        """
        nombres = list(comparacion.keys())
        valores = list(comparacion.values())
        colores = ['steelblue', 'darkorange', 'seagreen', 'orchid'][:len(nombres)]

        fig, ax = plt.subplots(figsize=(9, 4))
        bars = ax.barh(nombres, valores, color=colores, edgecolor='white', height=0.5)
        ax.set_xscale('log')
        ax.set_xlabel("Ancho de Banda (Hz)")
        ax.set_title("Comparacion de Ancho de Banda", fontsize=13, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.4)

        # Etiqueta de valor sobre cada barra
        for bar, val in zip(bars, valores):
            ax.text(val * 1.05, bar.get_y() + bar.get_height() / 2,
                    f'{val:,.0f} Hz', va='center', fontsize=9)

        self._guardar_o_mostrar("comparacion_bw.png", guardar)

    # ------------------------------------------------------------------
    # Curva de convergencia Monte Carlo
    # ------------------------------------------------------------------

    def plot_convergencia(self, convergencia: dict, amp_nombre: str, guardar: bool = True):
        """
        2 paneles: media y sigma vs numero de muestras (eje X log).
        Linea de referencia en la media nominal (valor con N maximo).
        """
        n      = convergencia['n_muestras']
        medias = convergencia['medias']
        sigmas = convergencia['sigmas']
        media_ref = medias[-1]

        fig, (ax_med, ax_sig) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
        fig.suptitle(f"Convergencia Monte Carlo — {amp_nombre}", fontsize=13, fontweight='bold')

        # Panel superior: media
        ax_med.semilogx(n, medias, 'o-', color='steelblue', linewidth=2, markersize=5)
        ax_med.axhline(media_ref, color='tomato', linestyle='--', linewidth=1.2,
                       label=f'Referencia = {media_ref:.4f}')
        ax_med.set_ylabel("Media de Ganancia")
        ax_med.legend(fontsize=9)
        ax_med.grid(True, which='both', alpha=0.4)

        # Panel inferior: sigma
        ax_sig.semilogx(n, sigmas, 's-', color='darkorange', linewidth=2, markersize=5)
        ax_sig.set_ylabel("Desv. Estandar (σ)")
        ax_sig.set_xlabel("Numero de Muestras")
        ax_sig.grid(True, which='both', alpha=0.4)

        nombre_archivo = f"convergencia_{amp_nombre.replace(' ', '_')}.png"
        self._guardar_o_mostrar(nombre_archivo, guardar)

    # ------------------------------------------------------------------
    # Mapa de calor: ganancia vs R1 / R2
    # ------------------------------------------------------------------

    def plot_heatmap_ganancia(
        self,
        amp_class,
        r1_range: np.ndarray,
        r2_range: np.ndarray,
        guardar: bool = True,
    ):
        """
        Mapa de calor 2D: ganancia en dB para todo el espacio R1/R2.
        Calcula la ganancia instanciando un amp temporal por celda usando
        meshgrid vectorizado — eficiente para rangos moderados.
        """
        R1, R2 = np.meshgrid(r1_range, r2_range)

        # Calculo vectorizado segun clase
        amp_name = amp_class.__name__
        if amp_name == 'AmpInversor':
            Av = -R2 / R1
        elif amp_name == 'AmpNoInversor':
            Av = 1 + R2 / R1
        else:
            raise ValueError(f"Heatmap no soportado para {amp_name}.")

        Av_db = 20 * np.log10(np.abs(Av))

        fig, ax = plt.subplots(figsize=(8, 6))
        heatmap = ax.pcolormesh(r2_range, r1_range, Av_db, cmap='viridis', shading='auto')
        cbar = fig.colorbar(heatmap, ax=ax)
        cbar.set_label("Ganancia (dB)", fontsize=10)

        ax.set_xlabel("R2 (Ohm)")
        ax.set_ylabel("R1 (Ohm)")
        ax.set_title(
            f"Mapa de Calor — Ganancia vs R1/R2 ({amp_name})",
            fontsize=13, fontweight='bold'
        )

        nombre_archivo = f"heatmap_{amp_name}.png"
        self._guardar_o_mostrar(nombre_archivo, guardar)
