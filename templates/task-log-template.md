# Bitácora de Feature ODD: {{FEATURE_NAME}}
> Documento vivo unificado de desarrollo — Gobernado por el protocolo Organic Driven Development (ODD).
> Ruta canónica: `q-tasks/{{FEATURE_NAME}}.md` (Modo Standalone) o `odd/tasks/{{FEATURE_NAME}}.md` (Modo Gentle-AI).
> Autoridad de alcance, estado de tareas, aceptación y decisiones; informes enlazan evidencia, no duplican estados.
> Aplicar [comunicación y procedencia](../references/communication-contract.md) y la [guía de fases](../docs/communication-policy.md).

> 🧭 **Criterio de Apertura (Resume Test):**
> Esta bitácora solo se abre para tareas **GRANDES** (features, evolución o requerimientos complejos). Si el cambio es **PEQUEÑO** (entendido en ≤3 llamadas/10k tokens, riesgo acotado, y terminable desde el `git diff` solo si la sesión se corta), se resuelve **INLINE** sin bitácora vía Fast-Track (Plan F).

| Metadato | Valor |
|---|---|
| **Feature ID** | `{{FEATURE_ID}}` |
| **Fecha de inicio** | `{{YYYY-MM-DD}}` |
| **Motor de Ejecución** | [q-agent Standalone / Gentle-AI ODD] |
| **Arquitecto / Agente** | `{{AGENTE_NOMBRE}}` |
| **Estado Global** | [EN PROGRESO / VERIFICADO / CERRADO] |

---

## 1. MOTIVACIÓN Y VALOR

### Problema y Oportunidad
[Describir en 2-3 oraciones qué problema técnico o de negocio se resuelve y por qué es relevante ahora.]

### Impacto Esperado
[¿Qué se desbloquea al entregar este slice? ¿Qué fricción se elimina?]

---

## 2. ESPECIFICACIONES CONSTITUCIONALES (S# — Spec by Reference)

> 📜 **Mandato Spec by Reference:**
> Los requerimientos del usuario, errores reportados y strings exactos se transcriben aquí literalmente (sin parafrasear).
> Al despachar tareas a subagentes o worktrees aislados, el handoff cita esta fuente directa (`Spec: q-tasks/{{FEATURE_NAME}}.md, Tarea T-XX, Specs S-01 a S-02`).
> El subagente lee esta sección y la sección final `## Log` directamente, rindiendo cuentas de qué `S#` fueron cubiertas.

- **S-01:** [Requerimiento técnico/funcional exacto, citando strings literales, inputs esperados y salidas observables]
  - *Criterio de Aceptación / Verificación:* [Condición booleana demostrable en test o terminal]
- **S-02:** [Requerimiento técnico/funcional exacto, citando strings literales, inputs esperados y salidas observables]
  - *Criterio de Aceptación / Verificación:* [Condición booleana demostrable en test o terminal]

---

## 3. PERSPECTIVA DE PRODUCT MANAGER (Lente BMAD / Squad Path)

### 👤 User Persona & Dolor Actual
- **Rol / Persona:** [ej. Líder de Proyecto / Operador Técnico / Usuario Final]
- **Fricción / Dolor Actual:** [¿Qué cuello de botella, error manual o falta de visibilidad sufre hoy?]

### 📋 Historias de Usuario Ágiles (User Stories)
- **US-01:** Como **[rol]**, quiero **[capacidad o acción en el sistema]**, para **[beneficio medible en negocio o productividad]**.
  - **Criterio de Aceptación (UAC-01):** [Resultado observable y verificable en la interfaz o respuesta HTTP, vinculado a S-01]
- **US-02:** Como **[rol]**, quiero **[capacidad o acción en el sistema]**, para **[beneficio medible en negocio o productividad]**.
  - **Criterio de Aceptación (UAC-02):** [Resultado observable y verificable en la interfaz o respuesta HTTP, vinculado a S-02]

