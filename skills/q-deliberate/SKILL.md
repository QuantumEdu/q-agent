---
name: q:deliberate
description: "Trigger: /q-deliberate, deliberate, multi-agent debate, stress-test architecture, design deliberation. Multi-agent dialectical interview that deploys Proponent, Adversary, and Synthesizer subagents to rigorously stress-test decisions in frontier rounds, producing validated architectures and ADRs."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "2.0.0"
  date: "2026-10-10"
  context_policy: "PROGRESSIVE"
  requires: ["references/execution-authority.md"]
  may_call:
    - "skills/q-deliberate/prompts/proponent.md"
    - "skills/q-deliberate/prompts/adversary.md"
    - "skills/q-deliberate/prompts/synthesizer.md"
  produces: ["docs/adr/*.md", "CONTEXT.md Glossary"]
---

# q:deliberate v2.0 — Deliberación Dialéctica Multi-Agente

## 1. Quick Bootstrap & Triggers
- **Propósito**: Interrogar, estresar y perfeccionar decisiones arquitectónicas mediante un debate dialéctico tripartito (Proponente vs Adversario vs Sintetizador) antes de presentar preguntas de frontera al usuario.
- **Cuándo Aplica**:
  - En Paso 2a de `q-agent` ante incertidumbre arquitectónica o bifurcaciones con tradeoffs reales.
  - Al diseñar sistemas donde la decisión sea costosa de revertir (selección de BD, protocolo de mensajería, patrones de sincronización).
  - Bajo demanda explícita (`/q-deliberate`).
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO para tareas mecánicas o ya acordadas**: Si el usuario o el equipo ya eligió el stack, no reabrir debate.
  - ⛔ **PROHIBIDO preguntar hechos observables**: Averiguar código, versiones y APIs directamente en el repo antes de consultar al usuario.
  - No deliberar cambios fácilmente reversibles o de bajo impacto.
- **Política de Contexto**: `PROGRESSIVE`. Cargar prompts de roles (`prompts/proponent.md`, etc.) únicamente durante su fase de ejecución.

## 2. Roles y Arquitectura Dialéctica

```text
               ┌──────────────────────────────────────┐
               │          User Prompt / Topic         │
               └──────────────────┬───────────────────┘
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │   Subagent 1: Proponent   │   │    Subagent 2: Adversary  │
    │      (Thesis Agent)       │   │     (Antithesis Agent)    │
    └─────────────┬─────────────┘   └─────────────┬─────────────┘
                  └───────────────┬───────────────┘
                                  ▼
                    ┌───────────────────────────┐
                    │   Subagent 3: Synthesizer │
                    │     (Arbitrator Agent)    │
                    └─────────────┬─────────────┘
                                  ▼
                    ┌───────────────────────────┐
                    │    Interactive User Round │
                    └───────────────────────────┘
```

## 3. Contrato de Ejecución (5 Fases)
- [ ] **M1 (Árbol de Decisión)**: Mapear el problema como un Grafo Acíclico Dirigido (DAG) e identificar la frontera inmediata.
- [ ] **M2 (Exploración Paralela)**:
  - *Proponent*: Construye la tesis viable basada en documentación primaria y benchmarks.
  - *Adversary*: Estresa límites de escala, modos de fallo y concurrencia.
- [ ] **M3 (Síntesis y Arbitraje)**: *Synthesizer* filtra sesgos y formula recomendación vinculante (`➡️`) con mitigaciones.
- [ ] **M4 (Ronda Interactiva)**: Presentar **una sola pregunta enfocada** con tradeoffs simétricos. **STOP y esperar**.
- [ ] **M5 (Cristalización de ADR)**: Incorporar respuesta, cerrar nodo de frontera y generar ADR en `docs/adr/000N-<title>.md`.

## 4. Completion Gate
Antes de dar por concluida la deliberación:
- [ ] Frontera de decisiones completamente resuelta (DAG sin nodos pendientes).
- [ ] ADR formalizado en `docs/adr/` para cada decisión difícil de revertir.
- [ ] Términos canónicos agregados a `CONTEXT.md` si aplica.
- [ ] Estado final:
  - `[COMPLETE]` ──► Decisiones zanjadas y documentadas en disco.
  - `[BLOCKED - reason]` ──► Disyuntiva requiere autorización humana pendiente.
