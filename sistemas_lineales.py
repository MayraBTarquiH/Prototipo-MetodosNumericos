"""Sistemas lineales A x = b: referencia directa, LU, Jacobi, Gauss-Seidel y Gradiente Conjugado.
Todos los métodos están programados a mano (NumPy solo para productos matriz-vector y la referencia)."""
from time import perf_counter
import numpy as np
from .errores import error_absoluto, error_relativo, residuo, numero_condicion


# ---------------------------------------------------------------- diagnósticos
def es_simetrica(A, tol=1e-12):
    return bool(np.allclose(A, A.T, atol=tol))


def es_spd(A):
    if not es_simetrica(A):
        return False
    try:
        np.linalg.cholesky(A)
        return True
    except np.linalg.LinAlgError:
        return False


def es_diag_dominante(A):
    d = np.abs(np.diag(A))
    resto = np.abs(A).sum(axis=1) - d
    return bool(np.all(d > resto))


def radio_espectral_jacobi(A):
    D = np.diag(np.diag(A))
    T = -np.linalg.inv(D) @ (A - D)
    return float(max(abs(np.linalg.eigvals(T))))


def radio_espectral_gs(A):
    DL = np.tril(A)
    U = np.triu(A, 1)
    T = -np.linalg.inv(DL) @ U
    return float(max(abs(np.linalg.eigvals(T))))


def diagnostico(A):
    return {
        "n": int(A.shape[0]),
        "kappa": numero_condicion(A),
        "simetrica": es_simetrica(A),
        "spd": es_spd(A),
        "diag_dominante": es_diag_dominante(A),
        "rho_jacobi": radio_espectral_jacobi(A),
        "rho_gauss_seidel": radio_espectral_gs(A),
    }


# ---------------------------------------------------------------- utilidades
def _reg(k, x, A, b, x_ref):
    return {
        "numero": k,
        "aproximacion": x.tolist(),
        "residual": residuo(A, b, x),
        "error_abs": error_absoluto(x_ref, x),
        "error_rel": error_relativo(x_ref, x),
    }


def _resultado(metodo, x, hist, conv, motivo, t0, tol, max_iter, extra=None):
    return {
        "metodo": metodo, "x": x, "iteraciones": hist[-1]["numero"], "convergio": bool(conv),
        "motivo_parada": motivo, "historial": hist, "tiempo_ms": (perf_counter() - t0) * 1000,
        "tolerancia": tol, "max_iter": max_iter, "extra": extra or {},
    }


# ---------------------------------------------------------------- referencia directa
def referencia_directa(A, b, x_ref):
    t0 = perf_counter()
    x = np.linalg.solve(A, b)
    return _resultado("Directa (numpy.linalg.solve)", x, [_reg(1, x, A, b, x_ref)], True,
                      "método directo", t0, None, None)


# ---------------------------------------------------------------- LU con pivoteo parcial
def lu_factorizar(A):
    """P A = L U (Doolittle con pivoteo parcial)."""
    U = np.array(A, dtype=float)
    n = len(U)
    L = np.eye(n)
    P = np.arange(n)
    for k in range(n - 1):
        p = k + int(np.argmax(np.abs(U[k:, k])))
        if abs(U[p, k]) < 1e-300:
            raise ValueError("Matriz singular")
        if p != k:
            U[[k, p]] = U[[p, k]]
            P[[k, p]] = P[[p, k]]
            L[[k, p], :k] = L[[p, k], :k]
        for i in range(k + 1, n):
            L[i, k] = U[i, k] / U[k, k]
            U[i, k:] -= L[i, k] * U[k, k:]
            U[i, k] = 0.0
    if abs(U[n - 1, n - 1]) < 1e-300:
        raise ValueError("Matriz singular")
    return P, L, U


def lu_resolver(A, b, x_ref=None):
    t0 = perf_counter()
    P, L, U = lu_factorizar(A)
    n = len(b)
    pb = np.asarray(b, float)[P]
    y = np.zeros(n)
    for i in range(n):                      # sustitución hacia adelante
        y[i] = pb[i] - L[i, :i] @ y[:i]
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):          # sustitución hacia atrás
        x[i] = (y[i] - U[i, i + 1:] @ x[i + 1:]) / U[i, i]
    ref = x if x_ref is None else x_ref
    return _resultado("LU (pivoteo parcial)", x, [_reg(1, x, A, b, ref)], True,
                      "método directo", t0, None, None, extra={"P": P.tolist(), "L": L, "U": U})