### 🎯 Hipótesis de Valor de Negocio
[¿Cómo medimos que esta entrega resolvió el dolor del usuario? Métrica observable de éxito.]

---

## 4. ALCANCE Y GOBERNANZA CONSTITUCIONAL (ARQ-01)

### ✅ In Scope (Lo que se construye)
1. [Capacidad 1 vinculada a S-01 / UAC-01]
2. [Capacidad 2 vinculada a S-02 / UAC-02]

### 🔴 Out of Scope (Exclusiones deliberadas)
> ⚠️ Cualquier omisión debe estar justificada aquí para evitar Scope Drift no documentado en la auditoría P09.
1. [Elemento diferido y justificación de por qué no entra en este ciclo]

### ⚖️ Cláusulas Constitucionales Aplicables
- [x] **Cláusula 1 (Vertical Slice):** Feature implementado como slice autónomo sin capas pasamanos artificiales.
- [x] **Cláusula 3 (Persistencia Pragmática):** Consultas directas sin hidratación forzada. (Si SQLite: WAL mode + busy timeout).
- [x] **Cláusula 4 (Higiene de Plantillas):** Vistas en archivos `.html` independientes empaquetados (`//go:embed` o template engine nativo). Cero HTML en strings de código.
- [x] **Cláusula 5 (Ciberseguridad):** 100% SQL parametrizado, escape contextual anti-XSS activado, cero secrets.

---

## 5. CHECKLIST DE TAREAS ATÓMICAS EN OLEADAS (WAVE-BASED EXECUTION)

> **Regla de Vertical Slices, Declaración de Ruta & Commits Atómicos:**
> Cada tarea es una unidad mínima coherente (~400 LOC) construida como un slice vertical o paso atómico con sus tests.
> - **Ruta:** Cada tarea declara explícitamente `Ruta: inline` (si la hace el orquestador) o `Ruta: delegated` (si usa worktree aislado `.q-worktrees/task-XX` por disparador de paralelismo o aislamiento).
> - **Handoff:** Despachar por referencia (`Spec: q-tasks/{{FEATURE_NAME}}.md, TASK-XX, S-01`). Prohibido parafrasear.
> - **Sello de Tarea:** Toda tarea verificada se sella con su commit convencional atómico (código + tests + docs) y su hash queda registrado en el checklist: `- [x] TASK-XX (Commit: <sha>) ...` antes de pasar a la siguiente.
>
> Las tareas se agrupan en **Oleadas (Waves)** basadas en su grafo de dependencias:
> - **Wave 1 (Cero dependencias mutuas):** Entidades de dominio, esquemas de BD, tests reproductores en rojo (`RED_FAIL`). Ejecutables concurrentemente.
> - **Wave 2 (Dependientes de Wave 1):** Casos de uso, servicios de aplicación y adaptadores de persistencia.
> - **Wave 3 (Dependientes de Wave 2):** Controladores HTTP, endpoints, plantillas `.html` empaquetadas e integración UI.

### 🌊 Wave 1: Contratos, Dominio y Tests Base (Sin dependencias)
- [ ] **TASK-01 [Wave 1] [S-01] [Ruta: inline | delegated] — [Nombre de la tarea, ej. Modelo de almacenamiento y migración SQL]:**
  - *Archivos:* `[ruta/al/storage.go]`, `[ruta/a/schema.sql]`
  - *Acción:* [descripción concreta de la implementación]
  - *Verificación prevista:* [Comando o test para validar]

### 🌊 Wave 2: Casos de Uso y Servicios de Aplicación (Depende de W1)
- [ ] **TASK-02 [Wave 2] [S-01] [Ruta: inline | delegated] — [Nombre de la tarea, ej. Handler HTTP y lógica de servicio]:**
  - *Archivos:* `[ruta/al/handler.go]`, `[ruta/al/service.go]`
  - *Acción:* [Crear controlador de ruta y caso de uso]
  - *Verificación prevista:* [Comando curl o test de integración HTTP 200]

