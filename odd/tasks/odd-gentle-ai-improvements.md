# Bitácora de Feature ODD: odd-gentle-ai-improvements
> Documento vivo unificado de desarrollo — Gobernado por el protocolo Organic Driven Development (ODD).
> Ruta canónica: `odd/tasks/odd-gentle-ai-improvements.md`.

| Metadato | Valor |
|---|---|
| **Feature ID** | `ODD-GA-01` |
| **Fecha de inicio** | `2026-11-15` |
| **Motor de Ejecución** | q-agent Standalone / Gentle-AI Integrated ODD |
| **Arquitecto / Agente** | Quantum / Senior Architect |
| **Estado Global** | VERIFICADO |

---

## 1. MOTIVACIÓN Y VALOR

### Problema y Oportunidad
`q-agent` tomó como referencia conceptual a Gentle-AI para ODD y flujos adaptativos. Tras auditar Gentle-AI v4.5.0 (post-retiro total de SDD), se identificaron cinco avances críticos de ingeniería determinista en ODD:
1. **Resume Test:** Regla objetiva para sizing de tareas pequeñas vs grandes (si se puede retomar con el diff solo, corre inline sin bitácora).
2. **Spec by Reference (`S#` y `## Log`):** Eliminar el parafraseo de requerimientos al delegar en subagentes; workers leen la bitácora directamente hasta el Log verbatim.
3. **Declaración Explícita de Ruta:** Registro de `Route: inline | delegated` en cada tarea para visibilidad de delegación.
4. **Spec-Derived Probes:** Pruebas independientes derivadas de la especificación ejecutadas en aislamiento (`mktemp -d`), previniendo que los tests del escritor perpetúen bugs.
5. **Trazabilidad de Commit SHA:** Vinculación del hash de commit convencional en el checklist de tareas.

Integrar estos avances en `q-agent` eleva la precisión, elimina overhead documental y fortalece la compuerta de verificación sin alterar la gobernanza constitucional ARQ-01 ni las oleadas por dependencias.

---

## 2. ESPECIFICACIONES CONSTITUCIONALES (S#)

- **S-01 (Resume Test para Sizing):** Formalizar el criterio: una tarea es *pequeña* si está entendida (presupuesto inline), riesgo acotado y pasa el *Resume Test* (resumable únicamente desde el pedido y `git diff`). Tareas pequeñas corren inline sin bitácora. Solo las tareas grandes crean bitácora.
- **S-02 (Spec by Reference en Plantilla y Contrato):** `templates/task-log-template.md` debe incluir sección de especificaciones numeradas `S#` y sección final `## Log` con el requerimiento verbatim (`L1`) y correcciones posteriores. Al despachar subagentes, la orden es por referencia (`Spec: q-tasks/<feature>.md, T2, S1-S2`), prohibiendo el parafraseo.
- **S-03 (Declaración de Ruta y Trazabilidad de Commits):** Cada tarea en la bitácora declara `Ruta: [inline | delegated]` con trigger, y al completarse registra el commit: `- [x] TASK-XX (Commit: <sha>)`.
- **S-04 (Spec-Derived Probes en Verificación Dual):** Actualizar `SKILL.md`, `prompts/P06_terminal_evidence_gate.md` y `skills/q-adversarial-review/SKILL.md` para exigir que la verificación no se limite a reejecutar los tests del escritor; debe formular probes ciegos en aislamiento (`mktemp -d`) y convertirlos en tests de regresión duraderos.
- **S-05 (Sincronización Dual-Engine y Versionado):** Actualizar `references/dual-engine.md`, mantener integridad de suites y documentar en `CHANGELOG.md`.

---

## 3. CHECKLIST DE TAREAS ATÓMICAS EN OLEADAS

### 🌊 Wave 1: Plantilla Viva y Contrato de Bitácora
- [x] **TASK-01 (Commit: 9eb066d) [Wave 1] [S-01, S-02, S-03] [Ruta: inline] — Actualizar templates/task-log-template.md:**
  - *Archivos:* `templates/task-log-template.md`
  - *Acción:* Incorporar Resume Test, sección `S#`, sección `## Log`, campos `Ruta: [inline | delegated]` y trazabilidad de `Commit: <sha>`.
  - *Verificación prevista:* Inspección sintáctica y pruebas unitarias de templates.

### 🌊 Wave 2: Orquestador Central y Prompts del Pipeline
- [x] **TASK-02 (Commit: 9eb066d) [Wave 2] [S-01, S-02, S-03, S-04] [Ruta: inline] — Actualizar SKILL.md y Prompts ODD (P04 y P06):**
  - *Archivos:* `SKILL.md`, `prompts/P04_odd_feature_log.md`, `prompts/P06_terminal_evidence_gate.md`
  - *Acción:* Integrar Resume Test en Pasos 0/4, Spec by Reference en Pasos 4/5, Route declaration y Spec-Derived Probes en Paso 6.
  - *Verificación prevista:* `just test` exit 0.

### 🌊 Wave 3: Revisión Adversarial, Dual-Engine Reference y Changelog
- [x] **TASK-03 (Commit: 9eb066d) [Wave 3] [S-04, S-05] [Ruta: inline] — Actualizar q-adversarial-review, dual-engine.md y CHANGELOG.md:**
  - *Archivos:* `skills/q-adversarial-review/SKILL.md`, `references/dual-engine.md`, `CHANGELOG.md`
  - *Acción:* Reforzar eje de pruebas con Spec-Derived Probes, documentar paridad Gentle-AI v4.5.0 y registrar cambios en CHANGELOG.md.
  - *Verificación prevista:* `just test` exit 0.

---

## 4. TERMINAL EVIDENCE GATE

| Wave | Tarea ID | Comando Ejecutado en Terminal | Código de Salida (Exit Code) | Resultado Observado / Evidencia | Estado |
|---|---|---|---|---|---|
| W1 | TASK-01 | `python3 -m unittest tests/test_skill_integrity.py tests/test_communication_policy.py` | 0 | `Ran 22 tests in 0.004s - OK` | PASS |
| W2 | TASK-02 | `python3 -m unittest tests/test_skill_integrity.py` | 0 | `Ran 8 tests - OK` | PASS |
| W3 | TASK-03 | `just test` | 0 | `Ran 245 tests in 20.223s - OK` | PASS |

---

## 5. LOG DE CAMBIOS Y CORRECCIONES (L#)
- **L1:** Requerimiento inicial del usuario: "adelante con la implementacion" tras acordar las 5 mejoras derivadas de la auditoría de Gentle-AI v4.5.0.
