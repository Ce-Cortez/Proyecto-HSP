import os
import datetime


class GeneradorReporte:

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
        Exporta resumen completo de la simulacion a archivo de texto plano.

        Secciones:
          1. Encabezado
          2. Resumen por amplificador (ganancia, fc, BW)
          3. Estadisticas Monte Carlo por amp y tolerancia
          4. Tabla comparativa de ancho de banda
          5. Pie con timestamp
        """
        ruta = os.path.join(self._output_dir, filename)
        ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sep  = "=" * 65
        sep2 = "-" * 65

        lineas = []

        # ------------------------------------------------------------------
        # 1. Encabezado
        # ------------------------------------------------------------------
        lineas += [
            sep,
            "  REPORTE DE SIMULACION — AMPLIFICADORES OPERACIONALES",
            f"  Generado: {ahora}",
            sep,
            "",
        ]

        # ------------------------------------------------------------------
        # 2. Resumen por amplificador
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
        # 3. Estadisticas Monte Carlo
        # ------------------------------------------------------------------
        lineas += ["  SECCION 2: ANALISIS MONTE CARLO", sep2]

        if not resultados_mc:
            lineas.append("  Sin resultados Monte Carlo.")
        else:
            for amp_nombre, por_tol in resultados_mc.items():
                lineas.append(f"\n  [{amp_nombre}]")
                lineas.append(
                    f"    {'Tolerancia':>12}  {'Media':>10}  {'Std Dev':>10}  {'P(fallo)':>10}"
                )
                lineas.append(f"    {'-'*12}  {'-'*10}  {'-'*10}  {'-'*10}")

                for tol, datos in sorted(por_tol.items()):
                    lineas.append(
                        f"    {f'+-{int(tol*100)}%':>12}  "
                        f"{datos['media']:>10.4f}  "
                        f"{datos['std']:>10.4f}  "
                        f"{datos['prob_fallo']:>10.2%}"
                    )

        lineas += ["", sep2, ""]

        # ------------------------------------------------------------------
        # 4. Tabla comparativa de ancho de banda
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
        # 5. Pie
        # ------------------------------------------------------------------
        lineas += [
            f"  Fin del reporte. {ahora}",
            sep,
        ]

        with open(ruta, 'w', encoding='utf-8') as f:
            f.write("\n".join(lineas))

        print(f"  Reporte guardado: {ruta}")
        return ruta