### 🌊 Wave 3: Vistas, Interfaz y Entrega (Depende de W2)
- [ ] **TASK-03 [Wave 3] [S-02] [Ruta: inline | delegated] — [Nombre de la tarea, ej. Interacción reactiva HTMX / Alpine en view.html]:**
  - *Archivos:* `[views/modulo/view.html]`, `[assets/js/...]`
  - *Acción:* [Implementar vista empaquetada o swap dinámico]
  - *Verificación prevista:* [Prueba de endpoint fragmento]

---

## 6. TERMINAL EVIDENCE GATE & SPEC-DERIVED PROBES

> ⛔ **CANDADO MANDATORIO DE EJECUCIÓN:**
> Queda estrictamente prohibido marcar una tarea como completada (`[x]`) sin registrar en esta tabla la evidencia real de ejecución observada en la terminal.
> Cero falsas completitudes, cero suposiciones, cero mocks permanentes sin autorización.
>
> 🧪 **Spec-Derived Probes (Verificación Independiente):**
> Los tests del implementador no bastan por sí solos. La compuerta de verificación formula pruebas independientes derivadas de la especificación (`S#`): casos frontera (vacíos, duplicados, límites), hashing de invariantes en comandos rechazados (la base de datos no muta ante error), y los consolida como tests de regresión duraderos.

| Wave | Tarea ID | Comando Ejecutado en Terminal | Código de Salida (Exit Code) | Resultado Observado / Evidencia | Telemetría (Tokens / Costo USD) | Estado |
|---|---|---|---|---|---|---|

Tabla inicialmente vacía; registrar únicamente ejecuciones observadas, con tests,
exit/status/tiempo disponibles y enlaces a evidencia, nunca filas de ejemplo como resultados.

### 💰 Telemetría y Presupuesto Económico de Ejecución
- Cada métrica usa status/value/source/basis: `measured` requiere fuente real;
  `estimated` requiere fuente y supuestos explícitos; `unavailable` usa valor `null`.
- Tokens/costo opcionales sin instrumentación, incluso enterprise; desconocido no
  significa cero ni gratuito. Totales parciales deben identificar lo no disponible.
- Registrar actor, fase y hora real con zona o ausencia visible conforme al contrato;
  un mensaje del LLM no prueba ejecución de CLI ni reemplaza evidencia nativa.
- **Eficiencia de Corrección (Zero-Waste):** [Indicar número de rondas de corrección consumidas, ej. 0/2 en verde a la primera pasada].

---

## 7. CIERRE, REVISIÓN E INTEGRACIÓN EN BLUEPRINT

### Verificaciones Finales
- [ ] Todos los Criterios de Aceptación (`S#` / `UAC`) fueron demostrados empíricamente.
- [ ] Spec-Derived Probes ejecutados y añadidos a la suite permanente de regresión.
- [ ] No hay regresiones en la suite de tests del proyecto.
- [ ] El archivo `BLUEPRINT.md` fue actualizado con el nuevo Slice Vertical en la Sección 3.1.
- [ ] Si se detectaron decisiones estructurales nuevas, se documentaron en `ADR.md`.

**Fecha de Cierre:** `{{YYYY-MM-DD}}`  
**Veredicto Final:** `[ENTREGA CERTIFICADA / GAPS PENDIENTES]`

---

## 8. LOG DE CAMBIOS Y CORRECCIONES (L#)

> 📝 **Registro Verbatim de Requerimientos y Correcciones:**
> Cada interacción o corrección del usuario que altere el rumbo del feature se anexa aquí literalmente.
> Un cambio de requerimiento no destruye la bitácora: añade una entrada `L#`, actualiza únicamente el `S#` afectado y reabre su tarea correspondiente.

- **L1:** `{{REQUERIMIENTO_INICIAL_VERBATIM}}`
