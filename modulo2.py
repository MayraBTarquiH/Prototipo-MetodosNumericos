"""Lógica del Módulo 2 (calibración por sistemas lineales) separada de la interfaz."""
import numpy as np
from .errores import error_porcentual, sensibilidad
from .escenarios import construir_sistema
from .sistemas_lineales import diagnostico, lu_resolver, resolver_todos


def correr(params):
    A, b, x_star = construir_sistema(params)
    diag = diagnostico(A)
    res = resolver_todos(A, b, x_star, float(params["tol"]), int(params["max_iter"]))
    sens = sensibilidad(lambda A_, b_: lu_resolver(A_, b_)["x"], A, b, eps=float(params["eps_sens"]))
    return {"A": A, "b": b, "x_star": x_star, "diag": diag, "res": res, "sens": sens}


def conclusion_numerica(out, tipo):
    d, res, s = out["diag"], out["res"], out["sens"]
    it = [r for r in res if r["tolerancia"] is not None]
    ok = [r["metodo"] for r in it if r["convergio"]]
    mal = [r["metodo"] for r in it if not r["convergio"]]
    L = [f"κ(A) = {d['kappa']:.3e}; A {'es' if d['spd'] else 'NO es'} SPD y "
         f"{'es' if d['diag_dominante'] else 'NO es'} diagonalmente dominante.",
         f"Radio espectral: ρ(T_Jacobi) = {d['rho_jacobi']:.4f}, ρ(T_GS) = {d['rho_gauss_seidel']:.4f} "
         "(un método estacionario converge para todo x0 si y solo si ρ < 1)."]
    if ok:
        mejor = min((r for r in it if r["convergio"]), key=lambda r: r["iteraciones"])
        L.append(f"Convergieron: {', '.join(ok)}. El de menos iteraciones fue {mejor['metodo']} ({mejor['iteraciones']}).")
    if mal:
        L.append(f"NO alcanzaron la tolerancia: {', '.join(mal)}. Ver criterio de parada: distinguir DIVERGENCIA "
                 "(ρ > 1) de convergencia lenta (ρ ≈ 1) y ambas de un problema mal condicionado.")
    ref = res[0]["historial"][-1]
    L.append(f"La referencia directa logra residuo {ref['residual']:.1e} y error {ref['error_abs']:.1e}. "
             f"Con una perturbación relativa de {s['cambio_rel_b']:.1e} en b, la solución cambió "
             f"{s['cambio_rel_x']:.1e} (amplificación {s['amplificacion']:.1f} ≤ κ(A) = {s['cota_kappa']:.2e}).")
    if tipo == "MAL_CONDICIONADO":
        L.append("Un residuo pequeño NO implica error pequeño cuando κ(A) es grande: error ≲ κ(A)·residuo relativo.")
    return "\n".join(f"- {l}" for l in L)


PLANTILLA_PROBLEMA = (
    "(Completar con sus palabras)\n"
    "- Qué representa x en la calibración de D(t) = D0 + αt + βt² y qué significa un error en x para la "
    "estimación del tiempo de inspección.\n"
    "- Qué variables influyen (número de datos, ruido, condicionamiento del ajuste).\n"
    "- Qué NO puede inferirse: los datos son sintéticos y el modelo es hipotético."
)


def a_ejecuciones(out, params, interpretacion):
    x_star = out["x_star"]
    ejs = []
    for r in out["res"]:
        u = r["historial"][-1]
        ejs.append({
            "metodo": r["metodo"], "tolerancia": r["tolerancia"], "paso": None, "max_iter": r["max_iter"],
            "convergio": r["convergio"], "tiempo_ms": r["tiempo_ms"], "historial": r["historial"],
            "resumen": {
                "referencia": "x* conocido; b = A x*",
                "valor": {"x": r["x"], "iteraciones": r["iteraciones"], "motivo_parada": r["motivo_parada"]},
                "metricas": {"residual": u["residual"], "error_abs": u["error_abs"], "error_rel": u["error_rel"],
                             "error_pct": error_porcentual(x_star, r["x"]), "kappa": out["diag"]["kappa"],
                             "sensibilidad": out["sens"]},
                "interpretacion": interpretacion,
            },
        })
    return ejs
