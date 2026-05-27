# Generador de reporte: exporta todos los resultados de la simulacion
# a un archivo de texto plano legible, sin dependencias externas.
# El reporte esta dividido en secciones y usa separadores para que
# sea facil de leer tanto en consola como en un editor de texto.

import os
import datetime


class GeneradorReporte:
    """
    Escribe un reporte de texto con los resultados de la simulacion.
    No usa librerias externas — solo formato de strings de Python.

    Args:
        output_dir: carpeta donde se guarda el reporte (se crea si no existe)
    """

    def __init__(self, output_dir: str = "outputs/reportes"):
        self._output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generar(
        self,
        resultados: dict,
        resultados_mc: dict,
        filename: str = "reporte.txt",
    ):
        """
        Genera el archivo de reporte con todos los resultados de la simulacion.
        El archivo se sobreescribe si ya existe.

        Estructura del reporte:
          1. Encabezado con titulo y timestamp
          2. Resumen por amplificador: ganancia, fc, ancho de banda
          3. Estadisticas Monte Carlo por amp y por nivel de tolerancia
          4. Tabla comparativa de ancho de banda entre configuraciones
          5. Pie con timestamp final

        Args:
            resultados    : dict de resultados del SimuladorCircuito
            resultados_mc : dict de resultados del AnalizadorMonteCarlo
            filename      : nombre del archivo de salida
        """
        ruta  = os.path.join(self._output_dir, filename)
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sep   = "=" * 65   # separador de seccion principal
        sep2  = "-" * 65   # separador de subseccion

        # Construimos el contenido como lista de lineas para unir al final
        lineas = []

        # ------------------------------------------------------------------
        # Seccion 1: encabezado
        # ------------------------------------------------------------------
        lineas += [
            sep,
            "  REPORTE DE SIMULACION — AMPLIFICADORES OPERACIONALES",
            f"  Generado: {ahora}",
            sep,
            "",
        ]

        # ------------------------------------------------------------------
        # Seccion 2: resumen por amplificador
        # Mostramos los valores calculados para cada configuracion.
        # Si un valor es None (Comparador) ponemos N/A.
        # ------------------------------------------------------------------
        lineas += ["  SECCION 1: RESUMEN POR CONFIGURACION", sep2]

        for nombre, datos in resultados.items():
            lineas.append(f"\n  [{nombre}]")
            lineas.append(f"    Ganancia Av    : {datos['ganancia']}")

            if datos['ganancia_db'] is not None:
                lineas.append(f"    Ganancia (dB)  : {datos['ganancia_db']:.4f} dB")
            else:
                lineas.append( "    Ganancia (dB)  : N/A (lazo abierto)")

            if datos['fc'] is not None:
                lineas.append(f"    Frec. corte fc : {datos['fc']:,.2f} Hz")
            else:
                lineas.append( "    Frec. corte fc : N/A")

            if datos['ancho_banda'] is not None:
                lineas.append(f"    Ancho de banda : {datos['ancho_banda']:,.2f} Hz")
            else:
                lineas.append( "    Ancho de banda : N/A")

        lineas += ["", sep2, ""]

        # ------------------------------------------------------------------
        # Seccion 3: estadisticas Monte Carlo
        # Una tabla por amplificador con media, std y probabilidad de fallo
        # para cada nivel de tolerancia analizado.
        # ------------------------------------------------------------------
        lineas += ["  SECCION 2: ANALISIS MONTE CARLO", sep2]

        if not resultados_mc:
            lineas.append("  Sin resultados Monte Carlo.")
        else:
            for amp_nombre, por_tol in resultados_mc.items():
                lineas.append(f"\n  [{amp_nombre}]")
                # Encabezado de la tabla
                lineas.append(
                    f"    {'Tolerancia':>12}  {'Media':>10}  {'Std Dev':>10}  {'P(fallo)':>10}"
                )
                lineas.append(f"    {'-'*12}  {'-'*10}  {'-'*10}  {'-'*10}")

                # Una fila por nivel de tolerancia, ordenadas de menor a mayor
                for tol, datos in sorted(por_tol.items()):
                    lineas.append(
                        f"    {f'+-{int(tol*100)}%':>12}  "
                        f"{datos['media']:>10.4f}  "
                        f"{datos['std']:>10.4f}  "
                        f"{datos['prob_fallo']:>10.2%}"
                    )

        lineas += ["", sep2, ""]

        # ------------------------------------------------------------------
        # Seccion 4: tabla comparativa de ancho de banda
        # Muestra todos los amps en una tabla para comparacion directa.
        # El Comparador aparece como N/A porque no tiene BW definido.
        # ------------------------------------------------------------------
        lineas += ["  SECCION 3: COMPARATIVA DE ANCHO DE BANDA", sep2]
        lineas.append(f"\n    {'Configuracion':<35}  {'Ancho de Banda':>15}")
        lineas.append(f"    {'-'*35}  {'-'*15}")

        for nombre, datos in resultados.items():
            if datos['ancho_banda'] is not None:
                lineas.append(f"    {nombre:<35}  {datos['ancho_banda']:>12,.2f} Hz")
            else:
                lineas.append(f"    {nombre:<35}  {'N/A':>15}")

        lineas += ["", sep2, ""]

        # ------------------------------------------------------------------
        # Pie del reporte
        # ------------------------------------------------------------------
        lineas += [
            f"  Fin del reporte. {ahora}",
            sep,
        ]

        # Unimos todas las lineas y escribimos el archivo
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("\n".join(lineas))

        print(f"  Reporte guardado: {ruta}")
        return ruta
