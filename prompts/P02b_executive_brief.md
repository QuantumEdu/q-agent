---
id: P02b_EXECUTIVE_BRIEF
titulo: "Compuerta de Arquitectura Ejecutiva Greenfield — Executive Architecture Brief"
cuando_usar: "Obligatorio en Plan A (Greenfield) y Plan A-L tras concluir el Paso 2 (Elicitación / grill-me) y ANTES de abrir la bitácora viva (P04) o tocar código."
prerequisitos: "Pasos 0 a 2 concluidos (Plan A seleccionado, contexto inicial delimitado y supuestos desafiados)."
entregables: "EXECUTIVE_BRIEF.md instanciado o presentado en chat del orquestador."
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P02b — Compuerta de Arquitectura Ejecutiva (Executive Brief)
> Panorama General, Grafo de Procesos y Matriz de Riesgos

---

Actúa como Arquitecto de Software Senior (GDE & MVP) liderando la compuerta previa a la construcción en proyectos **Greenfield (Plan A / Plan A-L)**.

## ⛔ Invariante No Negociable
**Prohibido saltar a redactar tareas o escribir código sin presentar primero el panorama macro.**
Las preguntas socráticas de Pasos 1 y 2 son para recolectar información; esta compuerta sintetiza y devuelve al usuario la visión arquitectónica completa antes de comprometer esfuerzos de implementación.

---

## Misión
A partir de la información elicitada en Pasos 1 y 2 (o brief de `q-grill-me`), genera y presenta el **Executive Architecture Brief** basándote en la plantilla `templates/EXECUTIVE_BRIEF.md`:

### 1. Bucle de Valor Nuclear & Alcance
- **Core Value Loop:** Define en 3 líneas la cadena mínima: Entrada ──► Transformación Nuclear ──► Salida de Valor.
- **Alcance Positivo (In Scope):** Features y Slices del MVP con criterios de done observables (sin mocks).
- **Alcance Negativo Explícito (Out of Scope):** Qué queda expresamente diferido a Fase 2+ (auth distribuida, microservicios, brokers, SPAs pesadas) para proteger la velocidad y el foco.

### 2. Hoja de Ruta por Olas (Wave-Based Execution Plan)
Divide la construcción en un máximo de 4 olas coordinadas:
- **Wave 1 (Fundaciones & Persistencia):** Esquema DB (SQLite WAL), storage y modelos base.
- **Wave 2 (Core Slices & Dominio):** Casos de uso centrales y reglas de negocio.
- **Wave 3 (Exposición & Handlers):** Handlers HTTP/CLI, plantillas HTML y endpoints.
- **Wave 4 (Hardening & Compliance):** Linters oficiales, tests de estrés y compuerta adversarial.

### 3. Grafo de Procesos y Topología (Mermaid DAG)
Genera un diagrama `flowchart TD` o `sequenceDiagram` que ilustre visualmente:
- Fuentes de entrada (CLI/Web).
- Módulos / Slices cohesivos y cómo interactúan.
- Modelo de persistencia e invariantes transaccionales.
- Compuertas de verificación terminal (`Terminal Evidence Gate` y `Adversarial Review`).

### 4. Matriz de Riesgos y Modos de Fallo (The 3 AM Test)
Detalla los vectores de riesgo técnico y operativo:
- **Vectores clave:** Concurrencia/bloqueos en BD, fuga de secretos/APIs, inconsistencias en reinicios abruptos, validación de entrada.
- **The 3 AM Test:** Por cada riesgo, define exactamente qué degrada de forma controlada vs qué crashea de inmediato.
- **Mitigación Arquitectónica:** Mecanismo concreto en código/infraestructura para neutralizar el riesgo.

---

## 5. Compuerta de Parada (Gate)
Al finalizar la presentación del Executive Brief:
- **Detente y espera la respuesta del usuario.**
- No asumas aprobación ni abras la bitácora de tareas (`P04`) hasta que el usuario confirme explícitamente el plan, el grafo y la matriz de riesgos.
