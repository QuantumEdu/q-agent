# Catálogo de Prompts Interactivos de GBrain

> **Propósito:** Plantillas de prompts prediseñadas para consulta, síntesis, decisiones y mantenimiento del grafo de conocimiento en GBrain. Cargar bajo demanda cuando el usuario solicite asistencia o inspiración de prompts.

---

### 1. 🔍 Consulta & Síntesis Contextual
*Búsqueda híbrida (RRF + expansión semántica) con redacción de respuestas y análisis de brechas.*

- **Prompt 1.1 (Briefing de Reunión / Contacto):**
  > *"¿Qué necesito saber antes de mi reunión con `[Persona / Empresa]`? Resume acuerdos previos, compromisos pendientes y notas abiertas."*
- **Prompt 1.2 (Resumen Ejecutivo de Proyecto):**
  > *"Hazme una síntesis del estado actual de `[Proyecto]`. ¿Cuáles han sido los hitos recientes y qué bloqueos existen?"*
- **CLI Command:**
  ```bash
  gbrain query "¿Qué acuerdos abiertos tenemos con [Persona]?"
  ```

---

### 2. 🏛️ Decisiones Técnicas & Arquitectura
*Recuperación de justificaciones de diseño, historial de decisiones pasadas y navegación de dependencias.*

- **Prompt 2.1 (Justificación Histórica / Por qué de una decisión):**
  > *"¿Por qué decidimos utilizar `[Tecnología / Patrón]` en lugar de `[Alternativa]` en el módulo `[Módulo]`?"*
- **Prompt 2.2 (Grafo de Dependencias entre Servicios):**
  > *"¿Qué servicios o librerías dependen de `[Componente]` y cuáles son los contratos de datos clave?"*
- **CLI Commands:**
  ```bash
  gbrain search "arquitectura [modulo]"
  gbrain graph-query [componente] --type depends_on
  ```

---

### 3. 💾 Registro & Capitalización de Conocimiento
*Persistencia de hechos atómicos estructurados y enlace de aristas tipadas en el grafo.*

- **Prompt 3.1 (Guardar Hecho Atómico Vinculado a Entidad):**
  > *"Guarda en GBrain que `[Hecho / Regla / Configuración]` para la entidad `[Entidad/Servicio]`."*
- **Prompt 3.2 (Vincular Entidades en el Grafo de Conocimiento):**
  > *"Conecta la entidad `[Servicio A]` con `[Servicio B]` indicando una relación de tipo `[depends_on / calls / owns]`."*
- **CLI Commands:**
  ```bash
  gbrain remember "La tasa de refresco del token es de 15 minutos" --entity auth-service
  gbrain link auth-service redis-cluster --link-type depends_on
  ```

---

### 4. 📊 Métricas, Trayectorias y Verificación de Consistencia
*Auditoría cronológica de cambios y detección de lagunas de información (Gap Analysis).*

- **Prompt 4.1 (Evolución y Línea de Tiempo de Entidad):**
  > *"Muestra la trayectoria histórica y cambios clave de `[Entidad / Proyecto]` en los últimos meses."*
- **Prompt 4.2 (Detección de Brechas / Gap Analysis):**
  > *"Analiza la información disponible sobre `[Iniciativa]`. ¿Qué datos críticos faltan por documentar o están desactualizados?"*
- **CLI Commands:**
  ```bash
  gbrain eval trajectory [entidad-slug]
  gbrain timeline [entidad-slug]
  ```

---

### 5. 🩺 Diagnóstico, Sincronización y Mantenimiento
*Comprobación de salud de la base de datos (PGLite / Postgres), sincronización Git e ingesta de notas.*

- **Prompt 5.1 (Diagnóstico de Salud Operativa):**
  > *"Ejecuta un diagnóstico del estado del motor de GBrain y reporta si hay inconsistencias."*
- **Prompt 5.2 (Sincronización Incremental Git):**
  > *"Sincroniza los últimos cambios del repositorio local con la base de datos de GBrain."*
- **CLI Commands:**
  ```bash
  gbrain doctor
  gbrain engine status
  gbrain sync
  ```
