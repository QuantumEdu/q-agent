---
name: q:gbrain-assistant
description: >
  Trigger: /q-gbrain-assistant, /gbrain, gbrain, g-brain, cerebro, consultar gbrain, invocar gbrain, segundo cerebro, usar gbrain.
  Interactive prompt catalog, query templates, and actionable CLI workflows to query, enrich, and maintain the GBrain knowledge graph and multi-agent memory.
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "1.0.0"
  date: "2026-08-29"
  updated_at: "2026-08-29"
---

# q:gbrain-assistant

## Goal

Provide a structured, interactive gateway to **GBrain** (Personal & Multi-Agent Knowledge Graph + Memory Substrate). When invoked, it immediately surfaces high-value prompt templates, structured intent categories, and deterministic CLI commands for interacting with the brain.

## When to Use (Triggers)

- User types `/gbrain`, `/q-gbrain-assistant`, or asks `"en qué me ayuda gbrain"`, `"cómo consulto gbrain"`, `"segundo cerebro"`, `"invocar gbrain"`.
- User needs ready-to-use prompt templates for meeting preparation, architectural history, knowledge ingestion, trajectory evaluation, or health checks.
- Agent needs deterministic CLI mappings to execute operations against GBrain (`gbrain query`, `gbrain remember`, `gbrain link`, `gbrain doctor`).

---

## 🧠 Interactive Prompt & Workflow Hub

When triggered, present the user with this structured intent catalog:

### 1. 🔍 Consulta & Síntesis Contextual
*Búsqueda híbrida (RRF + expansión semántica) con redacción de respuestas y análisis de brechas.*

- **Prompt 1.1 (Briefing de Reunión / Contacto):**
  > *"¿Qué necesito saber antes de mi reunión con `[Persona / Empresa]`? Resume acuerdos previos, compromisos pendientes y notas abiertas."*
- **Prompt 1.2 (Resumen Ejecutivo de Proyecto):**
  > *"Hazme una síntesis del estado actual de `[Proyecto]`. ¿Cuáles han sido los hitos recientes y qué bloqueos existen?"*
- **CLI Command:**
  ```bash
  gbrain query "¿Qué acuerdos abiertos tenemos con [Persona]?"
  ```

---

### 2. 🏛️ Decisiones Técnicas & Arquitectura
*Recuperación de justificaciones de diseño, historial de decisiones pasadas y navegación de dependencias.*

- **Prompt 2.1 (Justificación Histórica / Por qué de una decisión):**
  > *"¿Por qué decidimos utilizar `[Tecnología / Patrón]` en lugar de `[Alternativa]` en el módulo `[Módulo]`?"*
- **Prompt 2.2 (Grafo de Dependencias entre Servicios):**
  > *"¿Qué servicios o librerías dependen de `[Componente]` y cuáles son los contratos de datos clave?"*
- **CLI Commands:**
  ```bash
  gbrain search "arquitectura [modulo]"
  gbrain graph-query [componente] --type depends_on
  ```

---

### 3. 💾 Registro & Capitalización de Conocimiento (Compounding Memory)
*Persistencia de hechos atómicos estructurados y enlace de aristas tipadas en el grafo.*

- **Prompt 3.1 (Guardar Hecho Atómico Vinculado a Entidad):**
  > *"Guarda en GBrain que `[Hecho / Regla / Configuración]` para la entidad `[Entidad/Servicio]`."*
- **Prompt 3.2 (Vincular Entidades en el Grafo de Conocimiento):**
  > *"Conecta la entidad `[Servicio A]` con `[Servicio B]` indicando una relación de tipo `[depends_on / calls / owns]`."*
- **CLI Commands:**
  ```bash
  gbrain remember "La tasa de refresco del token es de 15 minutos" --entity auth-service
  gbrain link auth-service redis-cluster --link-type depends_on
  ```

---

### 4. 📊 Métricas, Trayectorias y Verificación de Consistencia
*Auditoría cronológica de cambios y detección de lagunas de información (Gap Analysis).*

- **Prompt 4.1 (Evolución y Línea de Tiempo de Entidad):**
  > *"Muestra la trayectoria histórica y cambios clave de `[Entidad / Proyecto]` en los últimos meses."*
- **Prompt 4.2 (Detección de Brechas / Gap Analysis):**
  > *"Analiza la información disponible sobre `[Iniciativa]`. ¿Qué datos críticos faltan por documentar o están desactualizados?"*
- **CLI Command:**
  ```bash
  gbrain eval trajectory [entidad-slug]
  gbrain timeline [entidad-slug]
  ```

---

### 5. 🩺 Diagnóstico, Sincronización y Mantenimiento
*Comprobación de salud de la base de datos (PGLite / Postgres), sincronización Git e ingesta de notas.*

- **Prompt 5.1 (Diagnóstico de Salud Operativa):**
  > *"Ejecuta un diagnóstico del estado del motor de GBrain y reporta si hay inconsistencias."*
- **Prompt 5.2 (Sincronización Incremental Git):**
  > *"Sincroniza los últimos cambios del repositorio local con la base de datos de GBrain."*
- **CLI Commands:**
  ```bash
  gbrain doctor
  gbrain engine status
  gbrain sync
  ```

---

## ⚡ Reference Table: Core CLI Commands

| Intent | CLI Command | Notes |
| :--- | :--- | :--- |
| **Hybrid Query** | `gbrain query "<question>"` | RRF + semantic expansion + synthesis |
| **Keyword Search** | `gbrain search "<keyword>"` | Fast full-text BM25 / tsvector search |
| **Atomic Fact** | `gbrain remember "<fact>" --entity <slug>` | Persists typed facts to entity facts table |
| **Full Page Write** | `gbrain put <slug> < document.md` | Writes or updates a full Markdown page |
| **Graph Edge** | `gbrain link <from> <to> --link-type <type>` | Creates typed relations (`depends_on`, `works_at`, etc.) |
| **Timeline** | `gbrain timeline <slug>` | Views chronological sequence of entity events |
| **Trajectory** | `gbrain eval trajectory <slug>` | Rollup of metric claims and regressions |
| **Directory Ingest** | `gbrain import <dir> [--no-embed]` | Bulk imports Markdown documentation into vault |
| **Health Check** | `gbrain doctor [--json]` | Verifies database, pgvector, skills & embeddings |
