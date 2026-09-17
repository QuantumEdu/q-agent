# Bitácora de Feature ODD: {{FEATURE_NAME}}
> Documento vivo unificado de desarrollo — Gobernado por el protocolo Organic Driven Development (ODD).
> Ruta canónica: `q-tasks/{{FEATURE_NAME}}.md` (Modo Standalone) o `odd/tasks/{{FEATURE_NAME}}.md` (Modo Gentle-AI).

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

## 2. PERSPECTIVA DE PRODUCT MANAGER (Lente BMAD / Squad Path)

### 👤 User Persona & Dolor Actual
- **Rol / Persona:** [ej. Líder de Proyecto / Operador Técnico / Usuario Final]
- **Fricción / Dolor Actual:** [¿Qué cuello de botella, error manual o falta de visibilidad sufre hoy?]

### 📋 Historias de Usuario Ágiles (User Stories)
- **US-01:** Como **[rol]**, quiero **[capacidad o acción en el sistema]**, para **[beneficio medible en negocio o productividad]**.
  - **Criterio de Aceptación (UAC-01):** [Resultado observable y verificable en la interfaz o respuesta HTTP]
- **US-02:** Como **[rol]**, quiero **[capacidad o acción en el sistema]**, para **[beneficio medible en negocio o productividad]**.
  - **Criterio de Aceptación (UAC-02):** [Resultado observable y verificable en la interfaz o respuesta HTTP]

### 🎯 Hipótesis de Valor de Negocio
[¿Cómo medimos que esta entrega resolvió el dolor del usuario? Métrica observable de éxito.]

---

## 3. ALCANCE Y GOBERNANZA CONSTITUCIONAL (ARQ-01)

### ✅ In Scope (Lo que se construye)
1. [Capacidad 1 vinculada a UAC-01]
2. [Capacidad 2 vinculada a UAC-02]

### 🔴 Out of Scope (Exclusiones deliberadas)
> ⚠️ Cualquier omisión debe estar justificada aquí para evitar Scope Drift no documentado en la auditoría P09.
1. [Elemento diferido y justificación de por qué no entra en este ciclo]

### ⚖️ Cláusulas Constitucionales Aplicables
- [x] **Cláusula 1 (Vertical Slice):** Feature implementado como slice autónomo sin capas pasamanos artificiales.
- [x] **Cláusula 3 (Persistencia Pragmática):** Consultas directas sin hidratación forzada. (Si SQLite: WAL mode + busy timeout).
- [x] **Cláusula 4 (Higiene de Plantillas):** Vistas en archivos `.html` independientes empaquetados (`//go:embed` o template engine nativo). Cero HTML en strings de código.
- [x] **Cláusula 5 (Ciberseguridad):** 100% SQL parametrizado, escape contextual anti-XSS activado, cero secrets.

---

## 4. CHECKLIST DE TAREAS ATÓMICAS (~400 LÍNEAS POR SLICE)

> **Regla de ODD:** Cada tarea debe ser una unidad mínima coherente con sus propios tests y comprobaciones. Tareas estimadas en ~400 líneas de autoría.

- [ ] **TASK-01 [UAC-01] — [Nombre de la tarea, ej. Modelo de almacenamiento y migración SQL]:**
  - *Archivos:* `[ruta/al/storage.go]`, `[ruta/a/schema.sql]`
  - *Acción:* [descripción concreta de la implementación]
  - *Verificación prevista:* [Comando o test para validar]

- [ ] **TASK-02 [UAC-01] — [Nombre de la tarea, ej. Handler HTTP y plantilla higiénica de vista]:**
  - *Archivos:* `[ruta/al/handler.go]`, `[views/modulo/view.html]`
  - *Acción:* [Crear controlador de ruta y archivo html empaquetado]
  - *Verificación prevista:* [Comando curl o test de integración HTTP 200]

- [ ] **TASK-03 [UAC-02] — [Nombre de la tarea, ej. Interacción reactiva HTMX / Alpine]:**
  - *Archivos:* `[views/modulo/fragment.html]`, `[assets/js/...]`
  - *Acción:* [Implementar swap o validación dinámica]
  - *Verificación prevista:* [Prueba de endpoint fragmento]

---

## 5. TERMINAL EVIDENCE GATE (Evidencia Observable en Terminal)

> ⛔ **CANDADO MANDATORIO DE EJECUCIÓN:**
> Queda estrictamente prohibido marcar una tarea como completada (`[x]`) sin registrar en esta tabla la evidencia real de ejecución observada en la terminal.
> Cero falsas completitudes, cero suposiciones, cero mocks permanentes sin autorización.

| Tarea ID | Comando Ejecutado en Terminal | Código de Salida (Exit Code) | Resultado Observado / Evidencia | Estado |
|---|---|---|---|---|
| `TASK-01` | `[ej. go test ./features/reuniones -v]` | `0` | `PASS: TestCreateReunion (0.02s)` | `[VERIFICADO]` |
| `TASK-02` | `[ej. curl -I -s http://localhost:8080/reuniones]` | `0` | `HTTP/1.1 200 OK - Content-Type: text/html` | `[VERIFICADO]` |
| `TASK-03` | `[ej. go vet ./... && golangci-lint run]` | `0` | `Clean - 0 warnings, 0 errors` | `[VERIFICADO]` |

---

## 6. CIERRE, REVISIÓN E INTEGRACIÓN EN BLUEPRINT

### Verificaciones Finales
- [ ] Todos los Criterios de Aceptación (`UAC`) fueron demostrados empíricamente.
- [ ] No hay regresiones en la suite de tests del proyecto.
- [ ] El archivo `BLUEPRINT.md` fue actualizado con el nuevo Slice Vertical en la Sección 3.1.
- [ ] Si se detectaron decisiones estructurales nuevas, se documentaron en `ADR.md`.

**Fecha de Cierre:** `{{YYYY-MM-DD}}`  
**Veredicto Final:** `[ENTREGA CERTIFICADA / GAPS PENDIENTES]`
