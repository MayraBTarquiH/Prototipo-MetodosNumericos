import numpy as np
import streamlit as st

from core.casos import CASOS
from core.escenarios import MATRICES, PARAMS_DEFECTO, TIPOS
from core.graficos import fig_convergencia, fig_errores, fig_solucion, tabla_metodos
from core.modulo2 import PLANTILLA_PROBLEMA, a_ejecuciones, conclusion_numerica, correr
from core.ui import AVISO, banner_bd
from core import db

st.set_page_config(page_title="Deterioro · SIMTELE-RISK", page_icon="🚡", layout="wide")
C = CASOS["deterioro"]
st.title(f"{C['icono']} {C['nombre']}")
st.caption(AVISO)
engine = banner_bd()

tab_modelo, tab_res, tab_interp = st.tabs(["1 · Modelo y parámetros", "2 · Resultados", "3 · Interpretación"])

# ------------------------------------------------------------------ MODELO
with tab_modelo:
    st.markdown(f"**Pregunta:** {C['pregunta']}")
    st.latex(C["modelo"])
    st.markdown(f"**Variables y unidades:** {C['variables']}")
    st.markdown(f"**Referencia verificable:** {C['analitico']}")
    st.info("**Semana 1:** subexperimento de *sistemas lineales para calibración*. Se construye A x* = b con "
            "x* conocido (x* = [1, 2, …, n]) y se comparan Referencia directa, LU, Jacobi, Gauss-Seidel y "
            "Gradiente Conjugado. Las raíces D(t)=D_umbral llegan en la Semana 2.")
    tipo = st.radio("Escenario", TIPOS, horizontal=True, format_func=lambda t: t.replace("_", " "))
    st.caption(C["escenarios"][tipo])
    base = PARAMS_DEFECTO[tipo]
    k = tipo
    c1, c2, c3 = st.columns(3)
    matriz = c1.selectbox("Matriz A", list(MATRICES), index=list(MATRICES).index(base["matriz"]),
                          format_func=lambda m: MATRICES[m], key=f"mat_{k}")
    n = c2.number_input("Tamaño n (≥ 4)", 4, 200, base["n"], step=1, key=f"n_{k}")
    tol = c3.select_slider("Tolerancia (‖b−Ax‖/‖b‖)", [10.0 ** -e for e in range(2, 15)],
                           value=base["tol"], format_func=lambda v: f"{v:.0e}", key=f"tol_{k}")
    c4, c5 = st.columns(2)
    max_iter = c4.number_input("Máx. iteraciones", 10, 100000, base["max_iter"], step=100, key=f"mi_{k}")
    eps_sens = c5.select_slider("Perturbación relativa de b (sensibilidad)",
                                [10.0 ** -e for e in range(1, 13)], value=base["eps_sens"],
                                format_func=lambda v: f"{v:.0e}", key=f"es_{k}")
    equipo = st.text_input("Equipo / usuario (opcional)", key="equipo")
    params = {"matriz": matriz, "n": int(n), "tol": float(tol), "max_iter": int(max_iter),
              "eps_sens": float(eps_sens)}
    if st.button("▶ Ejecutar los 5 métodos", type="primary"):
        try:
            with st.spinner("Calculando…"):
                st.session_state["m2"] = {"tipo": tipo, "params": params, "out": correr(params),
                                          "id": st.session_state.get("m2", {}).get("id", 0) + 1,
                                          "guardada": None}
            st.success("Listo. Revisa las pestañas Resultados e Interpretación.")
        except Exception as e:
            st.error(f"Error en el cálculo: {e}")

M = st.session_state.get("m2")

