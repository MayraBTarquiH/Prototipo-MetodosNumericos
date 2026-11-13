"""Utilidades compartidas de la interfaz Streamlit."""
import streamlit as st
from .casos import CASOS

AVISO = ("⚠️ Sistema **estrictamente educativo**. Los datos y parámetros son **sintéticos/hipotéticos** y no "
         "describen fallas verificadas de Mi Teleférico ni tienen conexión con equipos de control reales.")


@st.cache_resource(show_spinner="Conectando con la base de datos…")
def obtener_engine():
    from .db import get_engine
    try:
        return get_engine(), None
    except Exception as e:  # la app sigue funcionando sin BD, pero sin guardar
        return None, str(e)


def banner_bd():
    engine, err = obtener_engine()
    if engine is None:
        st.error(f"No hay conexión con la base de datos; no se podrá guardar ni abrir el historial.\n\n`{err}`")
    else:
        st.sidebar.caption(f"🗄️ Base de datos: **{engine.dialect.name}**")
    return engine


def pagina_pendiente(clave):
    """Pantalla de un módulo que aún no se implementa (prototipo Semana 1)."""
    c = CASOS[clave]
    st.title(f"{c['icono']} {c['nombre']}")
    st.caption(AVISO)
    banner_bd()
    st.info(f"Módulo visible en el prototipo. Estado: **{c['estado']}**.")
    t1, t2 = st.tabs(["Modelo", "Escenarios definidos"])
    with t1:
        st.markdown(f"**Pregunta:** {c['pregunta']}")
        st.latex(c["modelo"])
        st.markdown(f"**Variables y unidades:** {c['variables']}")
        st.markdown(f"**Referencia analítica:** {c['analitico']}")
        st.markdown("**Métodos que se usarán:** " + ", ".join(c["metodos"]))
    with t2:
        for tipo, desc in c["escenarios"].items():
            st.markdown(f"**{tipo.replace('_', ' ')}** — {desc}")
