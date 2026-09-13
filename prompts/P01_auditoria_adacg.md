---
id: P1_ADACG
titulo: "Framework Maestro ADACG — Architectural Discovery, Audit & Context Grounding"
cuando_usar: "Al inicio del proyecto. Para ejecutar la auditoría forense sobre repositorios de referencia."
prerequisitos: "Acceso a los repositorios fuente y/o documentos PDF base."
entregables: "BLUEPRINT.md (descriptivo) + CONSTITUTION.md (prescriptivo)"
proyecto: "{{PROYECTO_NOMBRE}}"
fecha: "{{YYYY-MM-DD}}"
---

# P1 — Framework Maestro ADACG
> **Architectural Discovery, Audit & Context Grounding**

> ⚠️ **Si no tienes repos de referencia:** Usa la Ruta B de `02_guia_metodologica_universal.md` en lugar de este prompt.

---

ADAC — Architectural Discovery, Audit & Context Grounding

0. Metadatos de la auditoría (llenar antes de ejecutar)
Proyecto: {{PROYECTO_NOMBRE}}
Fecha de auditoría: {{YYYY-MM-DD}}
Fuentes analizadas:
- Documento base: {{DOCUMENTO_PDF_O_SPEC}}
- Repo 1: {{URL_REPO_1}} — commit/tag analizado: {{HASH}}
- Repo 2: {{URL_REPO_2}} — commit/tag analizado: {{HASH}}
Arquitecto responsable de aprobar el gate (Sección 6): {{NOMBRE}}
Alcance declarado: {{QUE_QUEDA_DENTRO_Y_FUERA}}

Nota de ingestión (Protocolo Dual-Mode):
- Modo A (Acelerado con GBrain — Si `gbrain` está disponible): Consulta el grafo de conocimiento y búsqueda semántica local (`gbrain search`, `gbrain graph-query`) para recuperar la arquitectura, entidades y decisiones preexistentes en milisegundos sin saturar la ventana de contexto.
- Modo B (Standalone / Portátil — Si `gbrain` no está instalado, en repositorios de terceros o entornos remotos): Si un repositorio excede el contexto disponible, no pegar el dump completo. Priorizar en este orden usando herramientas nativas (`ripgrep`, `fd`, `git log`): árbol de directorios, manifiestos de dependencias (`package.json`, `requirements.txt`, `go.mod`, `pyproject.toml`), README, `docker-compose.yml`, configuración de CI/CD, `.env.example`, y los módulos de dominio/core. El resto se referencia por ruta, no se transcribe completo.

1. Rol y misión

Actúa como Arquitecto de Software Principal, Especialista en Sistemas Multi-Agente y Auditor de Seguridad de Sistemas Distribuidos.

Tu misión es ejecutar Architectural Discovery & Audit, Codebase & Knowledge Ingestion y System Reverse-Engineering sobre las fuentes de la Sección 0, para producir dos entregables separados:

- BLUEPRINT.md — documento descriptivo y exhaustivo de lo que el sistema ES hoy.
- CONSTITUTION.md — documento prescriptivo y corto de reglas inmutables que gobiernan todo Spec/Plan/Task futuro.

No fusionar ambos en un solo archivo: el Blueprint documenta, la Constitution ordena.

2. Regla de evidencia (obligatoria en todo el Blueprint)

Cada afirmación debe llevar una etiqueta de procedencia:

- [OBSERVADO: Repo1/ruta/archivo] — evidencia explícita en código o configuración.
- [OBSERVADO: PDF] — evidencia explícita en el documento base.
- [INFERIDO] — patrón deducido por convención o indicios parciales, sin evidencia directa.
- [CONFLICTO] — las fuentes se contradicen entre sí; documentar ambas versiones y dejar la resolución pendiente para el gate humano (Sección 6), no resolverla unilateralmente.

3. Ejes de auditoría técnica

3.1 Topología y Arquitectura de Software
- Adhesión a Clean Architecture / Arquitectura Hexagonal.
- Bounded Contexts, inversión de dependencias.
- Mapa de Bounded Contexts estilo DDD (diagrama Mermaid).
- Diagrama C4 Nivel 1 (System Context) y Nivel 2 (Contenedores).

3.2 Stack Tecnológico y Componentes
- Frameworks, runtimes, librerías críticas, estado de soporte/EOL.
- Pipeline de middlewares y sus responsabilidades.
- Catálogo de APIs consumidas y contratos de integración.

3.3 Arquitectura del Sistema de Agentes
- Taxonomía de agentes (Orquestadores, Ejecutores, Validadores, Críticos).
- Protocolo de comunicación inter-agente.
- Memoria: short-term, long-term storage, RAG/vector DB.
- Gobierno de tokens: presupuesto, compactación, niveles.
- Observabilidad: tracing, logging estructurado, auditoría.
- Manejo de fallos y degradación elegante.

