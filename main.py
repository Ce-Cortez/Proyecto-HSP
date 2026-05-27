import sys
import numpy as np

from src.amplificadores.inversor import AmpInversor
from src.amplificadores.no_inversor import AmpNoInversor
from src.amplificadores.seguidor import SeguidorVoltaje
from src.amplificadores.comparador import Comparador
from src.simulacion.simulador import SimuladorCircuito
from src.simulacion.monte_carlo import AnalizadorMonteCarlo
from src.visualizacion.visualizador import VisualizadorResultados
from src.reporte.generador import GeneradorReporte


# ------------------------------------------------------------------
# Escenarios predefinidos: R1/R2 fijos por escenario
# GBW y Vcc son constantes del op-amp ideal
# ------------------------------------------------------------------
ESCENARIOS = [
    {"nombre": "Ganancia_Baja",  "r1": 1000, "r2": 10_000},   # |Av| = 10
    {"nombre": "Ganancia_Media", "r1": 1000, "r2": 47_000},   # |Av| = 47
    {"nombre": "Ganancia_Alta",  "r1": 1000, "r2": 100_000},  # |Av| = 100
]

GBW = 1e6    # Hz  — op-amp ideal (LM741 / uA741)
VCC = 15.0   # V


def separador(titulo: str):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")


def main():
    viz = VisualizadorResultados(output_dir="outputs/graficas")
    rep = GeneradorReporte(output_dir="outputs/reportes")

    for escenario in ESCENARIOS:
        nombre_esc = escenario["nombre"]
        r1 = escenario["r1"]
        r2 = escenario["r2"]

        separador(f"ESCENARIO: {nombre_esc}  (R1={r1} Ohm, R2={r2} Ohm)")

        # --------------------------------------------------------------
        # 1. Instanciar amplificadores
        # --------------------------------------------------------------
        inv   = AmpInversor(r1=r1, r2=r2, gbw=GBW, vcc=VCC)
        noinv = AmpNoInversor(r1=r1, r2=r2, gbw=GBW, vcc=VCC)
        buf   = SeguidorVoltaje(gbw=GBW, vcc=VCC)
        comp  = Comparador(vref=VCC / 2, gbw=GBW, vcc=VCC)

        # --------------------------------------------------------------
        # 2. Analisis principal
        # --------------------------------------------------------------
        sim = SimuladorCircuito()
        for amp in [inv, noinv, buf, comp]:
            sim.add_amplificador(amp)

        sim.ejecutar_analisis_completo()
        print(sim)

        # --------------------------------------------------------------
        # 3. Monte Carlo (Comparador excluido)
        # --------------------------------------------------------------
        separador(f"MONTE CARLO — {nombre_esc}")
        mc = AnalizadorMonteCarlo(n_muestras=1000)

        for amp in [inv, noinv, buf]:
            mc.ejecutar(amp)
            datos = mc.get_resultados()[amp.nombre]
            print(f"\n  {amp.nombre}")
            for tol, d in sorted(datos.items()):
                print(
                    f"    +-{int(tol*100):>2}%  "
                    f"media={d['media']:8.4f}  "
                    f"std={d['std']:7.4f}  "
                    f"P(fallo)={d['prob_fallo']:.2%}"
                )

        conv_inv = mc.curva_convergencia(inv, tolerancia=0.05)

        # --------------------------------------------------------------
        # 4. Visualizaciones
        # --------------------------------------------------------------
        separador(f"GRAFICAS — {nombre_esc}")

        # Bode para cada amp con respuesta en frecuencia
        for amp in [inv, noinv, buf]:
            viz.plot_bode(amp)

        # Histogramas MC
        for amp in [inv, noinv, buf]:
            nombre_archivo = f"{amp.nombre.replace(' ', '_')}_{nombre_esc}"
            viz.plot_histograma_mc(
                mc.get_resultados()[amp.nombre],
                f"{amp.nombre} ({nombre_esc})"
            )

        # Comparacion de ancho de banda
        viz.plot_comparacion_ancho_banda(sim.comparar_anchos_banda())

        # Convergencia (solo AmpInversor como representativo)
        viz.plot_convergencia(conv_inv, f"{inv.nombre} ({nombre_esc})")

        # Heatmap R1/R2 (solo primer escenario para no duplicar)
        if nombre_esc == "Ganancia_Baja":
            r1_range = np.linspace(500, 5000, 60)
            r2_range = np.linspace(1000, 100_000, 60)
            viz.plot_heatmap_ganancia(AmpInversor,   r1_range, r2_range)
            viz.plot_heatmap_ganancia(AmpNoInversor, r1_range, r2_range)

        # --------------------------------------------------------------
        # 5. Reporte por escenario
        # --------------------------------------------------------------
        separador(f"REPORTE — {nombre_esc}")
        rep.generar(
            sim.get_resultados(),
            mc.get_resultados(),
            filename=f"reporte_{nombre_esc}.txt",
        )

    separador("SIMULACION COMPLETA")
    print("  Graficas : outputs/graficas/")
    print("  Reportes : outputs/reportes/")


if __name__ == "__main__":
    main()
