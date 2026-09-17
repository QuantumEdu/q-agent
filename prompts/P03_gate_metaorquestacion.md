---
id: P3_GATE_METAORQUESTACION
titulo: "Gate de Metaorquestación — Selección de Motor Dual y Topología de Ejecución"
cuando_usar: "Al finalizar el descubrimiento inicial y antes de abrir la bitácora de implementación de cualquier feature."
prerequisitos: "CONSTITUTION.md (con Artículo ARQ-01) y requerimiento de feature definido."
entregables: "Declaración explícita del Motor de Ejecución seleccionado + Ruta canónica de la bitácora de tareas."
posicion_en_pipeline: "Paso 3 — Compuerta de metaorquestación previa a la implementación"
proyecto: "{{PROYECTO_NOMBRE}}"
fecha: "{{YYYY-MM-DD}}"
---

# P3 — Gate de Metaorquestación: Motor Dual y Topología

> **Misión:** Detectar dinámicamente las capacidades del host para seleccionar la topología de ejecución óptima (**Gentle-AI ODD** o **q-agent Standalone**) garantizando que ambos motores obedezcan la misma **CONSTITUTION** y el **Artículo ARQ-01**.

---

## 1. Protocolo de Detección Automática del Entorno

El agente evaluará de forma determinista la disponibilidad de herramientas en el entorno mediante los siguientes pasos:

### Paso 1.1: Sondeo de CLI y Skills de Gentle-AI
Ejecutar verificación en terminal o inspección de contexto:
```bash
gentle-ai --version 2>/dev/null || echo "GENTLE_AI_NOT_FOUND"
```
- **Si `gentle-ai` está instalado y responde:** Activar **MOTOR A (Gentle-AI Integrated ODD)**.
- **Si el comando no existe o falla:** Activar **MOTOR B (q-agent Standalone ODD)**.

### Paso 1.2: Sondeo de Capacidades Complementarias
- **Inspección de CodeGraph:** Verificar si el MCP `codegraph_explore` o la CLI `codegraph` están disponibles. Si `.codegraph/` existe o puede inicializarse, priorizarlo para navegación de código. Si no, operar con `ripgrep` y `fd`.
- **Inspección de Memoria Persistente:** Si herramientas `mem_*` (Engram) están activas, vincular el proyecto con `mem_current_project` y guardar el estado. Si no, usar archivos Markdown locales como única fuente de verdad.

---

## 2. Definición de Topología por Motor

### 🟢 MOTOR A: Gentle-AI Integrated ODD (Modo Ecosistema)
Se activa cuando el host cuenta con las herramientas de gentle-ai.
- **Ruta de Bitácora:** `odd/tasks/{{FEATURE_NAME}}.md` y espejo en memoria Engram `odd/{{FEATURE_NAME}}/tasks`.
- **Revisión de Calidad:** Sujeta al switch de usuario `gentle-ai review mode` (off por defecto; nunca activar sin permiso del usuario).
- **Herramienta de Exploración:** MCP `codegraph_explore` preferente.
- **Regla de Ejecución:** Tareas de ~400 líneas, avance orgánico, verificación terminal obligatoria.

### 🔵 MOTOR B: q-agent Standalone ODD (Modo Autónomo / Portátil)
Se activa cuando `gentle-ai` no está instalado (entorno limpio, CI básico, máquina remota o servidor estándar).
- **Ruta de Bitácora:** `q-tasks/{{FEATURE_NAME}}.md` (archivo markdown local autónomo).
- **Revisión de Calidad:** Gate interno autónomo `q-audit-readonly` + `q-ci-fixer` guiado por linters locales.
- **Herramienta de Exploración:** `ripgrep` (`rg`), `fd` y lecturas directas.
- **Regla de Ejecución:** Tareas atómicas de ~400 líneas, auto-verificación en terminal (`Terminal Evidence Gate`), cero dependencias externas.

---

## 3. Validación de Alineación Constitucional (Regla Común)

Independientemente del motor seleccionado:
1. Validar que exista `CONSTITUTION.md` en la raíz del proyecto.
2. Comprobar que el **Artículo ARQ-01** esté vigente:
   - Toda nueva funcionalidad debe planificarse como **Vertical Slice** (Cláusula 1).
   - Vistas en archivos `.html` higiénicos empaquetados (Cláusula 4).
   - Consultas SQL 100% parametrizadas (Cláusula 5).
   - Si se usa SQLite: DSN configurado con WAL mode y busy_timeout ≥ 5000ms (Cláusula 3).

---

## 4. Declaración de Gate (Salida Obligatoria al Usuario)

El agente debe emitir un mensaje de confirmación de 2 a 3 líneas antes de proceder a la creación de la bitácora (P04):

```text
🏛️ [GATE DE METAORQUESTACIÓN CONFIRMADO]
- Motor Activo: [Gentle-AI Integrated ODD / q-agent Standalone]
- Ruta de Bitácora: [odd/tasks/<feature>.md / q-tasks/<feature>.md]
- Ley Suprema: CONSTITUTION.md vigente (Artículo ARQ-01: Vertical Slices)
```