# ------------------------------------------------------------------ RESULTADOS
with tab_res:
    if not M:
        st.info("Ejecuta una simulación en la pestaña 1.")
    else:
        out, d, s = M["out"], M["out"]["diag"], M["out"]["sens"]
        st.markdown(f"#### Escenario **{M['tipo'].replace('_', ' ')}** · {MATRICES[M['params']['matriz']]} · n = {d['n']}")
        m = st.columns(4)
        m[0].metric("κ(A)", f"{d['kappa']:.3e}")
        m[1].metric("¿A es SPD?", "sí" if d["spd"] else "no")
        m[2].metric("ρ Jacobi", f"{d['rho_jacobi']:.4f}")
        m[3].metric("ρ Gauss-Seidel", f"{d['rho_gauss_seidel']:.4f}")
        st.caption("Condición suficiente: diagonal dominante estricta ⇒ Jacobi y GS convergen. "
                   "A SPD ⇒ GS y Gradiente Conjugado convergen. Jacobi converge ⇔ ρ < 1. "
                   f"Diagonalmente dominante: **{'sí' if d['diag_dominante'] else 'no'}**.")
        st.dataframe(tabla_metodos(out["res"]).style.format(
            {"Residuo ‖b−Ax‖": "{:.2e}", "Error abs ‖x*−x‖": "{:.2e}", "Error rel": "{:.2e}", "Error %": "{:.2e}"},
            na_rep="—"), width="stretch", hide_index=True)
        g1, g2 = st.columns(2)
        g1.plotly_chart(fig_convergencia(out["res"]), width="stretch")
        g2.plotly_chart(fig_errores(out["res"]), width="stretch")
        st.plotly_chart(fig_solucion(out["res"], out["x_star"]), width="stretch")
        st.markdown("**Sensibilidad ante perturbación de b** (resuelta con LU)")
        st.table({"‖δb‖/‖b‖": [f"{s['cambio_rel_b']:.2e}"], "‖δx‖/‖x‖": [f"{s['cambio_rel_x']:.2e}"],
                  "Amplificación": [f"{s['amplificacion']:.2f}"], "Cota κ(A)": [f"{s['cota_kappa']:.2e}"]})
        with st.expander("Ver factores de LU (P A = L U)" + (" — solo si n ≤ 8" if d["n"] > 8 else "")):
            if d["n"] <= 8:
                ex = out["res"][1]["extra"]
                st.write("Permutación P:", ex["P"])
                st.write("L"); st.dataframe(ex["L"])
                st.write("U"); st.dataframe(ex["U"])
            else:
                st.write("Usa n ≤ 8 para visualizar los factores.")
        with st.expander("Ver iteraciones (primeras 50) de un método"):
            nom = st.selectbox("Método", [r["metodo"] for r in out["res"]])
            r = next(r for r in out["res"] if r["metodo"] == nom)
            st.dataframe([{"k": h["numero"], "residuo": h["residual"], "error_abs": h["error_abs"],
                           "error_rel": h["error_rel"], "x": np.round(h["aproximacion"], 6).tolist()}
                          for h in r["historial"][:50]], width="stretch", hide_index=True)

# ------------------------------------------------------------------ INTERPRETACIÓN
with tab_interp:
    if not M:
        st.info("Ejecuta una simulación primero.")
    else:
        rid = M["id"]
        st.markdown("### Conclusión NUMÉRICA (sobre los métodos)")
        c_num = st.text_area("Editable", conclusion_numerica(M["out"], M["tipo"]), height=230, key=f"cn_{rid}")
        st.markdown("### Conclusión del PROBLEMA (sobre el fenómeno simulado)")
        c_pro = st.text_area("Editable", PLANTILLA_PROBLEMA, height=170, key=f"cp_{rid}")
        st.divider()
        if engine is None:
            st.warning("Sin base de datos: no se puede guardar.")
        elif M["guardada"]:
            st.success(f"Guardada como simulación #{M['guardada']}. Ábrela en **Historial**.")
        elif st.button("💾 Guardar experimento en la base de datos"):
            texto = f"## CONCLUSIÓN NUMÉRICA\n{c_num}\n\n## CONCLUSIÓN DEL PROBLEMA\n{c_pro}"
            sid = db.guardar_simulacion(
                engine, C["nombre"], M["tipo"], M["params"],
                "Sintético: A construida por fórmula, b = A·x*, x* = [1..n]",
                a_ejecuciones(M["out"], M["params"], texto), equipo=st.session_state.get("equipo") or None)
            M["guardada"] = sid
            st.rerun()
