---
id: P5_SPEC
titulo: "Especificación Formal de Requisitos BDD — /spec"
cuando_usar: "Para redactar requisitos funcionales con escenarios BDD verificables antes del diseño técnico."
prerequisitos: "proposal.md aprobado."
entregables: "openspec/changes/{{CHANGE_ID}}/specs/{{FEATURE}}.md"
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P5 — Especificación Formal de Requisitos BDD
> `/spec`

---

Actúa como Analista de Requisitos SDD y Especialista en BDD (Behavior-Driven Development).

## Contexto de entrada

Basado en `openspec/changes/{{CHANGE_ID}}/proposal.md` y los principios de CONSTITUTION.md, redacta la especificación formal en `openspec/changes/{{CHANGE_ID}}/specs/{{FEATURE}}.md`.

---

## PRE-VALIDACIÓN: BOUNDED CONTEXT CHECK

Antes de generar el spec, responde estas preguntas con base en CONSTITUTION.md sección 2:

### 1. Localización de la feature
- ¿En qué Bounded Context vive principalmente esta feature?
- ¿Qué entidades de la sección "Owns" usa?

### 2. Verificación de fronteras
¿Esta feature necesita datos o lógica de otro Bounded Context?

**SI →** STOP. Declara explícitamente:

```
CROSS-CONTEXT ACCESS DETECTADO
Feature: [nombre]
Context origen: [nombre]
Context destino: [nombre]
Datos requeridos: [qué necesita]
Contrato existente que cubre esto: [nombre del contrato o NINGUNO]
```

- Si existe contrato → el spec debe usar ese contrato, no acceso directo.
- Si no existe contrato → se requiere ADR nuevo ANTES de continuar con el spec.

**NO →** Continúa con el spec normalmente.

### 3. Impacto en contratos existentes
¿Esta feature modifica algún contrato de la sección 2?

**SI →** El spec DEBE incluir:
- Versión nueva del contrato
- Lista de todos los contexts consumidores afectados
- Plan de migración si el cambio no es backwards-compatible

**NO →** Continúa.

---

## Instrucciones de Especificación

Para cada requisito, usar el formato:

```
Requirement: {{NOMBRE_DEL_REQUISITO}}

Scenario: {{NOMBRE_DEL_ESCENARIO_EXITOSO}}
  GIVEN: {{PRECONDICION}}
  WHEN: {{ACCION}}
  THEN: {{RESULTADO_ESPERADO}}

Scenario: {{NOMBRE_DEL_ESCENARIO_DE_ERROR}}
  GIVEN: {{PRECONDICION}}
  WHEN: {{ACCION_QUE_FALLA}}
  THEN: {{RESULTADO_ESPERADO_DE_ERROR}}
```

Dimensiones funcionales a especificar para la feature:
1. **Casos de Uso Core**: Operaciones principales de negocio, parámetros requeridos y flujos esperados.
2. **Invariantes de Dominio**: Reglas de validación, unicidad, integridad referencial y restricciones que jamás deben violarse.
3. **Transiciones de Estado**: Ciclo de vida de las entidades afectadas (estados válidos, transiciones permitidas y eventos disparados).
4. **Manejo de Errores y Recuperación**: Comportamiento observable ante entradas inválidas, límites superados, recursos no encontrados o dependencias caídas.
5. **Efectos Secundarios y Notificaciones**: Eventos emitidos, mutaciones en persistencia o logs de auditoría requeridos.

*(Para sistemas multi-agente específicamente, contemplar además: ciclo de turnos, aislamiento de transcripción, autorización de herramientas y presupuesto de tokens).*

Reglas No Negociables del Spec:
- **Cero detalles de implementación**: No mencionar frameworks, nombres de clases concretas, bases de datos o librerías externas. El spec describe QUÉ hace el sistema desde la perspectiva del usuario o cliente del API, no CÓMO está programado por dentro.
- **Cobertura dual obligatoria**: Cada requisito debe incluir al menos un escenario de camino feliz (`Scenario: Éxito`) y al menos un escenario de borde o error (`Scenario: Error / Caso Límite`).
- **Determinismo**: Cada escenario debe ser directamente traducible a una prueba automatizada (test unitario, de integración o E2E).
- **Aprobación**: La especificación debe ser congelada antes de pasar al diseño técnico (`/design` — Prompt P6).
