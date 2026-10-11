---
name: q:gbrain-assistant
description: "Trigger: /q-gbrain-assistant, /gbrain, gbrain, g-brain, cerebro, consultar gbrain, invocar gbrain, segundo cerebro, usar gbrain. Gateway especializado a GBrain para consultas semánticas híbridas, persistencia de hechos y mantenimiento del grafo de conocimiento."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "2.0.0"
  date: "2026-10-10"
  context_policy: "PROGRESSIVE"
  requires: ["references/context-retrieval.md"]
  may_call: ["templates/gbrain-prompts.md"]
  produces: ["GBrain Query Synthesis", "Persisted Knowledge Facts"]
---

# q:gbrain-assistant v2.0 — Gateway a GBrain

## 1. Quick Bootstrap & Triggers
- **Propósito**: Proveer acceso estructurado y determinista al grafo de conocimiento y memoria multi-agente de **GBrain**.
- **Cuándo Aplica**:
  - Consultas híbridas de contexto (`gbrain query "<pregunta>"`).
  - Búsquedas por palabras clave (`gbrain search "<término>"`).
  - Persistencia de hechos atómicos estructurados (`gbrain remember`).
  - Verificación de salud de la base vectorial (`gbrain doctor`).
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO consultar Engram o SkillVault a través de esta skill**: GBrain es un store independiente.
  - No usar si GBrain no está instalado o configurado en el sistema (revisar `references/context-retrieval.md`).
  - No ejecutar escrituras o mantenimiento a partir de una solicitud de solo lectura.
- **Política de Contexto**: `PROGRESSIVE`. Cargar `templates/gbrain-prompts.md` únicamente si el usuario pide inspiración o plantillas interactivas de prompts.

## 2. Comandos Core de GBrain

| Intención | Comando CLI | Propósito |
| :--- | :--- | :--- |
| **Búsqueda Híbrida** | `gbrain query "<pregunta>"` | RRF + expansión semántica + síntesis |
| **Búsqueda Texto** | `gbrain search "<keyword>"` | Búsqueda rápida BM25 / tsvector |
| **Guardar Hecho** | `gbrain remember "<hecho>" --entity <slug>` | Persistencia de hechos atómicos |
| **Enlace de Grafo** | `gbrain link <de> <a> --link-type <tipo>` | Relaciones tipadas (`depends_on`, etc.) |
| **Diagnóstico** | `gbrain doctor [--json]` | Verificación de Postgres/PGLite y embeddings |

## 3. Contrato de Ejecución
- [ ] **M1 (Verificación)**: Comprobar que `gbrain` CLI esté disponible y configurado antes de invocar comandos.
- [ ] **M2 (Consulta/Mutación Acotada)**:
  - Para lecturas: Ejecutar `gbrain query` o `gbrain search` y sintetizar los hechos observados sin alucinar.
  - Para escrituras: Confirmar alcance y ejecutar `gbrain remember` o `gbrain link` con entidades explícitas.
- [ ] **M3 (Plantillas)**: Si el usuario solicita ideas de consulta, referenciar `templates/gbrain-prompts.md`.

## 4. Completion Gate
Antes de dar por concluida la interacción:
- [ ] Respuesta entregada citando hechos y fuentes devueltas por GBrain.
- [ ] Estado final declarado:
  - `[COMPLETE]` ──► Consulta o persistencia ejecutada exitosamente.
  - `[BLOCKED - reason]` ──► `gbrain` no configurado o base de datos no disponible.
  - `[FAILED - reason]` ──► Error en el motor de embeddings o timeout de consulta.
