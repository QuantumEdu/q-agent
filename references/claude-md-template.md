# Template CLAUDE.md por tipo de proyecto

El agente genera este archivo en el raíz del repositorio del proyecto.
Adaptar las secciones según el plan activo y el executor elegido.

---

## Template base (todos los planes)

```markdown
# CLAUDE.md — [NOMBRE DEL PROYECTO]

> Generado por q-agent · Plan [A/B/C] · [fecha]

## Identidad del proyecto

**Problema que resuelve:** [descripción del Paso 1]
**Usuario final:** [del Paso 1, si Plan A]
**Constraint crítico:** [del grill-me, si Plan A]
**Executor activo:** [Codex / Antigraviti / OpenCode / Pi]

---

## Contexto de arquitectura

[Contenido de CONTEXT.md generado en P2]
[Si Plan B/C: resumen de BLUEPRINT.md de P1]

---

## Estado actual del ciclo

| Item | Estado |
|------|--------|
| Plan activo | [A/B/C] |
| Paso actual | [número] |
| Rama activa | [nombre] |
| Issue de estado | #[número] |
| Última decisión | [ADR-XXX] |

---

## Skills disponibles para este agente

### En /mnt/skills (core, siempre disponibles)
- `quantum-companion` — acompañamiento global, siempre activo
- `prd-fastapi` / `prd-nextjs15` / `prd-go-wails` — según stack decidido
- `frontend-design` — para componentes de interfaz
- `plan-day` — planificación diaria

### En ~/.q-agent/skills (desde QuantumEdu/dots-quantum)
- `q-deliberate` — investigación arquitectónica
- `grill-me` — elicitación de requerimientos
- `skill-metaorquestador` — decisión de runtime
- `flujo-prompts-github` — pipeline P1-P7
- `CAB-RP` — auditoría NFR de cierre

---

## Reglas de autonomía

1. Del paso 4 en adelante el agente opera sin pedir permiso
2. Solo interrumpe al usuario en:
   - Gate P4: aprobación de scope (`proposal.md`)
   - Gate ADR: decisión arquitectónica con tradeoffs simétricos
   - Gate BLOCKER: error que requiere contexto externo
3. Toda decisión queda como Issue con label `type:adr` antes de ejecutarse

---

## Convenciones de este repositorio

### Branches
- `main` — producción estable
- `develop` — integración
- `feature/<nombre>` — features nuevas
- `fix/<nombre>` — correcciones
- `audit/<fecha>-<nombre>` — auditorías

### Commits
Formato: `<tipo>(<scope>): <descripción>`
Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `audit`

### Issues — labels activos
Ver taxonomía completa en `references/issue-labels.md` del q-agent.
Labels mínimos requeridos: `type:*` + `priority:*`

---

## Token budget (para ejecutores con límite de contexto)

### TL;DR para arranque rápido (< 200 tokens)
Proyecto: [nombre] · Plan: [A/B/C] · Rama: [actual] · Issue activo: #[N]
Executor: [nombre] · Siguiente tarea: [descripción de tasks.md]

### Contexto completo
[resto del CLAUDE.md]
```

---

## Variante Plan A (agrega esta sección)

```markdown
## Decisiones de Greenfield

**Stack decidido:** [resultado de la skill de metaorquestación]
**PRD base:** [link al artefacto generado por skill prd-*]
**Scope MVP aprobado:** [resumen del proposal.md aprobado en Gate P4]
**Out of scope explícito:**
- [item 1]
- [item 2]
```

---

## Variante Plan B (agrega esta sección)

```markdown
## Estado del código existente

**Repo base:** [URL]
**Blueprint:** `BLUEPRINT.md` (P1 MAB-PC completado)
**Tags encontrados en P1:**
- OBSERVADO: [N items]
- INFERIDO: [N items]
- CONFLICTO: [N items — requieren atención]

**Evolución arquitectónica:** `EVOLUTION.md` (P3 completado)
**Feature objetivo:** [descripción del Paso 1]
```

---

## Variante Plan C (agrega esta sección)

```markdown
## Estado de la auditoría

**Repo auditado:** [URL]
**Reporte:** `AUDIT_REPORT.md`
**Issues de remediación creados:** [N]
**Gaps P0 (críticos):** [N]
**Categorías auditadas:** [lista CAB-RP]
```
