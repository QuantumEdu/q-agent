# Propuesta de Implementación Futura: `q-academic`
## Agente Curricular y de Autoría de Materiales Didácticos

> **Estado:** Documento de diseño arquitectónico para futura implementación fuera del alcance del proyecto actual (`q-agent-v01`).  
> **Propósito:** Adaptar la metodología SDD (Spec-Driven Development) y el marco pedagógico de [`q-tutorial-authoring`](file:///D:/02-A/code/dots-quantum/skills/quantum/q-tutorial-authoring/SKILL.md) para la creación integral de cursos, materias, presentaciones, actividades y rúbricas.

---

## 1. Visión y Fundamentos del Agente

`q-academic` traslada el rigor de la ingeniería de software a la docencia universitaria y técnica. En lugar de generar "temarios genéricos" mediante LLMs superficiales, opera como un **Orquestador Curricular Basado en Competencias**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FLUJO PEDAGÓGICO SDD                            │
├────────────────────────────────────────────────────────────────────────┤
│ P0: CONSTITUCIÓN CURRICULAR (Ideario, Nivel, Criterios de Evaluación)  │
│                                ↓                                       │
│ P1: INGESTA DOCUMENTAL (Planes oficiales, RFCs, Bibliografía, RAG)     │
│                                ↓                                       │
│ P2: MAPA DE COMPETENCIAS (Verbos observables + Ponderaciones)          │
│                                ↓                                       │
│ P3: DESGLOSE SEMANAL & PROYECTO ESPINA (PBL - Project Based Learning)  │
│                                ↓                                       │
│ P4: AUTORÍA DE MATERIALES (Diapositivas, Tutoriales con Andamiaje ZDP) │
│                                ↓                                       │
│ P5: RÚBRICAS ANALÍTICAS Y EVALUACIONES (Formativa, Sumativa)           │
│                                ↓                                       │
│ P6: AUDITORÍA DE ALINEACIÓN CONSTRUCTIVA (Matriz Biggs 100% Cobertura) │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ingesta y Revisión Rigurosa de Documentación

Antes de redactar una sola diapositiva o tarea, el agente tiene prohibido inventar contenido de la nada. Debe ejecutar un paso previo de **revisión de fuentes primarias**:

1. **Ingesta de Fuentes Oficiales:**
   - Lectura de archivos locales: syllabus institucional (`syllabus.pdf`), temarios oficiales y cartas descriptivas de la universidad.
   - Conexión con MCPs de conocimiento (`gbrain`, `engram`, o búsqueda técnica especializada).
2. **Revisión de Documentación Técnica de Grado de Producción:**
   - Si la materia es de ingeniería de software o ciberseguridad, el agente consulta la documentación canónica oficial (ej: documentación de Python, OWASP Top 10, RFCs de IETF, especificaciones de W3C, AWS Well-Architected Framework).
3. **Control de Alucinación y Citación Obligatoria:**
   - Todo concepto técnico en el material debe contar con una referencia comprobable a la documentación oficial o bibliografía recomendada.

---

## 3. Integración con el Skill `q-tutorial-authoring`

El diseño de las guías y tutoriales prácticos de la materia debe adoptar estrictamente los **principios no negociables** de [`q-tutorial-authoring`](file:///D:/02-A/code/dots-quantum/skills/quantum/q-tutorial-authoring/SKILL.md):

### A. Los 4 Lentes Pedagógicos Obligatorios
- **PBL (Project-Based Learning) orientado a proyectos:** Cada materia cuenta con un *proyecto espina* real que los alumnos construyen incrementalmente módulo a módulo (cero "ejemplos de juguete" aislados).
- **Basado en Competencias:** Cada sesión declara una competencia observable (verbo de acción taxonómico) y su criterio de logro. El alumno sabe qué *podrá hacer*, no qué "verá".
- **Aprendizaje Significativo (Ausubel):** Activación de conocimiento previo mediante preguntas diagnósticas y analogías con conceptos que el alumno ya domina.
- **Zona de Desarrollo Próximo (ZDP de Vygotsky) + Andamiaje:** Cada ejercicio sigue una progresión gradual:
  1. *Guiado* (Worked example paso a paso con explicación de decisiones).
  2. *Semi-guiado* (Completion problem: esqueleto con huecos estratégicos y pistas colapsables en `<details>`).
  3. *Autónomo* (Problema abierto con criterio de aceptación ejecutable).

### B. Reglas de Autoría No Negociables
1. **Verificación Ejecutable:** Todo ejercicio práctico debe incluir un comando de terminal (one-liner o script de prueba) para que el alumno auto-verifique de forma determinista si su solución es correcta antes de entregarla.
2. **Sección de Misconceptions y Anti-Patrones:** Sección explícita de *"Errores comunes y trampas típicas"* que enseña a los alumnos cómo depurar cuando las cosas fallan.
3. **Carga Cognitiva Controlada (Sweller):** Un solo concepto nuevo a la vez; el modelo trabajado se entrega antes de solicitar la resolución abierta.
4. **Metacognición:** Bloque de cierre *"¿Cómo sabes que dominas este tema?"*, donde el estudiante autoevalúa su nivel (Novato / Competente / Experto) con evidencia empírica.
5. **Badges de Contexto de Ejecución:** Cada fragmento o instrucción debe indicar exactamente dónde se ejecuta:
   - `[badge:terminal]` — Comandos de consola / bash / powershell.
   - `[badge:IDE]` — Código a escribir en el editor o archivos fuente.
   - `[badge:browser]` — Pruebas en navegador o APIs de cliente.

---

## 4. Artefactos Entregables por Módulo

Para cada unidad de la materia, `q-academic` producirá una suite estructurada de artefactos:

| Entregable | Formato | Herramienta / Estándar | Propósito |
|---|---|---|---|
| **Carta Descriptiva / Plan de Sesión** | Markdown | GFM + Frontmatter | Define objetivos, horas teóricas, horas prácticas y prerrequisitos. |
| **Presentación de Diapositivas** | Markdown / PPTX | Marp (`marp --pptx`) | Diapositivas con contraste óptico alto, diagramas Mermaid y código formateado. |
| **Guía de Práctica de Laboratorio** | Markdown / HTML | `q-tutorial-authoring` | Tutorial interactivo con andamiaje ZDP, pistas y comandos de auto-verificación. |
| **Rúbrica Analítica de Evaluación** | Markdown / Tabla | Taxonomía de Marzano / Bloom | Criterios desglosados en 4 niveles (Sobresaliente, Notable, Aprobado, Insuficiente). |
| **Banco de Reactivos / Examen** | Markdown / QTI | Opción múltiple + Caso práctico | Reactivos balanceados (conceptuales, de depuración y de diseño). |

---

## 5. Auditoría de Alineación Constructiva (Análogo a P09 / CAB-RP)

Al finalizar la generación del curso, el agente ejecuta una auditoría de cierre:
- **Verificación de Cobertura:** Comprueba que cada competencia del temario cuente con al menos una actividad formativa y un criterio en la rúbrica sumativa.
- **Tolerancia Cero a Desalineación:** Si un examen pregunta algo que no fue cubierto en los tutoriales o si una actividad evalúa algo fuera del programa oficial, la auditoría emite una brecha `[GAP: DESALINEACIÓN CURRICULAR]` para su corrección antes de publicar el material.

---

## 6. Próximos Pasos para su Construcción
Cuando se decida implementar formalmente:
1. Crear el paquete `skills/q-academic/` como skill independiente.
2. Definir los prompts canónicos: `A01_curriculum_discovery.md`, `A02_syllabus_spec.md`, `A03_slides_builder.md`, `A04_rubric_generator.md`, `A05_pedagogical_audit.md`.
3. Integrar exportadores automatizados a PDF (vía Pandoc/Weasyprint) y diapositivas (vía Marp CLI).
