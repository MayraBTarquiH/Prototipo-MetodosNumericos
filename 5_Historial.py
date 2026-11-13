import numpy as np
import plotly.graph_objects as go
import streamlit as st

from core import db
from core.escenarios import TIPOS
from core.modulo2 import correr
from core.ui import AVISO, banner_bd

st.set_page_config(page_title="Historial · SIMTELE-RISK", page_icon="🚡", layout="wide")
st.title("🗂️ Historial de experimentos")
st.caption(AVISO)
engine = banner_bd()
if engine is None:
    st.stop()

f1, f2, f3 = st.columns(3)
caso = f1.selectbox("Caso", [""] + db.CASOS, format_func=lambda v: v or "Todos")
tipo = f2.selectbox("Escenario", [""] + list(TIPOS), format_func=lambda v: (v or "Todos").replace("_", " "))
texto = f3.text_input("Buscar por equipo/usuario")
df = db.listar_simulaciones(engine, caso or None, tipo or None, texto or None)
st.dataframe(df, width="stretch", hide_index=True)
if df.empty:
    st.info("Aún no hay simulaciones guardadas. Ejecuta y guarda una en el módulo Deterioro.")
    st.stop()

sid = st.selectbox("Abrir simulación #", df["id"].tolist())
S = db.cargar_simulacion(engine, int(sid))
st.markdown(f"### Simulación #{S['id']} · {S['caso']} · {S['tipo'].replace('_', ' ')}")
st.caption(f"Fecha: {S['fecha']} · Equipo: {S['equipo'] or '—'} · Estado: {S['estado']} · Fuente: {S['fuente_datos']}")
with st.expander("Parámetros guardados (JSON)", expanded=True):
    st.json(S["parametros_json"])

st.dataframe([{
    "Método": e["metodo"], "Convergió": "sí" if e["convergio"] else "NO", "Tolerancia": e["tolerancia"],
    "Máx. iter": e["max_iter"], "Iteraciones": (e["resumen"].get("valor_json") or {}).get("iteraciones"),
    "Residuo": (e["resumen"].get("metrica_error_json") or {}).get("residual"),
    "Error abs": (e["resumen"].get("metrica_error_json") or {}).get("error_abs"),
    "Error %": (e["resumen"].get("metrica_error_json") or {}).get("error_pct"),
    "Tiempo ms": round(e["tiempo_ms"] or 0, 3)} for e in S["ejecuciones"]],
    width="stretch", hide_index=True)

fig = go.Figure()
for e in S["ejecuciones"]:
    if len(e["iteraciones"]) > 1:
        fig.add_scatter(x=[i["numero"] for i in e["iteraciones"]],
                        y=[max(i["residual"] or 1e-20, 1e-20) for i in e["iteraciones"]], name=e["metodo"])
fig.update_yaxes(type="log", title="Residuo")
fig.update_xaxes(title="Iteración")
fig.update_layout(title="Convergencia recuperada desde la base de datos", height=380)
st.plotly_chart(fig, width="stretch")

interp = next((e["resumen"].get("interpretacion") for e in S["ejecuciones"] if e["resumen"].get("interpretacion")), None)
if interp:
    with st.expander("Interpretación guardada"):
        st.markdown(interp.replace("\n", "  \n"))

# ------------------------------------------------------------------ relanzar
st.divider()
st.markdown("### 🔁 Relanzar y verificar coincidencia")
if S["caso"] != "Deterioro y mantenimiento":
    st.info("En la Semana 1 solo se puede relanzar el módulo Deterioro.")
else:
    tol_c = st.select_slider("Tolerancia de coincidencia (relativa a ‖x‖)", [10.0 ** -e for e in range(4, 15)],
                             value=1e-8, format_func=lambda v: f"{v:.0e}")
    if st.button("Repetir el cálculo con los parámetros guardados"):
        nuevo = correr(S["parametros_json"])
        filas, todo_ok = [], True
        for e, r in zip(S["ejecuciones"], nuevo["res"]):
            xg = np.array((e["resumen"].get("valor_json") or {}).get("x", []), float)
            dif = float(np.max(np.abs(xg - r["x"]))) if xg.size == len(r["x"]) else float("nan")
            ok = bool(dif <= tol_c * max(1.0, float(np.linalg.norm(xg))))
            todo_ok &= ok
            filas.append({"Método": r["metodo"], "Máx |x_guardada − x_nueva|": dif,
                          "Iter. guardadas": (e["resumen"].get("valor_json") or {}).get("iteraciones"),
                          "Iter. nuevas": r["iteraciones"], "Coincide": "✅" if ok else "❌"})
        st.dataframe(filas, width="stretch", hide_index=True)
        (st.success if todo_ok else st.error)(
            "Los resultados recalculados coinciden con los guardados dentro de la tolerancia."
            if todo_ok else "Hay diferencias fuera de la tolerancia.")
