---
name: q:audit-readonly
description: "Trigger: /q-audit-readonly, /audit-readonly, auditar sin tocar, auditar repo read-only, inspeccion no mutante, audit integridad, revisar contratos openspec. Ejecuta auditorías técnicas exhaustivas de arquitectura, contratos SDD/OpenSpec, integridad de frontend y superficie de APIs sin modificar ningún byte en disco."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "1.0.0"
  date: "2026-09-03"
---

# q:audit-readonly

## Goal
Ejecutar auditorías técnicas profundas y exhaustivas sobre repositorios brownfield o código recién implementado con la garantía absoluta de **cero mutaciones en disco**, evaluando contratos SDD/OpenSpec, higiene de código, estabilidad de frontend y seguridad de APIs.

## When to Use
- Al iniciar el trabajo en un repositorio desconocido para hacer context grounding sin alterar Git.
- Cuando el usuario solicita auditar tareas, contratos o la UI expresando explícitamente "sin modificar archivos" o "modo lectura".
- Para certificar que las tareas marcadas como completadas `[x]` en `tasks.md` realmente cumplen la especificación `spec.md`.

---

## Invariantes Operativos No Negociables
1. **Inmutabilidad Absoluta**: Prohibido el uso de herramientas de edición (`replace_file_content`, `write_to_file`, `sed`, `git checkout .`). Al finalizar, `git status -s` debe ser idéntico al estado inicial.
2. **CodeGraph Primero**: Utilizar `codegraph` para resolver relaciones de llamadas y blast radius antes de realizar búsquedas textuales masivas.
3. **Tolerancia Cero a Completitudes Falsas**: Verificar si una funcionalidad marcada como terminada depende de datos estáticos inventados o mocks no autorizados.

---

## Protocolo Paso a Paso

### Paso 1: Verificación de Entorno y Topología
1. Ejecutar `git status -s` para registrar el estado de partida.
2. Comprobar si existe índice de CodeGraph (`.codegraph/`). Si no existe, inicializarlo de manera local.
3. Mapear los puntos de entrada principales (main, server, router, index).

### Paso 2: Auditoría de Contratos SDD / OpenSpec
1. Leer `spec.md` y `tasks.md`.
2. Para cada tarea marcada como completada `[x]`:
   - Localizar el archivo y función correspondiente.
   - Contrastar los criterios de aceptación (Given / When / Then).
   - Comprobar la existencia de tests automatizados reales que la respalden.

### Paso 3: Inspección de UI y Superficie de Red
1. En componentes de frontend: verificar que los formularios no precarguen valores falsos, no ignoren errores de validación y manejen estados de carga.
2. En APIs y WebSockets: revisar las rutas registradas, middleware de autenticación/RBAC y manejo de excepciones (evitar errores 500 no capturados ante payloads maliciosos).

### Paso 4: Emisión del Reporte Ejecutivo
Generar un informe en Markdown estructurado en:
- **Veredicto General**: [APTO / NO APTO / APTO CON OBSERVACIONES].
- **Hallazgos Críticos (P1)**: Discrepancias de contrato y bugs que rompen funcionalidad.
- **Hallazgos Medios (P2)**: Ausencia de validaciones, UX degradada o falta de tests.
- **Plan de Remediación Sugerido**: Lista ordenada de tareas para corregir los hallazgos.
