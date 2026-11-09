---
name: q:fuzz
description: "Trigger: /q-fuzz, /fuzz, fuzzing, romper con fuzz, property testing, pruebas de fuzz. Generación acotada de entradas con semilla (herramienta tools/q-fuzz/q_fuzz.py, solo stdlib) para intentar romper funciones puras y convertir cada crash en un test reproductor en ROJO antes de autorizar el fix. Enganche: Paso 6 Fase A (consultivo, no bloqueante) y Paso 9 (fuente de tests RED_FAIL)."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "1.0.0"
  date: "2026-11-08"
  context_policy: "PROGRESSIVE"
  requires: ["tools/q-fuzz/q_fuzz.py", "target registrado"]
  produces: ["Fuzz report JSON", "RED reproducer"]
---

# q:fuzz v1.0 — Romper para Corregir (Fuzz Acotado)

## 1. Quick Bootstrap & Triggers
- **Propósito**: Encontrar lo que los tests no buscan. El fuzzer genera
  entradas hasta romper una función pura; cada crash se minimiza a un
  test reproductor en ROJO, y solo entonces se autoriza el fix
  (TDD reproduction-first, igual que el Paso 9).
- **El circuito completo**:
  `fuzzer → crash → minimiza → test ROJO → fix → test VERDE → re-fuzz`
- **Cuándo Aplica**:
  - En Paso 6 Fase A (compuerta de máquina), después de los unit tests,
    como paso **consultivo**. Nunca bloquea por "no encontró nada".
  - En Paso 9, como fuente de tests RED_FAIL, igual que un fallo de
    producción.
  - Bajo demanda explícita (`/q-fuzz --target <nombre>`).
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO fuzzear producción, bases de datos reales o servicios
    externos.** Solo funciones puras y locales.
  - ⛔ **PROHIBIDO correr sin presupuesto**: siempre `--budget` o
    `--iterations`. Un fuzz sin límite es un bucle infinito con gastos.
  - ⛔ **PROHIBIDO bloquear el merge por no encontrar crashes.** Solo
    bloquea un crash **sin triar** (ver sección 3).
  - No fuzzear UI, migraciones DDL ni código con efectos secundarios.

## 2. Invariantes Operativos No Negociables
1. **Determinismo acotado**: misma `--seed` + mismas `--iterations` =
   misma secuencia de entradas. La semilla queda registrada en cada
   reporte. Para reproducibilidad estricta se usa `--iterations`; el
   `--budget` es tiempo de pared y varía.
2. **Corpus persistido**: las entradas generadas se guardan en
   `tests/fuzz/corpus/<objetivo>/` y los crashes en `crash-<firma>.txt`.
   Lo interesante se queda y se re-corre siempre.
3. **Deduplicación antes del LLM**: los crashes se agrupan por firma
   (tipo de excepción + marco más profundo). El modelo solo tria una
   vez por firma; triar diez veces el mismo crash quema tokens.
4. **El reproductor es sagrado**: cada crash emite un archivo
   `tests/fuzz/repro/test_repro_<objetivo>_<firma>.py` que sale con
   código 2 mientras el bug existe (ROJO) y 0 cuando está corregido.
   Promoverlo a test de regresión permanente es parte del fix.
5. **Cero mocks**: el fuzzer ejecuta la función real contra entradas
   reales. Un crash inventado no cuenta.

## 3. Objetivos y Presupuesto
| Objetivo registrado | Función | Invariante |
| :--- | :--- | :--- |
| `merge-gate-shortstat` | `parse_shortstat()` en `tools/q-merge-gate` | Devuelve `(added, deleted)` enteros no negativos y nunca lanza excepciones. |

- **Presupuesto por defecto**: 60 s por objetivo en compuerta, 10 min en
  nightly. Empezar con 1 objetivo y 1 stack; Go nativo (`go test -fuzz`)
  queda como trabajo futuro documentado, no en este MVP (el código
  propio del repo es Python).
- **Candidatos futuros**: parsers, validadores, máquinas de estado,
  serializadores y cálculos (p. ej. motor de SLAs, cálculos HOMA-IR).
- **Regla de bloqueo**: un crash sin triar bloquea el merge (se registra
  como hallazgo R-ID en la revisión). "Sin crashes en 60 s" no bloquea
  nada y no es prueba de corrección.

## 4. Contrato de Ejecución
- [ ] **M1 (Elegir objetivo)**: debe estar registrado en
      `tools/q-fuzz/q_fuzz.py` (`list-targets`). Sin objetivo registrado,
      no hay fuzz: se registra primero, con su invariante.
- [ ] **M2 (Correr acotado)**:
      `python3 tools/q-fuzz/q_fuzz.py run --target merge-gate-shortstat --seed 1 --budget 60 --json`
- [ ] **M3 (Triar)**: por cada firma, una sola vez: ¿crash real o
      entrada inválida fuera del contrato? Si es entrada inválida,
      se documenta y se ajusta el generador, no la función.
- [ ] **M4 (RED → fix → re-fuzz)**: promover el reproductor a test de
      regresión, corregir, verificar VERDE, re-correr el fuzz con la
      misma semilla y registrar la evidencia en Terminal Evidence Gate.

## 5. Formato del Reporte
```json
{
  "tool": "q-fuzz", "target": "merge-gate-shortstat", "seed": 1,
  "inputs_tried": 500, "inputs_sha256": "<hash de la secuencia>",
  "crashes_found": 1,
  "crashes": [{"signature": "<12 hex>", "exception": "ValueError",
               "input": "<entrada>", "repro_file": "tests/fuzz/repro/..."}],
  "exit_code": 2
}
```
Exit codes: `0` sin crashes · `2` crash encontrado (reproductor escrito) ·
`1` error de uso / objetivo desconocido.
