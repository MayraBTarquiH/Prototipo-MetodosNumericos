import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core import db
from core.errores import error_absoluto, error_relativo, numero_condicion
from core.escenarios import PARAMS_DEFECTO, construir_sistema
from core.modulo2 import a_ejecuciones, correr
from core.sistemas_lineales import lu_factorizar, resolver_todos


def test_errores_sin_division_por_cero():
    assert error_relativo(np.zeros(3), np.ones(3)) is None
    assert error_absoluto([1, 2], [1, 2.5]) == pytest.approx(0.5)


def test_lu_reconstruye_A():
    A, _, _ = construir_sistema(PARAMS_DEFECTO["NORMAL"])
    P, L, U = lu_factorizar(A)
    assert np.allclose(A[P], L @ U)


def test_normal_todos_convergen_y_son_precisos():
    p = PARAMS_DEFECTO["NORMAL"]
    A, b, x = construir_sistema(p)
    for r in resolver_todos(A, b, x, p["tol"], p["max_iter"]):
        assert r["convergio"]
        assert r["historial"][-1]["error_abs"] < 1e-8


def test_cg_termina_en_a_lo_sumo_n_iteraciones_en_normal():
    p = PARAMS_DEFECTO["NORMAL"]
    A, b, x = construir_sistema(p)
    cg = resolver_todos(A, b, x, p["tol"], p["max_iter"])[4]
    assert cg["iteraciones"] <= p["n"]


def test_mal_condicionado():
    p = PARAMS_DEFECTO["MAL_CONDICIONADO"]
    A, b, x = construir_sistema(p)
    assert numero_condicion(A) > 1e6
    res = {r["metodo"]: r for r in resolver_todos(A, b, x, p["tol"], p["max_iter"])}
    assert not res["Jacobi"]["convergio"]          # diverge
    u = res["Gradiente Conjugado"]["historial"][-1]
    assert u["residual"] < 1e-10 and u["error_abs"] > u["residual"]   # residuo pequeño != error pequeño


def test_persistencia_reinicio(tmp_path):
    url = f"sqlite:///{tmp_path/'t.db'}"
    eng = db.get_engine(url, forzar=True)
    p = PARAMS_DEFECTO["NORMAL"]
    out = correr(p)
    sid = db.guardar_simulacion(eng, "Deterioro y mantenimiento", "NORMAL", p, "sintético",
                                a_ejecuciones(out, p, "texto"), equipo="test")
    eng.dispose()
    eng2 = db.get_engine(url, forzar=True)             # "reinicio" de la aplicación
    S = db.cargar_simulacion(eng2, sid)
    assert S["parametros_json"] == p and len(S["ejecuciones"]) == 5
    nuevo = correr(S["parametros_json"])
    for e, r in zip(S["ejecuciones"], nuevo["res"]):
        xg = np.array(e["resumen"]["valor_json"]["x"])
        assert np.max(np.abs(xg - r["x"])) < 1e-9
    assert not db.listar_simulaciones(eng2, caso="Deterioro y mantenimiento").empty
