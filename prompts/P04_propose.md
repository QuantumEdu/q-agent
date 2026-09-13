---
id: P4_PROPOSE
titulo: "Propuesta Formal de Cambio SDD — /propose"
cuando_usar: "Para iniciar formalmente el ciclo SDD de la primera entrega funcional."
prerequisitos: "BLUEPRINT.md y CONSTITUTION.md aprobados. Gate de Fase 0 completado."
entregables: "openspec/changes/{{CHANGE_ID}}/proposal.md"
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P4 — Propuesta Formal de Cambio SDD
> `/propose`

---

Actúa como Orquestador SDD (Spec-Driven Development).

---

## PRE-CHECK: CLASIFICACIÓN DE CALIBRE (NIVEL 1 vs NIVEL 2)

Antes de redactar la propuesta, evalúa la solicitud contra los 4 filtros objetivos:
1. ¿Modifica o crea entidades del Dominio o tablas de Base de Datos?
2. ¿Crea o altera endpoints, contratos de API o eventos públicos?
3. ¿Afecta a 2 o más capas arquitectónicas?
4. ¿El volumen estimado supera 3 archivos o ~80 líneas de código?

- **SI TODAS LAS RESPUESTAS SON "NO" (y el usuario no forzó Full SDD):**
  Detén la generación de este documento y emite el dictamen:
  `⚡ Clasificación: NIVEL 1 (Fast-Track) — Micro-cambio / Patch.`
  Deriva la ejecución directamente al prompt **P8 en Modo Fast-Track** (Tarea atómica única con TDD + Verificación de stack + Commit atómico).

- **SI AL MENOS UNA RESPUESTA ES "SÍ" (o el usuario indicó Full SDD):**
  Procede con el flujo de **NIVEL 2 (Full SDD)** a continuación.

> 💡 **Nota de Contexto Dual-Mode:** Si `gbrain` está disponible en el entorno, consulta (`gbrain search "<tema>"`) para verificar qué entidades, decisiones y modelos ya existen en el proyecto antes de proponer nuevos. Si no está disponible, utiliza inspección directa con `ripgrep` o `git log`.

---

Contexto:
El descubrimiento, la auditoría, la Constitución y la propuesta de arquitectura de {{PROYECTO_NOMBRE}} están completados y aprobados. Iniciamos formalmente la Fase {{NUMERO_FASE}} del Roadmap.

Misión:
Crea el documento de propuesta de cambio en `openspec/changes/{{CHANGE_ID}}/proposal.md`.

Estructura y Contenido Requerido:

1. Motivación y Contexto:
   - ¿Por qué iniciamos por {{DESCRIPCION_ALCANCE_FASE}}?
   - Valor de negocio o técnico de esta entrega.

2. Alcance Formal:
   - IN SCOPE: {{LISTA_DE_ENTREGABLES_CONCRETOS}} — Capacidades y módulos que se construirán en esta iteración.
   - OUT OF SCOPE (Diferido): {{LISTA_DE_LO_QUE_NO_ENTRA}} — Capacidades explícitamente postergadas, **cada una con su justificación de negocio o técnica**.

   > ⚠️ **Regla Crítica de Trazabilidad para Auditoría CAB-RP (P9):**  
   > Todo requerimiento, integración, NFR o funcionalidad que no se aborde en este cambio DEBE quedar registrado en `OUT OF SCOPE (Diferido)` con su motivo explícito. En la auditoría de cierre (P9 / CAB-RP), esta sección es la **única fuente de verdad** para validar veredictos `⚪ No aplica`. Cualquier brecha omitida sin justificación previa en este documento será clasificada automáticamente como `Scope Drift no documentado` (`❌ Gap`).

3. Criterios de Éxito y Calidad:
   - Criterio funcional: {{DESCRIPCION_VERIFICABLE}}
   - Criterio de arquitectura: Invariante constitucional (ej. dominio puro sin dependencias externas, interfaces/puertos tipados).
   - Criterio de regresión y cobertura: Suite de tests automatizados pasando al 100% con detección de condiciones de carrera.

4. Gate de Aprobación de la Propuesta:
   - [ ] Motivación de negocio claramente articulada.
   - [ ] Límites IN SCOPE y OUT OF SCOPE definidos sin ambigüedades.
   - [ ] Aprobación humana explícita antes de proceder a `/spec` (Prompt P5).
