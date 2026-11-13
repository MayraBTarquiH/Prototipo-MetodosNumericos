"""Definición de los 4 casos de estudio: modelo, métodos y escenarios (datos SINTÉTICOS, uso educativo)."""

CASOS = {
    "detencion": {
        "nombre": "Detención de emergencia", "icono": "🛑", "pagina": "pages/1_Detencion.py",
        "pregunta": "¿Cómo varían tiempo y distancia de detención frente a cambios de velocidad, tiempo de reacción y frenado?",
        "modelo": r"\frac{dx}{dt}=v,\quad \frac{dv}{dt}=-a(v,t)",
        "analitico": "a constante: v(t)=v0−a·t, x(t)=x0+v0·t−(a/2)t², t_det=v0/a, d_frenado=v0²/(2a).",
        "variables": "x [m] posición, v [m/s] velocidad, a [m/s²] desaceleración, t [s].",
        "metodos": ["RK2", "RK4", "Trapecio compuesto", "Simpson 1/3 compuesto", "Romberg", "Bisección", "Newton-Raphson", "Secante"],
        "escenarios": {
            "NORMAL": "v0 = 5 m/s, a = 1 m/s² constante, paso h = 0.05 s. Datos consistentes y paso adecuado.",
            "ESTRÉS": "v0 = 7 m/s, a = 0.5 m/s², tiempo de reacción 2 s y pasos h grandes (0.5 s) y pequeños (0.001 s).",
            "MAL_CONDICIONADO": "v(t)=v0(1−t/T)² tiene raíz doble en T: v'(T)=0, Newton pierde convergencia cuadrática.",
        },
        "estado": "Semana 2",
    },
    "deterioro": {
        "nombre": "Deterioro y mantenimiento", "icono": "🔧", "pagina": "pages/2_Deterioro.py",
        "pregunta": "¿Cuándo alcanzaría un indicador hipotético de deterioro un umbral de inspección?",
        "modelo": r"D(t)=D_0+\alpha t+\beta t^2,\qquad D(t^*)=D_{umbral}",
        "analitico": "Resolver la cuadrática β t²+α t+(D0−D_umbral)=0 y elegir la raíz positiva. Sistemas lineales: A x* = b con x* conocido y A SPD.",
        "variables": "D [adimensional] indicador, α [1/día], β [1/día²], t [días].",
        "metodos": ["Bisección", "Newton-Raphson", "Secante", "Jacobi", "Gauss-Seidel", "LU", "Gradiente Conjugado", "Trapecio/Simpson/Romberg (opcional)"],
        "escenarios": {
            "NORMAL": "Calibración con matriz SPD bien condicionada (n=6); raíz simple.",
            "ESTRÉS": "Sistema grande (n=40) y tolerancia 1e-12; mantenimiento retrasado (β mayor).",
            "MAL_CONDICIONADO": "Matriz de Hilbert (κ≈1e7): residuo pequeño pero error grande; umbral casi tangente (raíz casi doble).",
        },
        "estado": "Semana 1: sistemas lineales (activo)",
    },
    "oscilaciones": {
        "nombre": "Oscilaciones por viento", "icono": "🌬️", "pagina": "pages/3_Oscilaciones.py",
        "pregunta": "¿Cómo se modifica la oscilación ante cambios de fuerza externa, amortiguamiento y parámetros del modelo?",
        "modelo": r"x'=v,\quad v'=\frac{F(t)-c\,v-k\,x}{m}",
        "analitico": "F=0, subamortiguado: x(t)=e^{−ζω₀t}[C1 cos(ω_d t)+C2 sen(ω_d t)].",
        "variables": "x [m], v [m/s], m [kg], c [N·s/m], k [N/m], F [N], ζ=c/(2√(km)).",
        "metodos": ["RK2", "RK4", "Trapecio compuesto", "Simpson 1/3 compuesto", "Romberg", "Sistemas lineales auxiliares"],
        "escenarios": {
            "NORMAL": "ζ = 0.1, F(t) = 0 (vibración libre), paso h pequeño.",
            "ESTRÉS": "F(t)=F0·sen(Ωt) cerca de la resonancia, tiempo largo y paso grande (RK2 pierde estabilidad).",
            "MAL_CONDICIONADO": "ζ cercano a 1 (ω_d→0): la frecuencia amortiguada es muy sensible a pequeños cambios de c, k y m.",
        },
        "estado": "Semana 2",
    },
    "sensores": {
        "nombre": "Reconstrucción de sensores", "icono": "📡", "pagina": "pages/4_Sensores.py",
        "pregunta": "¿Cómo reconstruir registros faltantes y medir la distorsión que producen datos con ruido?",
        "modelo": r"y(t)=\sin t \ \ \text{o}\ \ y(t)=e^{-t}\ \ \text{(datos sintéticos)}",
        "analitico": "Se ocultan puntos de y(t) conocida y se compara la reconstrucción con el valor real.",
        "variables": "t [s] tiempo, y [u.a.] señal del sensor sintético.",
        "metodos": ["Lagrange", "Newton (diferencias divididas)", "Splines cúbicos", "Bisección/Newton/Secante (cruce de umbral)", "Sistemas lineales auxiliares"],
        "escenarios": {
            "NORMAL": "y=sen t, 8 nodos equiespaciados, sin ruido, puntos ocultos en el interior.",
            "ESTRÉS": "Ruido gaussiano σ=0.05, más nodos (20) y huecos más grandes.",
            "MAL_CONDICIONADO": "Nodos equiespaciados de alto grado en intervalo largo (fenómeno de Runge); matriz de Vandermonde con κ enorme.",
        },
        "estado": "Semana 2",
    },
}
