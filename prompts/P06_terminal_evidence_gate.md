---
id: P6_TERMINAL_EVIDENCE_GATE
titulo: "Compuerta de Evidencia en Terminal — Verificación Empírica y Anti-Mocking"
cuando_usar: "Inmediatamente después de implementar el código de una tarea (P05) y antes de marcarla como completada."
prerequisitos: "Código del slice escrito en disco; bitácora viva abierta."
entregables: "Registro de ejecución en la tabla Terminal Evidence Gate + Checkbox marcado legítimamente [x]."
posicion_en_pipeline: "Paso 6 — Verificación Empírica Obligatoria"
proyecto: "{{PROYECTO_NOMBRE}}"
fecha: "{{YYYY-MM-DD}}"
---

# P6 — Terminal Evidence Gate (Compuerta de Evidencia en Terminal)

> **Regla de Oro Constitucional:**
> Queda estrictamente prohibido marcar una tarea como completada (`[x]`) si el agente no ejecutó un comando en la terminal del host y observó directamente la evidencia empírica de su correcto funcionamiento.

---

## 1. El Problema de las Falsas Completitudes (Anti-Mocking)

En el desarrollo asistido por IA, el fallo más común es dar por terminado un cambio asumiendo mentalmente que el código funciona, o peor aún, dejando mocks estáticos o datos en memoria para simular que la tarea pasó.

**Criterio de Tolerancia Cero:**
- Ningún checkbox se marca por "suposición".
- Ningún endpoint se da por bueno sin haber recibido una respuesta HTTP válida o haber ejecutado su test de integración correspondiente.
- Toda simulación no autorizada se clasifica como una falta crítica (`❌ Gap P0`).

---

## 2. Protocolo de Verificación Dual (Máquina + Adversarial)

Para cada tarea atómica construida en P05, la compuerta se divide en dos fases obligatorias y secuenciales:

### 2.1 Fase A: Verificación Empírica de Máquina
Ejecutar en terminal al menos dos de las siguientes comprobaciones:

#### A.1 Compilación e Integridad de Tipos
Ejecutar el compilador o checker de tipos del stack:
- En Go: `go vet ./...` y `go build ./...`
- En TypeScript: `npx tsc --noEmit`
- En Python: `python -m py_compile <archivos>` o `mypy`
*Condición de paso:* Código de salida `0` y cero errores de sintaxis.

#### A.2 Tests Automatizados
Ejecutar la suite de tests que cubre el slice vertical o módulo modificado:
- En Go: `go test -v -race ./features/<nombre-slice>/...`
- En Python: `pytest tests/<modulo>/`
- En Node: `npm test`
*Condición de paso:* Todos los tests en verde (`PASS`), sin panics ni fallos de aserción.

#### A.3 Humo y Superficie HTTP
Si la tarea incluye un endpoint o fragmento de vista (HTMX/HTML):
- Comprobar mediante un test de integración HTTP o invocación directa que el handler devuelve el código HTTP esperado (`200 OK` o `303 Redirect`).
- Verificar que los headers de respuesta sean correctos (`Content-Type: text/html; charset=utf-8`).
- Verificar que el fragmento HTML contenga los elementos de interfaz requeridos por el `UAC`.

---

### 2.2 Fase B: Compuerta de Revisión Adversarial Aislada (`skills/q-adversarial-review`)

Una vez que la máquina confirma verde (`exit code 0`), se activa la revisión de arquitectura y diseño:

1. **Aislamiento de Contexto:** Despachar un subagente independiente (`invoke_subagent`) invocando `skills/q-adversarial-review`.
2. **Auditoría del Diff:** El revisor evalúa el `git diff` contra el **Artículo ARQ-01** (mínima indirección, higiene de plantillas `.html`, 100% queries parametrizadas y cero mocks simulados).
3. **Condición de Paso:** Veredicto explícito `APPROVED`.
   - Si emite `REJECTED`: El agente escritor debe corregir las observaciones y repetir la compuerta 6.1 y 6.2.

---

## 3. Registro Obligatorio en la Bitácora

Una vez aprobadas AMBAS fases (Máquina + Adversarial):

1. **Abrir la bitácora activa** (`q-tasks/{{FEATURE_NAME}}.md` o `odd/tasks/{{FEATURE_NAME}}.md`).
2. **Registrar la fila en la tabla `Terminal Evidence Gate`:**
   ```markdown
   | TASK-01 | go test ./features/reuniones -v | 0 | PASS: TestCreateReunion (0.02s) | [VERIFICADO + ADVERSARIAL APPROVED] |
   ```
3. **Marcar el checkbox:**
   Cambiar `- [ ] **TASK-01` por `- [x] **TASK-01`.

---

## 4. Gestión de Errores y Bloqueos

- Si el comando de terminal falla (código de salida != 0):
  1. Analizar el stack trace o mensaje de error real devuelto por la terminal.
  2. Corregir el código en disco.
  3. Volver a ejecutar el comando hasta observar éxito determinista.
  4. Jamás marcar la tarea ni reportar éxito si persiste algún fallo.
