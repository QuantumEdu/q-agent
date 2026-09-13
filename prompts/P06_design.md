---
id: P6_DESIGN
titulo: "Diseño Técnico Detallado y Contratos — /design"
cuando_usar: "Para definir los contratos exactos de interfaces, DTOs y esquemas de base de datos antes de codificar."
prerequisitos: "specs/{{FEATURE}}.md aprobados."
entregables: "openspec/changes/{{CHANGE_ID}}/design.md"
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P6 — Diseño Técnico Detallado y Contratos
> `/design`

---

Actúa como Arquitecto de Software Principal.

Contexto:
Basado en `specs/{{FEATURE}}.md`, la Constitución y las reglas de Arquitectura Hexagonal Ligera en {{BACKEND_STACK}}, genera el documento técnico en `openspec/changes/{{CHANGE_ID}}/design.md`.

Contenido Requerido:

1. Diagrama de Secuencia Extremo a Extremo (Mermaid):
   - Flujo síncrono y asíncrono desde el cliente hasta la persistencia y de vuelta.

2. Contratos de Interfaces y Estructuras de Dominio (Arquitectura Hexagonal):
   - **Entidades de Dominio**: Structs/clases puras con validación de invariantes (sin importar librerías externas ni ORMs).
   - **Puertos de Entrada (Casos de Uso)**: Interfaces en `application/` que orquestan las operaciones de negocio.
   - **Puertos de Salida (Infraestructura)**: Interfaces en `domain/` que definen los contratos con el exterior:
     * *Puerto de Persistencia*: Métodos CRUD, transaccionalidad y consultas tipadas.
     * *Puerto de Durabilidad & Respaldo*: Hook para instantáneas consistentes (ej. backup/export seguro sin locks).
     * *Puerto de Telemetría & Observabilidad*: Emisión de eventos de negocio tipados, métricas y tracing con CorrelationID.
   - **DTOs y Mapeadores**: Estructuras de transferencia desacopladas de las entidades internas.

3. Esquema de Base de Datos y Persistencia:
   - DDL exacto con tipos de datos nativos, claves primarias, claves foráneas e índices.
   - Configuraciones del motor: si es SQLite, especificar obligatoriamente DSN de alta concurrencia (`_journal_mode=WAL&_busy_timeout=5000&_synchronous=NORMAL&_txlock=immediate`) y control de pool (`db.SetMaxOpenConns(1)` para escrituras en Go o 1 writer / N readers) para prevenir bloqueos de concurrencia.
   - Estrategia de migración de esquema versionada y reversible.

4. Protocolo de Comunicación y APIs (si aplica):
   - Esquemas JSON / Protobuf exactos para requests y responses.
   - Códigos de error tipados y mapeo HTTP/gRPC correspondiente.
   - Eventos de streaming y formato de payloads en tiempo real.

5. Matriz de Mitigación de Riesgos Técnicos:
   - Tabla: Riesgo Técnico → Probabilidad → Impacto → Estrategia de Mitigación Concreta.

Reglas No Negociables de Arquitectura:
- **Aislamiento estricto de dominio**: Las interfaces y entidades de dominio NO deben importar tipos de librerías externas, frameworks HTTP, drivers de BD ni SDKs de terceros.
- **Inversión de dependencias**: La capa de infraestructura depende e implementa las interfaces de dominio, jamás al revés.
- **Observabilidad por diseño**: Ninguna operación crítica del sistema se diseña sin su respectivo evento o trace en el puerto de telemetría.
