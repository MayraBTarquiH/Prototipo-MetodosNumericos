"""Teoría de errores transversal (se usa en TODOS los módulos)."""
import numpy as np


def _v(x):
    return np.atleast_1d(np.asarray(x, dtype=float))


def error_absoluto(x_ref, x_aprox):
    """||x_ref - x_aprox||_2"""
    return float(np.linalg.norm(_v(x_ref) - _v(x_aprox)))


def error_relativo(x_ref, x_aprox):
    """||x_ref - x_aprox|| / ||x_ref||. Devuelve None si ||x_ref|| = 0 (sin dividir por cero)."""
    n = float(np.linalg.norm(_v(x_ref)))
    if n == 0.0:
        return None
    return error_absoluto(x_ref, x_aprox) / n


def error_porcentual(x_ref, x_aprox):
    r = error_relativo(x_ref, x_aprox)
    return None if r is None else 100.0 * r


def residuo(A, b, x):
    """||b - A x||_2"""
    return float(np.linalg.norm(_v(b) - np.asarray(A, float) @ _v(x)))


def residuo_relativo(A, b, x):
    nb = float(np.linalg.norm(_v(b)))
    return None if nb == 0.0 else residuo(A, b, x) / nb


def numero_condicion(A):
    """kappa_2(A)"""
    return float(np.linalg.cond(np.asarray(A, float), 2))


def sensibilidad(resolver, A, b, eps=1e-6, semilla=0):
    """Perturba b con un ruido relativo `eps` y mide cuánto cambia la solución.

    amplificacion = (||dx||/||x||) / (||db||/||b||)  <=  kappa(A)
    """
    rng = np.random.default_rng(semilla)
    b = _v(b)
    db = rng.standard_normal(len(b))
    db *= eps * np.linalg.norm(b) / np.linalg.norm(db)
    x = _v(resolver(A, b))
    xp = _v(resolver(A, b + db))
    cambio_rel_x = float(np.linalg.norm(xp - x) / np.linalg.norm(x))
    cambio_rel_b = float(np.linalg.norm(db) / np.linalg.norm(b))
    return {
        "eps": eps,
        "cambio_rel_b": cambio_rel_b,
        "cambio_rel_x": cambio_rel_x,
        "amplificacion": cambio_rel_x / cambio_rel_b,
        "cota_kappa": numero_condicion(A),
    }
