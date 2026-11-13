# 🚡 SIMTELE-RISK — Desafío integrador de Métodos Numéricos

Aplicación web (Streamlit) con 4 casos de estudio inspirados en un sistema de transporte por cable.
**Uso estrictamente educativo: datos sintéticos, sin conexión con equipos reales.**

**Integrantes:** _(nombres)_ · **Mención:** _(mención)_ · **App:** _(enlace de Streamlit Cloud)_

## Estado (Semana 1)
| Módulo | Estado |
|---|---|
| Inicio con 4 tarjetas | ✅ |
| Teoría de errores (absoluto, relativo, %, residual, sensibilidad, κ) | ✅ `core/errores.py` |
| Sistemas lineales: directa, LU, Jacobi, Gauss-Seidel, Gradiente Conjugado | ✅ `core/sistemas_lineales.py` |
| Módulo 2 Deterioro: 3 escenarios (NORMAL, ESTRÉS, MAL CONDICIONADO) de calibración | ✅ |
| Módulos 1, 3, 4 | prototipo visible (modelo y escenarios definidos); implementación en Semana 2 |
| Base de datos + historial + relanzar | ✅ |

## Estructura
```
app.py                  Inicio
pages/                  1_Detencion, 2_Deterioro, 3_Oscilaciones, 4_Sensores, 5_Historial
core/errores.py         Teoría de errores transversal
core/sistemas_lineales.py  Métodos (programados a mano)
core/escenarios.py      Matrices y escenarios reproducibles
core/db.py              Tablas (SQLAlchemy) + guardar/cargar
core/casos.py           Definición de los 4 casos
db/schema_postgres.sql  Script SQL (PostgreSQL)
docs/DER.md             DER (Mermaid) y modelo relacional
tests/                  pytest (incluye prueba guardar → reiniciar → recuperar)
```

## Ejecutar en local
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Sin configurar nada, usa SQLite local (`data/simtele_local.db`). Pruebas: `python -m pytest -q`.

## Base de datos en la nube (necesaria en Streamlit Community Cloud)
Streamlit Cloud borra los archivos locales al reiniciar, por eso se usa PostgreSQL externo (Supabase o Neon).
1. Crea un proyecto en Supabase o Neon.
2. En su **SQL Editor** pega y ejecuta `db/schema_postgres.sql`.
3. Copia `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` y llena tus datos (local), o pega el contenido en
   **Streamlit Cloud → Settings → Secrets**.
4. Reinicia la app. En la barra lateral debe decir `Base de datos: postgresql`.

## Despliegue
1. Sube el repo a GitHub (el `.gitignore` ya excluye los secretos).
2. https://share.streamlit.io → *Create app* → repo, rama `main`, archivo `app.py`.
3. En *Advanced settings* → Secrets pega la configuración de la BD.

## Prueba de persistencia (para la defensa)
Deterioro → elegir escenario → Ejecutar → pestaña Interpretación → **Guardar** → reiniciar/actualizar la app →
**Historial** → abrir la simulación → **Repetir el cálculo** → debe mostrar ✅ en todos los métodos.
