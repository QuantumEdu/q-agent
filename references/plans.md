# Mapeo de Flujos ODD por Plan de Desarrollo
> Referencia Operativa del Orquestador q-agent v2.0 (Dual-Engine Architecture)
> Todas las rutas son relativas al paquete (`q-agent-v02/`).

---

## 🏛️ Matriz de Planes y Pipeline ODD

q-agent v2.0 unifica la rigurosidad de negocio con la agilidad técnica eliminando la burocracia de documentos fragmentados (`proposal.md`, `spec.md`, `tasks.md`), sustituyéndola por una **Bitácora Única ODD** y el **Artículo Constitucional ARQ-01**.

```
[Step 0: Selección de Plan (A, B, F, C)]
                  │
                  ▼
[Step 1-2: Contexto Guiado, Elicitación e Investigación]
                  │
                  ▼
[P03: Gate de Metaorquestación (Detección Gentle-AI vs Standalone)]
                  │
                  ▼
[P04: Bitácora Única ODD (BMAD User Stories + Tareas ~400 LOC)]
                  │
                  ▼
[P05: Vertical Slice Apply (Mínima Indirección + Higiene .html)]
                  │
                  ▼
[P06: Terminal Evidence Gate (Exit Code 0 obligatorio en terminal)]
                  │
                  ▼
[P07: Higiene Determinista y Consolidación en BLUEPRINT.md]
                  │
                  ▼
[P09: CAB-RP 2.0 Pre-Release Audit (Solo fin de ciclo / Plan C)]
```

---

## Plan A — Greenfield (Nuevo sistema desde cero)

Aplicable cuando se crea un proyecto nuevo sin código preexistente.

| Paso | Prompt / Plantilla | Artefacto Producido | Ubicación / Rama |
|---|---|---|---|
| **P00** | `templates/CONSTITUTION.md` | `CONSTITUTION.md` (con Artículo ARQ-01 y ADRs base) | Raíz del proyecto / `develop` |
| **P02** | `prompts/P02_context_engineering.md` | Contexto inicial y límites de módulos | Memoria / Internal |
| **P03** | `prompts/P03_gate_metaorquestacion.md` | Selección dinámica de Motor (Gentle-AI vs Standalone) | Salida en chat / logs |
| **P04** | `prompts/P04_odd_feature_log.md` | Bitácora ODD con BMAD User Stories y UAC | `q-tasks/<feature>.md` o `odd/tasks/<feature>.md` |
| **P05** | `prompts/P05_vertical_slice_apply.md` | Código del Slice (storage, handlers, templates .html) | `features/<modulo>/` |
| **P06** | `prompts/P06_terminal_evidence_gate.md` | Registro de exit code 0 y evidencia observable | En tabla de la bitácora activa |
| **P07** | `prompts/P07_hygiene_and_blueprint.md` | Linters limpios (0 tokens) + `BLUEPRINT.md` consolidado | Raíz del proyecto |

---

## Plan B — Brownfield (Feature / Evolución sobre código existente)

Aplicable al agregar funcionalidades o refactorizaciones sobre un repositorio vivo.

| Paso | Prompt / Plantilla | Artefacto Producido | Ubicación / Rama |
|---|---|---|---|
| **P01** | `prompts/P01_auditoria_mab_pc.md` | `BLUEPRINT.md` (por Slices) y `CONSTITUTION.md` inicial | Raíz del proyecto / `develop` |
| **P02** | `prompts/P02_context_engineering.md` | Análisis de blast radius e impacto | Internal context |
| **P03** | `prompts/P03_gate_metaorquestacion.md` | Confirmación de Motor y validación ARQ-01 | Salida de gate en chat |
| **P04** | `prompts/P04_odd_feature_log.md` | Bitácora ODD con Historias de Usuario BMAD | `q-tasks/<feature>.md` o `odd/tasks/<feature>.md` |
| **P05** | `prompts/P05_vertical_slice_apply.md` | Implementación de Slices Verticales (~400 LOC) | `features/<modulo>/` |
| **P06** | `prompts/P06_terminal_evidence_gate.md` | Verificación terminal obligatoria (cero fakes) | En tabla de la bitácora activa |
| **P07** | `prompts/P07_hygiene_and_blueprint.md` | Limpieza con linters y actualización de `BLUEPRINT.md` | Raíz del proyecto |

---

## Plan F — Fast-Track (Micro-parche o Bugfix quirúrgico en ≤3 archivos)

Aplicable para correcciones urgentes, ajustes de configuración o parches pequeños sin impacto en arquitectura ni modelos de base de datos.
- **Sin Bitácora Durable:** Resuelve directamente en sesión sin generar archivos markdown durables.
- **Protocolo Reproduction-First:**
  1. Escribir test que reproduzca la falla (Fase Roja obligatoria).
  2. Aplicar corrección quirúrgica en código fuente (Fase Verde).
  3. Ejecutar linters locales (0 tokens si pasa).
  4. Commit atómico: `fix: <descripción del error>`.

---

## Plan C — Audit (Auditoría Forense Atómica CAB-RP 2.0 & MAB-PC)

> **Principio de Oro:** *"Completeness is a filesystem property, not an LLM output property."*  
> Aplicable antes de cortes de versión, entrega a producción o evaluación de repositorios heredados.

