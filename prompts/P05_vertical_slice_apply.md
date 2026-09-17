---
id: P5_VERTICAL_SLICE_APPLY
titulo: "Implementación por Slices Verticales — Mínima Indirección e Higiene de Código"
cuando_usar: "Durante la construcción de cada tarea planificada en la bitácora viva."
prerequisitos: "Bitácora P04 creada y aprobada; CONSTITUTION.md vigente."
entregables: "Archivos de código fuente del slice (storage, handlers, templates .html empaquetados)."
posicion_en_pipeline: "Paso 5 — Construcción Atómica"
proyecto: "{{PROYECTO_NOMBRE}}"
fecha: "{{YYYY-MM-DD}}"
---

# P5 — Implementación por Slices Verticales (Apply)

> **Misión:** Construir la funcionalidad rebanada por rebanada (Vertical Slices), garantizando máxima cohesión, mínima indirección y estricta higiene de código según el **Artículo ARQ-01**.

---

## 1. Reglas Sagradas de Construcción

### 1.1 Mínima Indirección (Anti-Pasamanos)
- En operaciones CRUD, formularios y dashboards estándar, el controlador/handler interactúa directamente con la capa de persistencia del propio slice.
- **Prohibido:** Crear interfaces de una sola implementación, servicios pasamanos que solo redirigen llamadas a un repositorio, o DTOs redundantes que clonan exactamente la estructura de la entidad sin aportar valor.

### 1.2 Higiene Estricta de Plantillas y Vistas (Cláusula 4 ARQ-01)
- **Cero HTML en código backend:** Queda terminantemente prohibido construir fragmentos de interfaz o etiquetas HTML concatenando strings dentro de archivos `.go`, `.py`, `.ts` o `.rs`.
- **Vistas en archivos `.html` independientes:** Toda plantilla debe crearse en su propio archivo `.html` legible y bien formateado.
- **Empaquetado Nativo:** Utilizar mecanismos nativos del lenguaje para servir las plantillas (en Go: directivas `//go:embed views/*.html`; en Python: Jinja2 con carga desde paquete; en Node/TS: componentes TSX o plantillas de motor server-side).

### 1.3 Ciberseguridad por Defecto (Cláusula 5 ARQ-01)
- **100% SQL Parametrizado:** Toda sentencia SQL debe usar sentencias preparadas o placeholders (`?` en SQLite/Go, `$1` en PostgreSQL). Jamás concatenar variables del usuario en queries.
- **Escape Contextual Anti-XSS:** Garantizar que el motor de plantillas tenga activado el escape automático de caracteres peligrosos (`<`, `>`, `&`, `"`, `'`).
- **Validación de Entrada:** Validar tipos, longitudes y formatos en el handler antes de tocar el almacenamiento.

### 1.4 Heurística de Autoría (~400 Líneas por Slice)
- Diseñar el código en unidades atómicas y manejables.
- Preferir pequeños slices cohesivos con sus tests respectivos antes que gigantescos monolitos en un solo commit.

---

## 2. Flujo de Trabajo Tarea por Tarea

Para cada tarea pendiente en la bitácora:

```
[Leer Tarea y UAC en Bitácora]
              │
              ▼
[Escribir / Modificar Código del Slice]
(Storage SQL ──► Handler HTTP ──► Template .html)
              │
              ▼
[NO MARCAR CHECKBOX AÚN]
              │
              ▼
[Transicionar de Inmediato a P06 (Terminal Evidence Gate)]
```

> ⚠️ **REGLA DE BLOQUEO:** Queda estrictamente prohibido marcar el checkbox `[x]` en la bitácora al terminar de escribir el código. La tarea permanece en estado pendiente `[ ]` hasta que el Paso 6 ejecute los comandos de terminal y registre la evidencia observable.
