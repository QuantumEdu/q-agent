---
id: P7_HYGIENE_AND_BLUEPRINT
titulo: "Higiene Determinista de Código y Consolidación en BLUEPRINT.md"
cuando_usar: "Al completar todas las tareas atómicas de la bitácora activa."
prerequisitos: "100% de tareas verificadas con evidencia en Terminal Evidence Gate (P06)."
entregables: "Código higienizado + BLUEPRINT.md actualizado con el nuevo Slice + Bitácora cerrada."
posicion_en_pipeline: "Paso 7 — Higiene y Consolidación Final"
proyecto: "{{PROYECTO_NOMBRE}}"
fecha: "{{YYYY-MM-DD}}"
---

# P7 — Higiene Determinista y Consolidación de Blueprint

> **Misión:** Garantizar que todo el código entregado cumpla con los estándares de estilo y linters deterministas (sin consumir tokens innecesarios) y actualizar el mapa vivo del sistema (`BLUEPRINT.md`) para reflejar los nuevos Slices Verticales entregados.

---

## 1. Higiene Determinista de Código (Linters y Formato)

### 1.1 Ejecución de Herramientas Nativas
Ejecutar en terminal el formateador y analizador estático oficial del lenguaje:
- **Go:** `gofmt -s -w .` y `go vet ./...` (o `golangci-lint run`)
- **Python:** `black .` y `ruff check .`
- **TypeScript/Node:** `npx prettier --write .` y `npx eslint .`

### 1.2 Regla de Cero Tokens y Candado Bounded Turns (Máximo 2 Pasadas)
- **Si el linter reporta cero errores:** Avanzar de inmediato a la Sección 2 sin redactar explicaciones superfluas. Cero consumo de tokens cuando el código está limpio.
- **Si el linter o compilador reporta errores:**
  - Invocar `q-ci-fixer` para aplicar correcciones quirúrgicas estrictamente sobre los archivos y líneas señalados.
  - **Límite Estricto:** Máximo 2 pasadas de corrección. Quedan prohibidos los ciclos infinitos de ajustes cosméticos. Si tras 2 pasadas persiste un error de fondo, reportarlo explícitamente al usuario.

---

## 2. Consolidación en BLUEPRINT.md

Todo sistema vivo debe mantener su mapa de arquitectura actualizado. Al entregar un slice:

1. **Abrir `BLUEPRINT.md`:**
2. **Actualizar la Sección 3.1 (Catálogo de Slices Verticales):**
   - Registrar el nuevo Slice Vertical implementado:
     - Nombre del Slice y User Stories atendidas (`US-01`, etc.).
     - Archivos de control, storage y plantillas higiénicas empaquetadas.
     - Endpoints/rutas expuestas y formatos de respuesta.
     - Confirmación de sentencias preparadas y escape anti-XSS.
     - Evidencia observable (test pasando).
3. **Actualizar la Sección 11 (Historial de Revisiones):** Incrementar la versión menor e indicar el slice incorporado.
4. **Si se tomó una decisión arquitectónica no prevista:** Registrar el registro en `ADR.md`.

---

## 3. Cierre Formal de la Bitácora

1. En la bitácora activa (`q-tasks/{{FEATURE_NAME}}.md` o `odd/tasks/{{FEATURE_NAME}}.md`):
   - Marcar los checks de la Sección 6 ("Cierre, Revisión e Integración").
   - Actualizar el estado global a: `[ENTREGA CERTIFICADA]`.
   - Registrar la fecha de cierre.

---

## 4. Reporte de Cierre al Usuario

Presentar un resumen conciso de 3 a 5 líneas con los hechos comprobados:
```text
✅ [FEATURE COMPLETADA Y CERTIFICADA]
- Slice Vertical: [Nombre del Slice / Módulo]
- Criterios de Aceptación: [UAC-01, UAC-02 verificados con salida 0]
- Higiene: Linters en verde (0 errores)
- Documentación: BLUEPRINT.md actualizado en Sección 3.1
```