# ---------------------------------------------------------------- iterativos
def _iterativo(nombre, paso, A, b, x_ref, tol, max_iter):
    t0 = perf_counter()
    n = len(b)
    x = np.zeros(n)
    nb = float(np.linalg.norm(b)) or 1.0
    hist = [_reg(0, x, A, b, x_ref)]
    conv, motivo = False, "se alcanzó max_iter sin cumplir la tolerancia"
    for k in range(1, max_iter + 1):
        x = paso(x)
        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 1e100:
            conv, motivo = False, "DIVERGE (valores no finitos o |x| > 1e100)"
            x = np.array(hist[-1]["aproximacion"])
            break
        reg = _reg(k, x, A, b, x_ref)
        hist.append(reg)
        if reg["residual"] / nb < tol:
            conv, motivo = True, "||b-Ax||/||b|| < tol"
            break
    return _resultado(nombre, x, hist, conv, motivo, t0, tol, max_iter)


def jacobi(A, b, x_ref, tol=1e-8, max_iter=1000):
    A = np.asarray(A, float)
    D = np.diag(A)
    if np.any(D == 0):
        raise ValueError("Jacobi requiere diagonal sin ceros")
    R = A - np.diag(D)
    return _iterativo("Jacobi", lambda x: (b - R @ x) / D, A, b, x_ref, tol, max_iter)


def gauss_seidel(A, b, x_ref, tol=1e-8, max_iter=1000):
    A = np.asarray(A, float)
    n = len(b)
    if np.any(np.diag(A) == 0):
        raise ValueError("Gauss-Seidel requiere diagonal sin ceros")

    def paso(x):
        x = x.copy()
        for i in range(n):
            x[i] = (b[i] - A[i, :i] @ x[:i] - A[i, i + 1:] @ x[i + 1:]) / A[i, i]
        return x

    return _iterativo("Gauss-Seidel", paso, A, b, x_ref, tol, max_iter)


def gradiente_conjugado(A, b, x_ref, tol=1e-8, max_iter=1000):
    """CG estándar: SOLO garantiza convergencia si A es simétrica definida positiva."""
    A = np.asarray(A, float)
    t0 = perf_counter()
    n = len(b)
    spd = es_spd(A)
    x = np.zeros(n)
    r = np.array(b, float)
    p = r.copy()
    rs = r @ r
    nb = float(np.linalg.norm(b)) or 1.0
    hist = [_reg(0, x, A, b, x_ref)]
    conv, motivo = False, "se alcanzó max_iter sin cumplir la tolerancia"
    for k in range(1, max_iter + 1):
        Ap = A @ p
        pAp = p @ Ap
        if pAp <= 0:
            motivo = "p^T A p <= 0: A no es definida positiva"
            break
        alpha = rs / pAp
        x = x + alpha * p
        r = r - alpha * Ap
        reg = _reg(k, x, A, b, x_ref)
        hist.append(reg)
        if reg["residual"] / nb < tol:
            conv, motivo = True, "||b-Ax||/||b|| < tol"
            break
        rs_new = r @ r
        if rs_new == 0:
            conv, motivo = True, "residuo recurrente = 0"
            break
        p = r + (rs_new / rs) * p
        rs = rs_new
    return _resultado("Gradiente Conjugado", x, hist, conv, motivo, t0, tol, max_iter,
                      extra={"A_es_SPD": spd})


def resolver_todos(A, b, x_star, tol=1e-8, max_iter=1000):
    """Ejecuta los cinco métodos y devuelve la lista de resultados."""
    return [
        referencia_directa(A, b, x_star),
        lu_resolver(A, b, x_star),
        jacobi(A, b, x_star, tol, max_iter),
        gauss_seidel(A, b, x_star, tol, max_iter),
        gradiente_conjugado(A, b, x_star, tol, max_iter),
    ]