### ⛔ Invariantes No Negociables del Plan C:
1. **Inmutabilidad Absoluta en Disco & Cero Modo Mixto (Audit + Fix):**
   - El auditor es 100% de solo lectura sobre el código del proyecto (`src/`, `internal/`, `cmd/`, `tests/`).
   - ⛔ **PROHIBIDO SALTAR A PLAN F:** Queda terminantemente prohibido modificar código, crear parches en caliente o intentar corregir errores antes de que la auditoría completa esté validada y certificada en disco. No se puede alternar entre auditor y desarrollador en la misma fase.
2. **Prohibición de Informes Monolíticos Generados por LLM:**
   - ⛔ **PROHIBIDO redactar `AUDIT_REPORT.md` a mano en el chat.** Todos los entregables son ensamblados deterministamente por herramientas a partir de los archivos de ítem en disco.

### 🔄 Pipeline de 5 Fases de Atomic Dispatch:

| Fase | Herramienta / Prompt | Entregable Producido | Ubicación / Comando |
|---|---|---|---|
| **C1. Discovery** | `prompts/P01_auditoria_mab_pc.md` | `CONSTITUTION.md` + `BLUEPRINT.md` | Raíz del proyecto / `audit/<date>` |
| **C2. Atomic Dispatch** | `prompts/P01b_audit_item.md` & `P01c_strategic_item.md` | Archivos atómicos `A01.md`–`A17.md` y `E01.md`–`E05.md` | `audit/A{ID}-{slug}.md` y `audit/E{ID}-{slug}.md` |
| **C3. Compuerta Mecánica (Gate)** | `tools/q-audit-validator/validate_audit.py` | `audit/AUDIT_GAPS.json` + Validación Exit 0 | `python3 tools/q-audit-validator/validate_audit.py --mode manifest --level [0\|1\|2]` |
| **C4. Agregación Determinista** | `tools/q-audit-aggregator/generate_report.py` | `AUDIT_REPORT.md`, `PLAN_DE_MEJORA.md`, `REMEDIATION_ISSUES.md`, `PROPUESTA_EVOLUTIVA.md` | `python3 tools/q-audit-aggregator/generate_report.py --level [0\|1\|2]` |
| **C5. Cierre** | `skills/q-session-wrap` | Registro en Engram/SkillVault + Reporte en Chat | Chat del orquestador |

### ⛔ Regla Dura de la Compuerta Mecánica (Fase C3):
- Si `validate_audit.py` retorna código de salida `1` (`RESULT: REJECTED — Audit items are incomplete`):
  El agente tiene **ESTRICTAMENTE PROHIBIDO** interactuar con el usuario o dar por concluida la auditoría. Debe leer `audit/AUDIT_GAPS.json` y regenerar los ítems faltantes hasta obtener `RESULT: PASSED` (Exit Code 0).

---

## Plan A-L — Greenfield Large (Features extensos con artefactos separados)

Variante opcional de Plan A para proyectos que superan **20 tareas** o **2 semanas de duración**, donde la frecuencia de cambio del *intent* difiere sustancialmente del avance diario de tareas.

| Artefacto | Frecuencia de Cambio | Propósito | Audiencia |
|---|---|---|---|
| `intent.md` | Muy baja (estable) | Objetivos de negocio, restricciones, personas y UAC base | Stakeholders y Agente |
| `spec.md` | Media (diseño) | Contratos de API, esquemas SQLite WAL, arquitectura de Slices | Desarrolladores y Agente |
| `odd/tasks/<feature>.md` | Alta (diaria) | Lista atómica de tareas vivas y tabla Terminal Evidence Gate | Agente ejecutor y Reviewer |

- **Regla:** Si la feature es acotada (≤20 tareas, ≤2 semanas), se mantiene el **Living Log Unificado** por defecto para evitar burocracia documental.

---

## Plan O — Ops Bridge (Remediación de Incidentes de Producción)

Activado mediante `/ops-bridge` o el prompt `prompts/P10_ops_to_odd.md`.

| Paso | Prompt / Plantilla | Artefacto Producido | Ubicación / Rama |
|---|---|---|---|
| **P10** | `prompts/P10_ops_to_odd.md` | Bitácora de corrección con telemetría de runtime inyectada | `odd/tasks/fix-*.md` o `q-tasks/` |
| **RED** | Test de reproducción | Test automatizado que falla demostrando el error de runtime | `features/<slice>/reproduction_test.go` |
| **P05/P06** | `prompts/P05_vertical_slice_apply.md` | Corrección quirúrgica y paso a verde con Terminal Evidence Gate | `features/<slice>/` |
| **P08** | `prompts/P08_deploy_gate.md` | Generación de `REVIEW.md` con verificación y autorización de deploy | Raíz del proyecto |

## Modos de Interacción del Orquestador

Configurables en `.q-agent.json` o seleccionables en el Paso 0:

1. **`supervised` (Supervisado por Compuertas — MODO POR DEFECTO):**
   - El agente opera de forma fluida pero se detiene obligatoriamente en 3 compuertas clave:
     - **Gate P03:** Selección del Motor y validación de Constitución.
     - **Gate P04:** Validación del alcance y Criterios de Aceptación UAC con el usuario.
     - **Gate P07/P09:** Validación de cierre e integración a ramas principales.
   - En cada compuerta, formula una sola pregunta concisa y espera respuesta.

2. **`interactive` (Mentor Didáctico / Pair Programming):**
   - El agente se detiene en cada paso (P01 al P07), explicando el fundamento conceptual (*Concepts > Code*) y solicitando confirmación para avanzar.

3. **`autonomous` (Desatendido / CI Pipeline):**
   - El agente ejecuta todas las fases de forma autónoma respetando los candados de seguridad y el Terminal Evidence Gate.
