---
id: P2_CONTEXT_ENGINEERING
titulo: "Evaluación de Viabilidad y Anti-Sobreingeniería — Context Engineering"
cuando_usar: "Para aterrizar los hallazgos de la auditoría sobre el stack deseado y aplicar el filtro de ingeniería por contexto."
prerequisitos: "BLUEPRINT.md y CONSTITUTION.md completos (o borrador del Domain Expert Interview)."
entregables: "Evaluación de viabilidad del stack + Arquitectura Hexagonal Ligera definida."
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P2 — Evaluación de Viabilidad y Anti-Sobreingeniería
> Context Engineering

---

Actúa como Arquitecto de Software Senior aplicando la disciplina de Ingeniería por Contexto (Context Engineering).

Contexto del Sistema:
Estamos diseñando {{PROYECTO_NOMBRE}}: {{DESCRIPCION_BREVE}}.
Stack Tecnológico Deseado: {{BACKEND_STACK}} + {{MODEL_LAYER}} + {{FRONTEND_STACK}} + {{STORAGE}}.

Tareas y Criterios Requeridos:

1. Clasificación del Trabajo:
   - Clasifica el nivel: Prototipo | Simple | Profesional | Crítico.
   - Identifica los subcomponentes con riesgo crítico.

2. Evaluación Técnica del Stack:
   - Evalúa la idoneidad de {{BACKEND_STACK}} para la concurrencia de agentes.
   - Analiza si {{STORAGE}} es suficiente para el MVP y para producción.
   - Lista las bibliotecas complementarias estrictamente necesarias.

3. Arquitectura Hexagonal Ligera:
   - Diseña la estructura de paquetes con exactamente:
     * `domain/` — núcleo puro (entidades, reglas, interfaces/puertos)
     * `application/` — casos de uso y orquestación
     * `infrastructure/` — adaptadores técnicos
   - Regla no negociable: `domain` jamás importa infraestructura ni librerías externas.

4. Justificación de Patrones de Diseño:
   Para cada patrón propuesto, responder:
   a) ¿Qué problema real resuelve en {{PROYECTO_NOMBRE}}?
   b) ¿Por qué una solución más simple no basta?
   - Prohibir explícitamente patrones sin justificación.

5. Estrategia de Testing (TDD Selectivo):
   - TDD obligatorio: módulos con lógica crítica o de seguridad.
   - Testing convencional: handlers HTTP, repositorios, UI.

Entregables:
- Evaluación de viabilidad del stack.
- Definición de la arquitectura hexagonal ligera.
- Justificación de patrones.
- Clasificación de módulos para TDD.
