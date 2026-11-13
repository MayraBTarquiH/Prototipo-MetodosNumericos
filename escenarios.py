"""Construcción reproducible de sistemas A x* = b para los escenarios del Módulo 2 (calibración)."""
import numpy as np

TIPOS = ("NORMAL", "ESTRÉS", "MAL_CONDICIONADO")
MATRICES = {
    "tridiagonal_dd": "Tridiagonal diagonalmente dominante SPD (4 en la diagonal, -1 fuera)",
    "poisson1d": "Poisson 1D SPD (2 en la diagonal, -1 fuera): converge lento en Jacobi/GS",
    "hilbert": "Hilbert SPD, kappa(A) enorme (mal condicionada)",
}

PARAMS_DEFECTO = {
    "NORMAL": {"matriz": "tridiagonal_dd", "n": 6, "tol": 1e-10, "max_iter": 1000, "eps_sens": 1e-6},
    "ESTRÉS": {"matriz": "poisson1d", "n": 40, "tol": 1e-12, "max_iter": 20000, "eps_sens": 1e-3},
    "MAL_CONDICIONADO": {"matriz": "hilbert", "n": 6, "tol": 1e-10, "max_iter": 5000, "eps_sens": 1e-10},
}


def construir_matriz(tipo, n):
    if tipo == "tridiagonal_dd":
        return 4.0 * np.eye(n) - np.eye(n, k=1) - np.eye(n, k=-1)
    if tipo == "poisson1d":
        return 2.0 * np.eye(n) - np.eye(n, k=1) - np.eye(n, k=-1)
    if tipo == "hilbert":
        i = np.arange(1, n + 1)
        return 1.0 / (i[:, None] + i[None, :] - 1.0)
    raise ValueError(f"Tipo de matriz desconocido: {tipo}")


def construir_sistema(params):
    """A, b = A x*, x* conocido. Determinista: mismos params -> mismo sistema."""
    n = int(params["n"])
    if n < 4:
        raise ValueError("La consigna exige n >= 4")
    A = construir_matriz(params["matriz"], n)
    x_star = np.arange(1, n + 1, dtype=float)
    b = A @ x_star
    return A, b, x_star
