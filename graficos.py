import numpy as np
import pandas as pd
import plotly.graph_objects as go


def fig_convergencia(resultados):
    """Residuo ||b-Ax|| vs iteración (solo métodos iterativos) en escala log."""
    fig = go.Figure()
    for r in resultados:
        h = r["historial"]
        if len(h) < 2:
            continue
        y = [max(p["residual"], 1e-20) for p in h]
        fig.add_scatter(x=[p["numero"] for p in h], y=y, mode="lines", name=r["metodo"])
    fig.update_yaxes(type="log", title="Residuo ‖b − A x‖₂")
    fig.update_xaxes(title="Iteración")
    fig.update_layout(title="Convergencia (residuo vs iteración)", height=380, margin=dict(t=50, b=40))
    return fig


def fig_errores(resultados):
    """Error absoluto final y residuo final por método (escala log)."""
    nombres = [r["metodo"] for r in resultados]
    err = [max(r["historial"][-1]["error_abs"], 1e-20) for r in resultados]
    res = [max(r["historial"][-1]["residual"], 1e-20) for r in resultados]
    fig = go.Figure()
    fig.add_bar(x=nombres, y=err, name="Error ‖x* − x‖₂")
    fig.add_bar(x=nombres, y=res, name="Residuo ‖b − Ax‖₂")
    fig.update_yaxes(type="log", title="Valor final")
    fig.update_layout(title="Error vs residuo final por método", barmode="group", height=380,
                      margin=dict(t=50, b=40))
    return fig


def fig_solucion(resultados, x_star):
    fig = go.Figure()
    idx = list(range(1, len(x_star) + 1))
    fig.add_scatter(x=idx, y=x_star, mode="lines+markers", name="x* (exacta)", line=dict(width=4))
    for r in resultados:
        x = np.asarray(r["x"], float)
        if np.all(np.isfinite(x)) and np.max(np.abs(x)) < 1e6:
            fig.add_scatter(x=idx, y=x, mode="markers", name=r["metodo"])
    fig.update_layout(title="Solución obtenida vs x*", xaxis_title="Componente i", yaxis_title="x_i",
                      height=380, margin=dict(t=50, b=40))
    return fig


def tabla_metodos(resultados, x_star=None):
    from .errores import error_porcentual
    filas = []
    for r in resultados:
        u = r["historial"][-1]
        filas.append({
            "Método": r["metodo"], "Convergió": "sí" if r["convergio"] else "NO",
            "Iteraciones": r["iteraciones"], "Residuo ‖b−Ax‖": u["residual"],
            "Error abs ‖x*−x‖": u["error_abs"], "Error rel": u["error_rel"],
            "Error %": None if u["error_rel"] is None else 100 * u["error_rel"],
            "Tiempo (ms)": round(r["tiempo_ms"], 3), "Criterio de parada": r["motivo_parada"],
        })
    return pd.DataFrame(filas)
