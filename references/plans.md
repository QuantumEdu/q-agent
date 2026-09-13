# Mapeo de flujo SDD por plan

Todas las rutas son relativas a la raíz de este paquete (`q-agent-v01/`).
Estructura de artefactos estándar: los cambios se alojan bajo `openspec/changes/{{CHANGE_ID}}/` (o en la raíz del repo para archivos globales como `CONSTITUTION.md` y `BLUEPRINT.md`).

---

## Plan A — Greenfield (sistema nuevo desde cero)

Ejecutar en orden estricto:

| Paso | Archivo de prompt | Artefacto producido | Rama Git |
|------|-------------------|---------------------|----------|
| P0 | `templates/CONSTITUTION.md` | `CONSTITUTION.md` (reglas base + tabla ADRs) | `main` / `develop` |
| P2 | `prompts/P02_context_engineering.md` | `CONTEXT.md` (viabilidad y hexagonal ligera) | `develop` |
| P4 | `prompts/P04_propose.md` | `openspec/changes/{{CHANGE_ID}}/proposal.md` | `develop` |
| P5 | `prompts/P05_spec.md` | `openspec/changes/{{CHANGE_ID}}/specs/{{FEATURE}}.md` | `feature/<name>` |
| P6 | `prompts/P06_design.md` | `openspec/changes/{{CHANGE_ID}}/design.md` | `feature/<name>` |
| P7 | `prompts/P07_tasks.md` | `openspec/changes/{{CHANGE_ID}}/tasks.md` | `feature/<name>` |
| P8 | `prompts/P08_apply_verify.md` | Código verificado + `verify-report.md` | `feature/<name>` |
| P1.5 / P04b | `prompts/P04b_constitution_sync.md` | `CONSTITUTION.md` (sync drift + log) | `develop` |

> P0 inicializa la Constitution antes de entrar al pipeline.
> P1 MAB-PC y P3 Evolución no aplican en Plan A (no hay código preexistente).

**Gate obligatorio:** después de P4 `/propose` — mostrar al usuario y esperar aprobación explícita.

---

## Plan B — Brownfield (feature / evolución sobre código existente)

Ejecutar en orden:

| Paso | Archivo de prompt | Artefacto producido | Rama Git |
|------|-------------------|---------------------|----------|
| P1 | `prompts/P01_auditoria_mab_pc.md` | `BLUEPRINT.md` + `CONSTITUTION.md` | `develop` |
| P2 | `prompts/P02_context_engineering.md` | `CONTEXT.md` | `develop` |
| P3 | `prompts/P03_evolucion_blueprint.md` | `BLUEPRINT_V2.md` + `DIFF_V1_VS_V2.md` | `develop` |
| P4 | `prompts/P04_propose.md` | `openspec/changes/{{CHANGE_ID}}/proposal.md` | `feature/<name>` |
| P5 | `prompts/P05_spec.md` | `openspec/changes/{{CHANGE_ID}}/specs/{{FEATURE}}.md` | `feature/<name>` |
| P6 | `prompts/P06_design.md` | `openspec/changes/{{CHANGE_ID}}/design.md` | `feature/<name>` |
| P7 | `prompts/P07_tasks.md` | `openspec/changes/{{CHANGE_ID}}/tasks.md` | `feature/<name>` |
| P8 | `prompts/P08_apply_verify.md` | Código verificado + `verify-report.md` | `feature/<name>` |
| P1.5 / P04b | `prompts/P04b_constitution_sync.md` | `CONSTITUTION.md` (sync drift + log) | `develop` |

**Gate obligatorio:** después de P4 `/propose`.

**Bifurcación Fast-Track (Nivel 1):** Si P4 clasifica el requerimiento como Nivel 1 (≤3 archivos, sin impacto en Dominio ni BD), deriva directamente a **P8 en modo Fast-Track** (test unitario + fix quirúrgico + commit atómico), saltando P5, P6 y P7.

**Etiquetas MAB-PC (P1):**
- `[OBSERVADO]` — comprobado en código real
- `[INFERIDO]` — deducido por convención
- `[CONFLICTO]` — contradicción entre fuentes; pasa a gate humano

---

## Plan C — Audit (revisar, auditar y diagnosticar)

Ejecutar en orden:

| Paso | Archivo de prompt | Artefacto producido | Rama Git |
|------|-------------------|---------------------|----------|
| P1 | `prompts/P01_auditoria_mab_pc.md` | `BLUEPRINT.md` + `CONSTITUTION.md` | `audit/<date>` |
| P9 (CAB-RP) | `prompts/P09_compliance_audit.md` | `AUDIT_REPORT.md` (matriz + specs EARS + plan P0/P1) | `audit/<date>` |
| Remediación | Generación de Issues GitHub | Issues creados por brecha con severidad | `audit/<date>` |

**No hay gate de scope ni implementación de código en Plan C.** El ciclo concluye con la entrega de `AUDIT_REPORT.md` y la creación de los Issues de remediación en GitHub.

**Invariantes de Auditoría P9:**
- Inmutabilidad absoluta en disco (`git status -s` idéntico al estado de partida).
- CodeGraph primero para análisis de dependencias y blast radius.
- Anti-Mock / Fake Data check: tolerancia cero a funcionalidades simuladas con stubs.

---

## Templates Canónicos

| Plantilla | Archivo |
|-----------|---------|
| Architecture Decision Record | `templates/ADR.md` |
| Blueprint del Sistema | `templates/BLUEPRINT.md` |
| Constitución Arquitectónica | `templates/CONSTITUTION.md` |
| Propuesta de Cambio (/propose) | `templates/PROPOSAL.md` |

---

## Nota de compatibilidad con ejecutores

El flujo es tool-agnostic por diseño. El executor (Codex / Antigravity / OpenCode / Pi) recibe los artefactos generados bajo `openspec/changes/{{CHANGE_ID}}/` como contexto de entrada delimitado sin dependencias propietarias.