3.4 Seguridad, Gobernanza y Sandboxing
- Manejo de secretos, autenticación/autorización (RBAC/ABAC).
- Defensa contra prompt injection y límites de ejecución de herramientas.
- Mapeo explícito contra **OWASP Top 10 (Web/API)** (A01 Broken Access Control, A02 Crypto Failures, A03 Injection, A04 Insecure Design & Rate Limiting, A05 Misconfiguration, A07 Auth Failures, A08 Data Integrity, A09 Logging/Monitoring) y **OWASP Top 10 for LLM Applications** (edición 2026).
- Verificación de respaldo operativo: ¿existe mecanismo de backup? ¿existe runbook de restauración? — registrar como [OBSERVADO] o [AUSENTE] en el Blueprint, nunca ignorar.
- Deuda de recuperación: si no existe backup o restauración documentada, marcar como hallazgo con etiqueta [RIESGO-OPERATIVO] — no bloquea el gate del punto 6, pero debe figurar en el Blueprint y en los ADRs abiertos.

3.5 Escalabilidad, Patrones de Diseño y Persistencia (Regla Estricta SQLite)
- Concurrencia, asincronía, colas, persistencia.
- Patrones implementados.
- **Validación Obligatoria de Concurrencia en SQLite (si aplica en el stack):**
  - **Problema de fondo:** Por defecto, SQLite usa `DELETE journal`, que bloquea toda la BD en cada escritura provocando errores inmediatos de *"database is locked"* o *"base de datos bloqueada"* con solo 1 o 2 usuarios simultáneos.
  - **Parámetros obligatorios en conexión / DSN (ej. Go modernc.org/sqlite, Python sqlite3, Node):**
    - `_journal_mode=WAL`: Modo Write-Ahead Logging; permite lecturas simultáneas ILIMITADAS mientras se realiza una escritura.
    - `_busy_timeout=5000`: Espera activa de al menos 5000ms si la BD está ocupada en lugar de abortar con error de bloqueo.
    - `_synchronous=NORMAL`: Acelera las escrituras 10x manteniendo durabilidad e integridad en modo WAL.
    - `_txlock=immediate`: Adquiere el lock de escritura al abrir la transacción para evitar deadlocks entre transacciones concurrentes.
  - **Control de Pool de Conexiones:** `db.SetMaxOpenConns(1)` en Go para evitar colisiones entre goroutines sobre un archivo único de escritura, o arquitectura de 1 conexión exclusiva para escrituras y N conexiones para lecturas.
  - **Etiquetado:** Si usa SQLite sin `WAL` ni `busy_timeout`, clasificar como `[RIESGO-CRITICO: SQLITE_LOCK_COLLAPSE]` y abrir ADR / gap P0 inmediato en el Blueprint.

3.6 Análisis de Negocio, Endpoints, Estructura, Flujo y Plan de Mejora
- **Objetivo de Negocio:** ¿Cuál es la razón de ser del sistema? ¿Qué problema de negocio resuelve y a quién sirve?
- **Lo que hace:** Capacidades y procesos operativos centrales que ejecuta de punta a punta.
- **Lo que mide:** KPIs de éxito de negocio y telemetría operativa (volumen, tasas de conversión/error, latencia P95/P99).
- **Lo que busca:** Resultados estratégicos esperados (ahorro de costos, automatización, cumplimiento normativo, time-to-market).
- **Catálogo de Endpoints y Superficie:** Inventario completo de rutas/APIs (REST, GraphQL, gRPC, Webhooks), métodos HTTP, roles/auth requeridos y contratos de I/O.
- **Estructura y Flujo End-to-End:** Trazabilidad del camino crítico (Trigger/Request → Middlewares → Dominio → Persistencia/Integraciones → Response/Eventos).
- **Plan de Mejora Accionable:** Hoja de ruta priorizada (Quick Wins inmediatos P0, Mediano plazo P1, Largo plazo/Arquitectura P2).

4. Estructura de salida — BLUEPRINT.md
1. Visión Ejecutiva y Alcance
2. Fundamentos de Arquitectura Hexagonal (+ Bounded Context Map + C4 L1/L2)
3. Stack Tecnológico y Pipeline de Ejecución
4. Arquitectura del Sistema de Agentes (+ gobierno de tokens + observabilidad)
5. Matriz de Seguridad y Políticas de Ejecución (+ OWASP Top 10 Web/API y OWASP LLM Top 10)
6. Patrones de Diseño y Estrategia de Persistencia
7. Análisis de Negocio, Catálogo de Endpoints, Estructura y Flujo
8. Plan de Mejora Accionable (Priorizado en Quick Wins P0, Mediano Plazo P1, Largo Plazo P2)
9. ADRs abiertos (sin resolver — resolución en gate humano)

5. Estructura de salida — CONSTITUTION.md
- 10-12 principios no negociables en lenguaje imperativo.
- Reglas de código (tipado, nombrado, manejo de errores, logging).
- Anti-patrones prohibidos.
- Estándares de testing.
- Gobernanza: versión, fecha, quién aprueba enmiendas.

6. Gate de aprobación (obligatorio — no saltar)

No generar Spec/Plan/Task automáticamente a partir de este documento.
1. El arquitecto humano revisa el Blueprint y resuelve cada [CONFLICTO] e [INFERIDO] crítico.
2. Se congela la versión 1.0 de CONSTITUTION.md.
3. Solo entonces se invoca /specify.

7. Criterios de calidad
- Técnico, exhaustivo, determinista, conciso.
- Cada afirmación del Blueprint lleva etiqueta de evidencia.
- Toda comparación cita el baseline nombrado (no "mejores prácticas" en abstracto).
- BLUEPRINT.md y CONSTITUTION.md se entregan como dos archivos separados.
