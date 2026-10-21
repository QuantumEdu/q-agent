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
| **3. Context Recovery** | [`recovery_evaluator.py`](../../evals/harness2/recovery_evaluator.py) | Continuidad entre sesiones efímeras sin chat: Slice A, Slice B y reparación de regresión C. | Slice A: OK<br>Slice B: OK<br>Slice C: OK | Slice A: OK<br>Slice B: OK<br>Slice C: OK | **APROBADO (6/6)**. q-agent reparó quirúrgicamente la regresión de SLA sin rollback destructivo del trabajo previo. |

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

# 3. Context recovery entre sesiones efímeras
python3 evals/harness2/recovery_evaluator.py
```

Los reportes y trazas completas se escriben automáticamente en `evals/harness2/runs/`, `evals/harness2/stress_runs/` y `evals/harness2/recovery_runs/`.
