"""Persistencia con SQLAlchemy. Funciona con PostgreSQL (Supabase/Neon) y, para pruebas locales, SQLite."""
import json
import math
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import sqlalchemy as sa
from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Integer,
                        MetaData, String, Table, Text)
from sqlalchemy.dialects.postgresql import JSONB

JSONT = sa.JSON().with_variant(JSONB(), "postgresql")
metadata = MetaData()

caso_estudio = Table(
    "caso_estudio", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre", String(60), nullable=False, unique=True),
    Column("modelo_version", String(20), nullable=False, server_default="1.0"),
)
escenario = Table(
    "escenario", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("caso_id", Integer, ForeignKey("caso_estudio.id"), nullable=False),
    Column("tipo", String(20), nullable=False),
    Column("parametros_json", JSONT, nullable=False),
    Column("fuente_datos", Text),
    CheckConstraint("tipo IN ('NORMAL','ESTRÉS','MAL_CONDICIONADO')", name="ck_escenario_tipo"),
)
simulacion = Table(
    "simulacion", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("escenario_id", Integer, ForeignKey("escenario.id"), nullable=False),
    Column("fecha", DateTime(timezone=True), nullable=False),
    Column("equipo", String(80)),
    Column("estado", String(20), nullable=False, server_default="COMPLETADA"),
)
ejecucion_metodo = Table(
    "ejecucion_metodo", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("simulacion_id", Integer, ForeignKey("simulacion.id", ondelete="CASCADE"), nullable=False),
    Column("metodo", String(60), nullable=False),
    Column("tolerancia", Float),
    Column("paso", Float),
    Column("max_iter", Integer),
    Column("convergio", Boolean, nullable=False),
    Column("tiempo_ms", Float),
)
iteracion_resultado = Table(
    "iteracion_resultado", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ejecucion_id", Integer, ForeignKey("ejecucion_metodo.id", ondelete="CASCADE"), nullable=False),
    Column("numero", Integer, nullable=False),
    Column("aproximacion_json", JSONT),
    Column("residual", Float),
    Column("error_abs", Float),
    Column("error_rel", Float),
)
resultado_resumen = Table(
    "resultado_resumen", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ejecucion_id", Integer, ForeignKey("ejecucion_metodo.id", ondelete="CASCADE"), nullable=False),
    Column("referencia", Text),
    Column("valor_json", JSONT),
    Column("metrica_error_json", JSONT),
    Column("interpretacion", Text),
)

CASOS = ["Detención de emergencia", "Deterioro y mantenimiento", "Oscilaciones por viento",
         "Reconstrucción de sensores"]

_ENGINE = None


