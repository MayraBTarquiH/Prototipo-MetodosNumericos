# DER y modelo relacional (SIMTELE-RISK)

Pega el bloque `mermaid` en https://mermaid.live para exportarlo como PNG/SVG para el informe.

```mermaid
erDiagram
    CASO_ESTUDIO ||--o{ ESCENARIO : "tiene"
    ESCENARIO ||--o{ SIMULACION : "se ejecuta en"
    SIMULACION ||--|{ EJECUCION_METODO : "contiene"
    EJECUCION_METODO ||--|{ ITERACION_RESULTADO : "registra"
    EJECUCION_METODO ||--|| RESULTADO_RESUMEN : "resume"

    CASO_ESTUDIO {
        int id PK
        varchar nombre UK
        varchar modelo_version
    }
    ESCENARIO {
        int id PK
        int caso_id FK
        varchar tipo "NORMAL | ESTRÉS | MAL_CONDICIONADO"
        jsonb parametros_json
        text fuente_datos
    }
    SIMULACION {
        int id PK
        int escenario_id FK
        timestamptz fecha
        varchar equipo
        varchar estado
    }
    EJECUCION_METODO {
        int id PK
        int simulacion_id FK
        varchar metodo
        float tolerancia
        float paso
        int max_iter
        boolean convergio
        float tiempo_ms
    }
    ITERACION_RESULTADO {
        int id PK
        int ejecucion_id FK
        int numero
        jsonb aproximacion_json
        float residual
        float error_abs
        float error_rel
    }
    RESULTADO_RESUMEN {
        int id PK
        int ejecucion_id FK
        text referencia
        jsonb valor_json
        jsonb metrica_error_json
        text interpretacion
    }
```

## Modelo relacional

- `caso_estudio(id PK, nombre UNIQUE, modelo_version)`
- `escenario(id PK, caso_id FK→caso_estudio, tipo CHECK, parametros_json, fuente_datos)`
- `simulacion(id PK, escenario_id FK→escenario, fecha, equipo, estado)`
- `ejecucion_metodo(id PK, simulacion_id FK→simulacion ON DELETE CASCADE, metodo, tolerancia, paso, max_iter, convergio, tiempo_ms)`
- `iteracion_resultado(id PK, ejecucion_id FK→ejecucion_metodo ON DELETE CASCADE, numero, aproximacion_json, residual, error_abs, error_rel)`
- `resultado_resumen(id PK, ejecucion_id FK→ejecucion_metodo ON DELETE CASCADE, referencia, valor_json, metrica_error_json, interpretacion)`

Nota: el DER de la consigna no incluye `usuario`; `equipo` es un campo opcional en `simulacion`.
Para ejecuciones con más de 500 iteraciones se guardan 500 iteraciones submuestreadas (incluye la primera y la última).
