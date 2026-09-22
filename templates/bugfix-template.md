# Especificación Quirúrgica de Bugfix: {{BUG_ID}} — {{BUG_TITLE}}
> Artefacto Operativo de Reparación Rápida (Plan F / Fast-Track) — q-agent
> Regla de Oro: Mínima intervención (≤3 archivos), Reproduction-First obligatorio y Cero Regresiones.

| Metadato | Valor |
|---|---|
| **Bug ID** | `{{BUG_ID}}` |
| **Severidad** | [CRITICAL / HIGH / MEDIUM / LOW] |
| **Módulo Afectado** | `{{AFFECTED_MODULE}}` |
| **Fecha de Detección** | `{{YYYY-MM-DD}}` |
| **Estado** | [DIAGNOSTICADO / REPRODUCIDO_ROJO / REPARADO_VERDE / CERRADO] |

---

## 1. 🔍 DEFECTO OBSERVADO (Observed Defect)

### Descripción del Comportamiento Anómalo
[Descripción concisa del fallo técnico, excepción o inconsistencia de datos observada.]

### Pasos Exactos de Reproducción
1. [Paso 1: Configuración o estado previo]
2. [Paso 2: Comando, llamada API o acción del usuario]
3. [Paso 3: Falla observada]

### Evidencia de Terminal (Traceback / Salida de Error)
```text
[Pegar aquí la salida real del comando o stack trace sin mocks]
```

---

## 2. 🎯 COMPORTAMIENTO ESPERADO (Expected Target — EARS Spec)

- **WHEN:** [Evento disparador o invocación exacta]
- **THE SYSTEM SHALL:** [Respuesta o mutación esperada del sistema]
- **AND SHALL NOT:** [Efecto secundario no deseado a evitar]

---

## 3. 🛡️ INVARIANTES INTACTOS / NO-REGRESIÓN (Unchanged Invariants)

> ⚠️ **CANDADO DE PREVENCIÓN DE REGRESIONES:**
> Esta lista delimita los contratos que NO deben ser modificados durante la reparación. Cualquier alteración colateral en estos puntos invalida el fix.

1. **Contrato de API / Interfaz:** `[ej. Firmas de métodos existentes o endpoints]` no sufren breaking changes.
2. **Esquema de Base de Datos:** `[ej. No se agregan campos obligatorios sin default ni se alteran tipos]`.
3. **Flujos Adyacentes:** `[ej. Los usuarios no autenticados siguen recibiendo HTTP 401]`.

---

## 4. 🔴 TEST REPRODUCTOR MANDATORIO (Reproduction-First RED Phase)

> ⛔ **CANDADO REPRODUCTION-FIRST:**
> Queda estrictamente prohibido modificar código productivo sin haber creado y ejecutado primero este test reproductor demostrando la falla en rojo (`RED_FAIL`).

- **Archivo del Test:** `[tests/.../test_bug_{{BUG_ID}}.py / .go / .ts]`
- **Comando de Ejecución:** `[ej. python3 -m unittest tests/test_bug_{{BUG_ID}}.py]`
- **Resultado en Rojo Observado (Fase Roja):**
```text
[Pegar aquí el resultado de terminal demostrando el fallo inicial]
```

---

## 5. 🛠️ PLAN DE REPARACIÓN QUIRÚRGICA (Máximo 3 archivos)

- [ ] **FIX-01 — [Archivo principal a corregir]:**
  - *Ruta:* `[ruta/al/archivo.ext]`
  - *Acción:* [Corrección puntual de la causa raíz]
- [ ] **FIX-02 — [Ajuste de validación o contrato colateral si aplica]:**
  - *Ruta:* `[ruta/al/archivo_secundario.ext]`
  - *Acción:* [Corrección de soporte]

---

## 6. 🟢 TERMINAL EVIDENCE GATE (Fase Verde Verificada)

> El candado se levanta únicamente cuando el test reproductor pasa a verde (`PASS`) y la suite completa del proyecto se ejecuta sin advertencias ni regresiones.

| Tarea ID | Comando Ejecutado en Terminal | Código de Salida (Exit Code) | Resultado Observado / Evidencia | Estado |
|---|---|---|---|---|
| `REPRO` | `[Comando del test reproductor]` | `0` | `OK (1 test passed)` | `[VERIFICADO]` |
| `SUITE` | `[Comando suite general del repo]` | `0` | `All tests passed - 0 failures` | `[VERIFICADO]` |
| `LINT`  | `[Comando linter / type check]` | `0` | `Clean - 0 errors` | `[VERIFICADO]` |
