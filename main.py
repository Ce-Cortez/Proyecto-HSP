# Punto de entrada del simulador de amplificadores operacionales.
# Configura los escenarios, instancia los amplificadores, corre todos
# los analisis y genera las graficas y reportes de salida.

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
# Escenarios predefinidos
# Cada escenario define un par R1/R2 que determina la ganancia del circuito.
# GBW y Vcc son constantes del op-amp — no cambian entre escenarios.
# ------------------------------------------------------------------
ESCENARIOS = [
    {"nombre": "Ganancia_Baja",  "r1": 1000, "r2": 10_000},   # |Av| inversor = 10
    {"nombre": "Ganancia_Media", "r1": 1000, "r2": 47_000},   # |Av| inversor = 47
    {"nombre": "Ganancia_Alta",  "r1": 1000, "r2": 100_000},  # |Av| inversor = 100
]

# Catalogo de op-amps reales con sus especificaciones tipicas de hoja de datos.
# GBW: producto ganancia-ancho de banda (Hz)
# VCC: voltaje de alimentacion simetrica tipica (V)
OP_AMPS = {
    "LM741":  {"gbw": 1.0e6,  "vcc": 15.0},   # clasico de laboratorio, lento
    "TL081":  {"gbw": 3.0e6,  "vcc": 15.0},   # FET input, bajo ruido, 3x mas rapido
    "LM318":  {"gbw": 15.0e6, "vcc": 15.0},   # alta velocidad, 15x vs LM741
}

# Cambia este valor para simular con un chip diferente
CHIP_ACTIVO = "LM741"


def separador(titulo: str):
    """Imprime un separador visual en consola para organizar la salida."""
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")


def main():
    # Leemos las specs del chip seleccionado una sola vez
    chip = OP_AMPS[CHIP_ACTIVO]
    gbw  = chip["gbw"]
    vcc  = chip["vcc"]

    # Creamos las instancias de salida una sola vez — se reusan en todos los escenarios
    viz = VisualizadorResultados(output_dir="outputs/graficas", chip_nombre=CHIP_ACTIVO)
    rep = GeneradorReporte(output_dir="outputs/reportes")

    print(f"Chip activo: {CHIP_ACTIVO}  (GBW={gbw/1e6:.1f} MHz, Vcc=±{vcc} V)")

    for escenario in ESCENARIOS:
        nombre_esc = escenario["nombre"]
        r1 = escenario["r1"]
        r2 = escenario["r2"]

        separador(f"ESCENARIO: {nombre_esc}  (R1={r1} Ohm, R2={r2} Ohm)")

        # --------------------------------------------------------------
        # 1. Instanciar las 4 configuraciones con los parametros del escenario
        # El seguidor y comparador ignoran r1/r2 del escenario — sus valores
        # son fijos por definicion del circuito.
        # --------------------------------------------------------------
        inv   = AmpInversor(r1=r1, r2=r2, gbw=gbw, vcc=vcc)
        noinv = AmpNoInversor(r1=r1, r2=r2, gbw=gbw, vcc=vcc)
        buf   = SeguidorVoltaje(gbw=gbw, vcc=vcc)
        comp  = Comparador(vref=vcc / 2, gbw=gbw, vcc=vcc)  # Vref = mitad de la alimentacion

        # --------------------------------------------------------------
        # 2. Registrar los amps en el simulador y correr todos los analisis
        # --------------------------------------------------------------
        sim = SimuladorCircuito()
        for amp in [inv, noinv, buf, comp]:
            sim.add_amplificador(amp)

        sim.ejecutar_analisis_completo()
        print(sim)  # imprime el resumen de ganancia, fc y BW de cada config

        # --------------------------------------------------------------
        # 3. Monte Carlo: evaluamos los 3 amps con retroalimentacion
        # El Comparador se excluye porque su ganancia es infinita
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

        # Curva de convergencia solo para el inversor como ejemplo representativo
        conv_inv = mc.curva_convergencia(inv, tolerancia=0.05)

        # --------------------------------------------------------------
        # 4. Graficas
        # --------------------------------------------------------------
        separador(f"GRAFICAS — {nombre_esc}")

        # Bode para los 3 amps con retroalimentacion (Comparador no tiene Bode)
        for amp in [inv, noinv, buf]:
            viz.plot_bode(amp, escenario=nombre_esc)

        # Histogramas MC — uno por amplificador con los 3 niveles de tolerancia
        for amp in [inv, noinv, buf]:
            viz.plot_histograma_mc(
                mc.get_resultados()[amp.nombre],
                f"{amp.nombre} ({nombre_esc})"
            )

        # Barra comparativa de ancho de banda entre configuraciones
        viz.plot_comparacion_ancho_banda(sim.comparar_anchos_banda())

        # Curva de convergencia del inversor
        viz.plot_convergencia(conv_inv, f"{inv.nombre} ({nombre_esc})")

        # Heatmap solo en el primer escenario — el rango R1/R2 es el mismo para todos
        if nombre_esc == "Ganancia_Baja":
            r1_range = np.linspace(500, 5000, 60)
            r2_range = np.linspace(1000, 100_000, 60)
            viz.plot_heatmap_ganancia(AmpInversor,   r1_range, r2_range)
            viz.plot_heatmap_ganancia(AmpNoInversor, r1_range, r2_range)

        # --------------------------------------------------------------
        # 5. Reporte de texto por escenario
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
