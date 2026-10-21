# Evaluación Local de q-agent bajo Metodología Harness²

## 1. Visión General & Fundamentos

Este documento certifica los resultados de la primera etapa de evaluación contrastiva de **q-agent** utilizando la metodología de **Harness²** ([arXiv:2610.14224](https://arxiv.org/abs/2610.14224), Google Research).

A diferencia de los benchmarks sintéticos que evalúan modelos sobre problemas aislados, Harness² evalúa el **arnés** que envuelve al modelo: instrucciones, herramientas, memoria, compuertas de calidad y trazabilidad.

En esta suite local, evaluamos sesiones del **CLI de OpenAI Codex** (`codex-cli`) comparando:
- **Baseline:** Instrucciones mínimas directas sin especificación ODD ni estructura de tareas.
- **q-agent:** Instrucciones completas de `q-agent` con especificación formal ODD, compuertas de calidad terminal, pruebas inmutables y trazabilidad en `odd/tasks/`.

---

## 2. Disciplina Experimental

Para evitar sesgos y mediciones ilusorias:
1. **Fixtures Idénticos y Tests Inmutables:** Los tests de verificación están congelados mediante hashes SHA-256. El evaluador falla inmediatamente si el agente altera los tests.
2. **Cero Mocks:** Todas las pruebas interactúan con bases de datos SQLite reales en modo WAL y llaves foráneas habilitadas.
3. **Sesiones Efímeras:** En las pruebas de recuperación de contexto, cada invocación se ejecuta mediante `codex exec --ephemeral` sin historial de conversación persistente; el único contexto disponible es el repositorio.
4. **Revisión Adversarial Aislada:** Los diffs funcionales generados por el agente son sometidos a un revisor independiente para detectar artefactos espurios, inconsistencias de tipo o brechas de seguridad antes de otorgar el veredicto `APPROVED`.

---

## 3. Matriz de Resultados

| Fase | Evaluador | Tarea Principal | Baseline | q-agent | Veredicto |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Prototipo Base** | [`evaluator.py`](../../evals/harness2/evaluator.py) | Flujo estricto de tickets SQLite (OPEN->CLOSED), SLAs y WAL. | 3/3 tests passed (Exit 0) | 3/3 tests passed (Exit 0) | **APROBADO** (Diff limpio de 28 líneas aprobado por revisor independiente). |
| **2. Stress Testing** | [`stress_evaluator.py`](../../evals/harness2/stress_evaluator.py) | **Tarea A:** Multi-tenant workflow, RBAC y auditoría.<br>**Tarea B:** Migración idempotente de esquemas legacy con rollback. | Tarea A: 3/3 passed<br>Tarea B: 2/2 passed | Tarea A: 3/3 passed<br>Tarea B: 2/2 passed | **APROBADO**. q-agent corrigió autónomamente un defecto sutil de datetimes (naive vs. aware) en su 2da vuelta de corrección acotada. |
| **3. Concurrencia y Lock Contention** | [`concurrency_evaluator.py`](../../evals/harness2/concurrency_evaluator.py) | Carrera atómica de reclamo (`claim_ticket` con 10 threads) y ráfaga de 20 threads bajo SQLite WAL sin bloqueos. | 2/2 passed (0.070s) | 2/2 passed (0.041s) | **APROBADO (2/2)**. q-agent aplicó compare-and-swap SQL atómico (`rowcount == 1`), `timeout=15.0` y revisión adversarial aprobada. |
| **4. Context Recovery** | [`recovery_evaluator.py`](../../evals/harness2/recovery_evaluator.py) | Continuidad entre sesiones efímeras sin chat: Slice A, Slice B y reparación de regresión C. | Slice A: OK<br>Slice B: OK<br>Slice C: OK | Slice A: OK<br>Slice B: OK<br>Slice C: OK | **APROBADO (6/6)**. q-agent reparó quirúrgicamente la regresión de SLA sin rollback destructivo del trabajo previo. |
| **5. Benchmark Oficial JobBench** | `harness2 --bench jb` | Tarea profesional completa de soporte técnico y redes (`computer_user_support_specialists/task1`) bajo ciclo recursivo Propose–Probe–Compose. | Base: 1/1 completado | Refinado (`agg1`): **89.29%** | **APROBADO (31/32 criterios)**. El framework confirmó que el arnés compuesto superó a la base (`chosen_is_base: false`) con costo de $0.24 USD. |

---

## 4. Evidencia Cualitativa Destacada

### Autocorrección Acotada (Stress Evaluation)
Durante la implementación del workflow multi-tenant, un revisor adversarial detectó que la comparación de fechas fallaba ante combinaciones de datetimes naive y timezone-aware. `q-agent` activó su protocolo de corrección acotada (máximo 2 rondas) y generó la solución normalizada sin intervención humana, pasando tanto el CI como la revisión independiente.

### Resistencia a la Amnesia Contextual (Context Recovery)
En la fase C de recuperación de contexto, se inyectó deliberadamente una regresión en la constante `CRITICAL` (modificándola de 2 a 24 horas). En una sesión completamente nueva y sin memoria conversacional:
- Un agente ingenuo suele ejecutar `git checkout` o revertir el archivo completo, perdiendo todo el código no commiteado de los Slices A y B.
- `q-agent` inspeccionó `odd/tasks/context-recovery.md`, correlacionó los fallos de CI con el contrato de Git HEAD, aisló la constante y aplicó una corrección quirúrgica, manteniendo intacto el progreso previo y verificando los hashes de los tests.

---

## 5. Cómo Reproducir las Evaluaciones

Desde la raíz del repositorio de `q-agent`:

```bash
# 1. Prototipo funcional base
python3 evals/harness2/evaluator.py

# 2. Stress evaluation (Multi-tenancy y migración)
python3 evals/harness2/stress_evaluator.py

# 3. Concurrencia y Lock Contention (Race conditions y ráfagas WAL)
python3 evals/harness2/concurrency_evaluator.py

# 4. Context recovery entre sesiones efímeras
python3 evals/harness2/recovery_evaluator.py
```

Los reportes y trazas completas se escriben automáticamente en `evals/harness2/runs/`, `evals/harness2/stress_runs/`, `evals/harness2/concurrency_runs/` y `evals/harness2/recovery_runs/`.

---

## 6. Ejecución del Benchmark Oficial JobBench

Para ejecutar y validar contra el dataset oficial de Hugging Face bajo el framework Harness² con DeepSeek:

```bash
# Sweep adaptativo Propose–Probe–Compose (agg1)
python3 -m harness2.cli.sweep --bench jb --substrate oc --k 1 --tasks computer_user_support_specialists/task1 --modes parallel

# Inspección del reporte de adopción oficial
python3 -m harness2.cli.report --bench jb --substrate oc --k 1 --modes parallel
```

- **Puntaje alcanzado:** 89.29% (31/32 criterios aprobados).
- **Adopción:** `chosen_is_base: false` (el arnés compuesto refinado superó a la base con costo de $0.24 USD).
- **Referencia del framework:** [`QuantumEdu/harness2`](https://github.com/QuantumEdu/harness2).