# ---------------------------------------------------------------- utilidades
def limpiar(o):
    """Convierte tipos NumPy y NaN/Inf a algo serializable en JSON (NaN/Inf -> None)."""
    if isinstance(o, dict):
        return {str(k): limpiar(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [limpiar(v) for v in o]
    if isinstance(o, np.ndarray):
        return limpiar(o.tolist())
    if isinstance(o, (np.bool_, bool)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        f = float(o)
        return f if math.isfinite(f) else None
    return o


def _url_desde_configuracion():
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
        if "db" in st.secrets:
            c = st.secrets["db"]
            return sa.engine.URL.create(
                c.get("dialect", "postgresql+psycopg2"), username=c["username"], password=c["password"],
                host=c["host"], port=int(c.get("port", 5432)), database=c.get("database", "postgres"))
    except Exception:
        pass
    os.makedirs("data", exist_ok=True)
    return "sqlite:///data/simtele_local.db"


def get_engine(url=None, forzar=False):
    global _ENGINE
    if _ENGINE is not None and url is None and not forzar:
        return _ENGINE
    url = url or _url_desde_configuracion()
    eng = sa.create_engine(url, pool_pre_ping=True,
                           json_serializer=lambda o: json.dumps(limpiar(o), allow_nan=False))
    init_db(eng)
    if not forzar:
        _ENGINE = eng
    return eng


def init_db(engine):
    metadata.create_all(engine)
    with engine.begin() as conn:
        existentes = {r[0] for r in conn.execute(sa.select(caso_estudio.c.nombre))}
        nuevos = [{"nombre": n, "modelo_version": "1.0"} for n in CASOS if n not in existentes]
        if nuevos:
            conn.execute(sa.insert(caso_estudio), nuevos)


def tipo_backend(engine):
    return engine.dialect.name


# ---------------------------------------------------------------- guardar
def _submuestrear(hist, maximo):
    if len(hist) <= maximo:
        return hist
    idx = np.unique(np.linspace(0, len(hist) - 1, maximo).astype(int))
    return [hist[i] for i in idx]


def guardar_simulacion(engine, caso, tipo, parametros, fuente, ejecuciones, equipo=None,
                       max_iter_guardadas=500):
    """Guarda una simulación completa. `ejecuciones` = lista de dicts con:
    metodo, tolerancia, paso, max_iter, convergio, tiempo_ms, historial[list], resumen{referencia, valor, metricas, interpretacion}
    Devuelve el id de la simulación."""
    with engine.begin() as conn:
        caso_id = conn.execute(sa.select(caso_estudio.c.id).where(caso_estudio.c.nombre == caso)).scalar_one()
        esc_id = conn.execute(sa.insert(escenario).values(
            caso_id=caso_id, tipo=tipo, parametros_json=limpiar(parametros), fuente_datos=fuente)
        ).inserted_primary_key[0]
        sim_id = conn.execute(sa.insert(simulacion).values(
            escenario_id=esc_id, fecha=datetime.now(timezone.utc), equipo=equipo, estado="COMPLETADA")
        ).inserted_primary_key[0]
        for e in ejecuciones:
            ej_id = conn.execute(sa.insert(ejecucion_metodo).values(
                simulacion_id=sim_id, metodo=e["metodo"], tolerancia=e.get("tolerancia"),
                paso=e.get("paso"), max_iter=e.get("max_iter"), convergio=bool(e["convergio"]),
                tiempo_ms=e.get("tiempo_ms"))).inserted_primary_key[0]
            filas = [{
                "ejecucion_id": ej_id, "numero": h["numero"],
                "aproximacion_json": limpiar(h["aproximacion"]), "residual": limpiar(h["residual"]),
                "error_abs": limpiar(h["error_abs"]), "error_rel": limpiar(h["error_rel"]),
            } for h in _submuestrear(e["historial"], max_iter_guardadas)]
            if filas:
                conn.execute(sa.insert(iteracion_resultado), filas)
            r = e.get("resumen", {})
            conn.execute(sa.insert(resultado_resumen).values(
                ejecucion_id=ej_id, referencia=r.get("referencia"), valor_json=limpiar(r.get("valor")),
                metrica_error_json=limpiar(r.get("metricas")), interpretacion=r.get("interpretacion")))
    return sim_id


# ---------------------------------------------------------------- consultar
def listar_simulaciones(engine, caso=None, tipo=None, texto=None):
    q = (sa.select(simulacion.c.id, simulacion.c.fecha, caso_estudio.c.nombre.label("caso"),
                   escenario.c.tipo.label("escenario"), simulacion.c.equipo, simulacion.c.estado)
         .select_from(simulacion.join(escenario, simulacion.c.escenario_id == escenario.c.id)
                      .join(caso_estudio, escenario.c.caso_id == caso_estudio.c.id))
         .order_by(simulacion.c.id.desc()))
    if caso:
        q = q.where(caso_estudio.c.nombre == caso)
    if tipo:
        q = q.where(escenario.c.tipo == tipo)
    if texto:
        q = q.where(sa.func.lower(sa.func.coalesce(simulacion.c.equipo, "")).like(f"%{texto.lower()}%"))
    with engine.connect() as conn:
        return pd.read_sql(q, conn)


def cargar_simulacion(engine, sim_id):
    with engine.connect() as conn:
        s = conn.execute(
            sa.select(simulacion, escenario.c.tipo, escenario.c.parametros_json, escenario.c.fuente_datos,
                      caso_estudio.c.nombre.label("caso"))
            .select_from(simulacion.join(escenario, simulacion.c.escenario_id == escenario.c.id)
                         .join(caso_estudio, escenario.c.caso_id == caso_estudio.c.id))
            .where(simulacion.c.id == sim_id)).mappings().first()
        if s is None:
            return None
        out = dict(s)
        if isinstance(out["parametros_json"], str):
            out["parametros_json"] = json.loads(out["parametros_json"])
        ejs = conn.execute(sa.select(ejecucion_metodo).where(ejecucion_metodo.c.simulacion_id == sim_id)
                           .order_by(ejecucion_metodo.c.id)).mappings().all()
        out["ejecuciones"] = []
        for e in ejs:
            e = dict(e)
            its = conn.execute(sa.select(iteracion_resultado).where(iteracion_resultado.c.ejecucion_id == e["id"])
                               .order_by(iteracion_resultado.c.numero)).mappings().all()
            e["iteraciones"] = []
            for i in its:
                i = dict(i)
                if isinstance(i["aproximacion_json"], str):
                    i["aproximacion_json"] = json.loads(i["aproximacion_json"])
                e["iteraciones"].append(i)
            r = conn.execute(sa.select(resultado_resumen).where(resultado_resumen.c.ejecucion_id == e["id"])
                             ).mappings().first()
            r = dict(r) if r else {}
            for k in ("valor_json", "metrica_error_json"):
                if isinstance(r.get(k), str):
                    r[k] = json.loads(r[k])
            e["resumen"] = r
            out["ejecuciones"].append(e)
    return out
