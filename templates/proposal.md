# proposal.md
> Propuesta Formal de Cambio SDD — Producido por P4 (/propose)
> Path: `openspec/changes/{{CHANGE_ID}}/proposal.md`

Proyecto: [nombre]
Change ID: [CHANGE_ID]
Fase: [número y nombre de la fase]
Fecha: [YYYY-MM-DD]
Autor: [quien ejecutó P4]
Estado: [BORRADOR / APROBADO / RECHAZADO]

---

## 1. MOTIVACIÓN Y CONTEXTO

### ¿Por qué esta feature/cambio ahora?
[Describir el problema de negocio o técnico que resuelve. 2-4 oraciones.]

### Valor de negocio o técnico
[¿Qué se desbloquea al entregar esto? ¿Qué riesgo se mitiga?]

### Relación con la arquitectura existente
[¿Extiende, modifica o introduce un nuevo patrón en la CONSTITUTION?]

---

## 2. ALCANCE FORMAL

### ✅ IN SCOPE — Lo que se construye en este cambio

| # | Capacidad / Módulo | Descripción | Criterio de Done |
|---|---|---|---|
| 1 | [nombre] | [qué hace] | [cómo se verifica] |
| 2 | [nombre] | [qué hace] | [cómo se verifica] |

### 🔴 OUT OF SCOPE (Diferido) — Lo que NO entra en este cambio

> ⚠️ **Regla CAB-RP (P9):** Todo lo que no se aborda aquí DEBE estar en esta sección con su justificación. En la auditoría de cierre, esta tabla es la única fuente de verdad para veredictos `⚪ No aplica`. Omisiones sin justificación = `❌ Scope Drift no documentado`.

| # | Capacidad omitida | Motivo de exclusión | Fase prevista |
|---|---|---|---|
| 1 | [nombre] | [técnico / negocio / dependencia] | [Fase X / TBD] |

---

## 3. BOUNDED CONTEXTS INVOLUCRADOS

> Completar con base en CONSTITUTION.md sección 2 antes de proceder a P5.

| Context | Rol en este cambio | Contratos que se tocan |
|---|---|---|
| [nombre] | [produce / consume / modifica] | [nombre del contrato o NINGUNO] |

**¿Se cruzan fronteras de contexto?** [SÍ → requiere ADR previo / NO]

---

## 4. CRITERIOS DE ÉXITO Y CALIDAD

| Criterio | Tipo | Cómo se verifica |
|---|---|---|
| [descripción funcional verificable] | Funcional | [test / demo / log] |
| Invariante constitucional respetado | Arquitectónico | Revisión P9 CAB-RP |
| Suite de tests al 100% | Calidad | CI gate automatizado |
| Sin regresiones en módulos adyacentes | Regresión | Test suite existente |

---

## 5. RIESGOS Y DEPENDENCIAS

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| [descripción] | [Alta / Media / Baja] | [Alto / Medio / Bajo] | [acción] |

**Dependencias bloqueantes:** [lista o NINGUNA]

---

## 6. GATE DE APROBACIÓN

> La propuesta debe ser aprobada explícitamente ANTES de ejecutar P5 (/spec).

- [ ] Motivación de negocio claramente articulada.
- [ ] IN SCOPE sin ambigüedades — cada ítem tiene criterio de done verificable.
- [ ] OUT OF SCOPE completo — todo lo diferido tiene justificación explícita.
- [ ] Bounded Contexts identificados; fronteras cruzadas documentadas o declaradas como inexistentes.
- [ ] Aprobación humana explícita registrada.

**Aprobado por:** [nombre] **Fecha:** [YYYY-MM-DD]
