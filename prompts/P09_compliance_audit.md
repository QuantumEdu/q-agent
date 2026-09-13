---
id: P9_CAB_RP
titulo: "CAB-RP — Compliance Audit Blueprint & Remediation Plan"
cuando_usar: "Al cierre de un ciclo completo (MVP o N features). ANTES de etiquetar el sistema como production-ready o cortar un release."
prerequisitos: "Constitution/MAB-PC del proyecto, historial de Specs (OpenSpec), acceso de lectura al repositorio."
entregables: "Documento CAB-RP con: Matriz de Trazabilidad + Tabla PR-Readiness + Specs EARS por gap + Plan priorizado P0/P1."
posicion_en_pipeline: "Fase 6.5 — después de Quality Gates por feature (F6) y antes de entrega completa (F7)"
proyecto: "{{PROYECTO_NOMBRE}}"
fecha: "{{YYYY-MM-DD}}"
---

# CAB-RP — Compliance Audit Blueprint & Remediation Plan

**Contraparte de MAB-PC.** MAB-PC audita y define ANTES de generar Spec/Plan/Task (genera la Constitution). CAB-RP audita DESPUÉS de que el sistema ya fue construido — sobre dominio real, features reales, código real — y su output no es un reporte, es un nuevo lote de specs listos para reentrar al pipeline SDD.

No es un checklist que se tacha. Es un meta-prompt de tres movimientos: **detecta la brecha → la convierte en spec formal (EARS) → la prioriza en un plan de remediación ejecutable.**

---

## Cuándo se ejecuta

Al cierre de un ciclo de desarrollo — MVP completo, o después de N features añadidas — y siempre ANTES de etiquetar el sistema como "production-ready" o cortar un release. No se ejecuta por feature individual; se ejecuta contra el sistema como un todo.

## Inputs requeridos

- **Constitution / MAB-PC** del proyecto, si existe (contexto de negocio y decisiones ya tomadas)
- **Historial de Specs** (Contract Schema / OpenSpec: spec → plan → task de cada feature entregada)
- **Acceso de lectura al repositorio** (código, historial de commits, PRs, workflows de CI)
- **Una línea de contexto de negocio** — qué resuelve el sistema, para calibrar qué categorías aplican y cuáles no (un backoffice interno no necesita el mismo nivel de DR que un sistema con datos de clientes)

---

## Rol del ejecutor

Actúas como un auditor de arquitectura senior haciendo un *pre-release compliance audit*. No felicitas el trabajo hecho. No repites lo que ya está bien — lo mencionas en una línea y avanzas. Tu output tiene valor en las brechas que encuentras y en qué tan accionable dejas cada una. Cada brecha que reportes sin convertir en spec formal es una brecha que vas a tener que volver a explicar la próxima vez.

## Invariantes Operativos de Auditoría (Heredados de q-audit-readonly)

1. **Inmutabilidad Absoluta en Disco**: Esta auditoría es 100% de solo lectura. Queda estrictamente prohibido usar herramientas de edición (`replace_file_content`, `write_to_file`, `sed`, `git checkout .`, etc.) sobre el código fuente del proyecto auditado. Al finalizar, `git status -s` debe ser idéntico al estado inicial (salvo el reporte `AUDIT_REPORT.md` generado en la ruta designada).
2. **CodeGraph Primero**: Cuando la herramienta `codegraph` esté disponible en el entorno, utilizarla preferentemente para resolver grafos de llamadas, dependencias y blast radius antes de realizar búsquedas textuales ciegas con grep.
3. **Tolerancia Cero a Completitudes Falsas (Anti-Mock / Fake Data Check)**: Verificar rigurosamente que las tareas marcadas como completadas `[x]` en `tasks.md` no dependan de mocks no autorizados, datos estáticos inventados en memoria o valores precargados en formularios/APIs para simular funcionalidad inexistente. Si una tarea simula integración real con stubs permanentes: **`❌ Gap P0`**.

---

## Fase 1 — Matriz de Trazabilidad SDD y Calibre

Por cada feature entregada en el sistema, verificar cuatro aspectos clave:

| Verificación | Criterio de paso |
|---|---|
| **Calibre asignado** | ¿Fue ejecutado como Nivel 1 (Fast-Track) o Nivel 2 (Full SDD)? Si fue Nivel 1, verificar que NO haya tocado Dominio ni BD sin proposal/spec. Si violó esta regla: `❌ Gap (Calibre no autorizado)`. |
| **Spec origen** | Para Nivel 2: Existe un spec identificable (id + versión) que originó la feature. Para Nivel 1: Existe commit atómico con test unitario verificable. |
| **Referencia en código** | El código, commit o PR referencia el spec/task o issue que lo generó con trazabilidad. |
| **Drift** | Lo implementado coincide con lo especificado — o el drift está documentado y justificado. |

**Output de esta fase:** tabla con estado por feature — `✅ Trazable` / `⚠️ Drift no documentado` / `❌ Sin spec origen` / `❌ Violación de Calibre`. Cualquier `❌` es candidato automático a Fase 3.

> 💡 **Auditoría Dual-Mode:** Si `gbrain` está disponible en el host, ejecuta `gbrain doctor` para detectar enlaces rotos (`dead-links`), hashes de contenido duplicados (`content_hash_duplicates`) y anomalías en el grafo. Si no está disponible, audita mediante `git log`, `ripgrep` y diffs de commits.

---

## Fase 2 — Checklist de Production-Readiness

Categorías con criterio verificable contra el sistema real, no contra intención. Cada ítem recibe uno de cuatro veredictos — no es binario:

- `✅ Cumple` — verificado con evidencia (ruta, línea, commit)
- `❌ Gap` — no cumple y aplica a este sistema → pasa a Fase 3
- `⚪ No aplica` — el ítem no aplica a este desarrollo específico, **con justificación de negocio explícita** (ej.: "sin DR: sistema de solo lectura, reconstruible desde la fuente en <1h")
- `❓ No verificable` — no se pudo confirmar en esta corrida, **con motivo explícito** (ej.: sin acceso a navegador/staging, sin logs disponibles). No es aprobado por default ni se trata como gap automático — queda reportado aparte para que la Fase 4 decida si bloquea

`⚪ No aplica` sin justificación, o `❓ No verificable` sin motivo, se tratan como `❌ Gap`. La justificación es lo que distingue "no lo pensamos" de "decidimos conscientemente no hacerlo" — esa distinción es la que evita reabrir la misma discusión en el siguiente ciclo o en el siguiente proyecto.

### 0. Arquitectura Base (Clean + Hexagonal integradas)

La única categoría que no nace de una NFR diferible — nace de la Constitution (P1) y de la clasificación de P2. Se audita aquí de todos modos, por dos razones independientes entre sí: (1) la arquitectura se erosiona con el tiempo aunque haya estado bien el día 1 — la feature 7 mete una consulta directa en un controlador y nadie lo nota hasta que se busca; (2) en un proyecto legacy/brownfield auditado con CAB-RP puede que nunca haya existido un P1/P2 formal — este es el único punto donde esos huecos van a salir a la luz.

- Regla de dependencias intacta: `domain/` no importa infraestructura ni frameworks en ningún punto del código (verificable por grep de imports, no por revisión manual selectiva)
- Los patrones mínimos requeridos (5) están implementados — no solo nombrados en un comentario — y cada uno tiene justificación trazable a P2 ("qué problema resuelve" + "por qué no basta algo más simple")
- TDD real en dominio e invariantes críticos — cobertura sobre reglas de negocio, no solo sobre el happy path del controlador
- Si el proyecto es brownfield y nunca tuvo P1/P2 formal: reconstruir aquí, retroactivamente, qué clasificación (Prototipo/Simple/Profesional/Crítico) le hubiera correspondido, y qué tan lejos está el estado actual de ese nivel
- **Persistencia y Concurrencia (Regla Estricta para SQLite):**
  Si el sistema utiliza SQLite en cualquier módulo o servicio (ej. Go modernc.org/sqlite, Python, Node):
  - **WAL Mode (`_journal_mode=WAL` / `PRAGMA journal_mode=WAL;`):** Verificable en DSN o init de BD. Permite lecturas simultáneas ilimitadas durante escrituras.
  - **Busy Timeout (`_busy_timeout=5000` / `PRAGMA busy_timeout=5000;`):** Espera activa mínima de 5000ms en lugar de fallar inmediatamente.
  - **Sincronización (`_synchronous=NORMAL`):** Acelera escrituras 10x manteniendo integridad en WAL.
  - **Bloqueo Transaccional (`_txlock=immediate`):** Adquisición inmediata del write-lock para evitar deadlocks entre transacciones concurrentes.
  - **Límite de Conexiones:** `db.SetMaxOpenConns(1)` en Go para escrituras (o separación 1 writer / N readers) para evitar colisiones de goroutines sobre el archivo.
  *Veredicto:* Si SQLite usa `DELETE journal` por defecto o carece de `busy_timeout`: **`❌ Gap P0` Bloqueante** inmediato (riesgo inminente de fallo *"database is locked"* ante concurrencia básica de 2+ usuarios).

Distinto de la Fase 1 (Trazabilidad): esa verifica spec→código por feature individual; esta verifica la arquitectura como sistema completo — una feature puede ser perfectamente trazable y aun así violar la regla de dependencias.

**A diferencia de las demás categorías, un `❌ Gap` aquí es P0 por default en Fase 4** — no se evalúa caso por caso como el resto. Deuda arquitectónica no es aditiva como la falta de telemetría; compromete la validez de todo lo que las otras ocho categorías intentan verificar. Un `❌` aquí es también la señal más clara para invocar P3 antes de seguir con el resto del checklist — reconciliar el blueprint primero tiene más sentido que auditar sobre uno que ya no describe el sistema real.

### 1. Usabilidad / Interfaz

Categoría con volumen propio — no se resuelve en tres bullets, requiere una auditoría dedicada. Ejecutar como auditor de UI/UX y control de calidad: inspeccionar código y, si el ejecutor tiene esa capacidad, correr la app en navegador (desktop y móvil).

Verificar: tipografía y jerarquía; color, contraste y consistencia; espaciado, alineación y responsive; integración entre pantallas/componentes/formularios/datos; animaciones (propósito, fluidez, rendimiento, `prefers-reduced-motion`); interactividad (botones, enlaces, menús, modales, formularios); estados (hover, focus, disabled, loading, vacío, éxito, error); navegación (mouse, teclado, móvil); flujos completos (enlaces rotos, errores de consola o red).

**Output de esta categoría** — más detallado que el resto porque el volumen de hallazgos lo justifica:
1. Veredicto general
2. Tabla de hallazgos: severidad | pantalla/componente | evidencia | impacto | corrección propuesta
3. Top 5 correcciones prioritarias
4. Aspectos no verificables y motivo → alimenta directamente el estado `❓` de esta fase

**Heurística de control:** ¿una persona que entra por primera vez sabría qué hacer en cada pantalla sin instrucciones? Si la respuesta no es un "sí" evidenciable, hay gap de usabilidad aunque el resto de la categoría pase.

Diagnóstico primero, sin tocar código. La corrección se autoriza después, explícitamente, y acotada a los hallazgos críticos — mismo principio que rige a todo CAB-RP: el output es plan, no parche.

### 2. Observabilidad
- Logs estructurados (no `print`/`console.log` sueltos) en las rutas críticas
- Correlación de logs por request/transacción (trace id o equivalente)
- Al menos un canal de alerta configurado para fallos críticos

### 3. Telemetría
- Puerto de telemetría existe en la capa de dominio (hexagonal), independientemente de qué tan implementado esté el adaptador
- Eventos de uso clave del negocio identificados y capturados (no telemetría genérica de infraestructura únicamente)

### 4. Versionado — dos capas, auditar por separado
- **Software:** versionado semántico, changelog actualizado
- **Specs:** el Contract Schema tiene su propio versionado, trazable a las versiones de software que lo implementaron

### 5. Flujo mínimo de GitHub
- Rama principal protegida (no push directo)
- PR template mínimo (qué cambia, cómo se probó)
- Al menos un gate de CI antes de merge (build o tests, no ambos son opcionales)

### 6. Sistema de respaldo / recuperación

**Auditar en dos subcapas independientes:**

#### 6a. Backup (respaldo)
- Backup automatizado existe y corrió al menos una vez **con éxito verificado** — no basta que el script exista, se requiere evidencia de ejecución (log de salida, archivo generado con timestamp, checksum)
- Política de retención definida (aunque sea mínima): cuántos backups se guardan y por cuánto tiempo
- El backup cubre **todos los datastores críticos** del sistema (DB principal, archivos de estado, configuración sensible) — un backup parcial que omite la DB se trata como ausencia de backup

#### 6b. Recuperación / importación
- Existe un procedimiento documentado (aunque sea un runbook mínimo) para restaurar desde un backup — "backup existe pero no sé cómo restaurarlo" se trata como `❌ Gap`
- El procedimiento fue probado al menos una vez (evidencia: log de restore en staging o copia en frío) — si nunca se probó: `❓ No verificable`, no `✅ Cumple`
- Existe mecanismo de **importación** cuando aplique (ej.: migración desde otro sistema, onboarding de datos legados): documentado aunque sea a nivel de comando o script

#### Regla de priorización en el reporte final

Al reportar hallazgos de esta categoría, distinguir entre:

- **Requerido** (`P0`): ausencia total de backup, o backup sin procedimiento de restauración documentado, o backup que nunca corrió
- **Opcional recomendado** (`P1`): backup no probado en restore real, política de retención no definida, importación no documentada pero el sistema no lo necesita hoy

Un sistema puede tener backup básico (`P0 ✅`) pero tener pendientes opcionales (`P1 ❌`) — el reporte los separa explícitamente para que la priorización sea ejecutable, no una lista plana donde todo parece igualmente urgente.

- RTO/RPO definidos aunque sea de forma mínima (aceptable: "restauración manual, RPO 24h" — lo que no es aceptable es la ausencia total de definición)

### 7. Seguridad y Compliance (OWASP Top 10 Crítico)

La seguridad no se evalúa únicamente con dos bullets genéricos; requiere una verificación explícita contra los vectores de ataque más comunes y destructivos (OWASP Top 10):

- **A01: Broken Access Control (Control de Acceso):**
  - Cada endpoint y ruta protegida aplica RBAC estricto según el rol mínimo necesario (Admin, Técnico, etc.).
  - Prevención de IDOR (Insecure Direct Object Reference): el usuario no puede mutar ni consultar entidades de otros contextos/planteles modificando simplemente el `id` en la URL o payload.
- **A02: Cryptographic Failures (Fallas Criptográficas):**
  - Contraseñas almacenadas exclusivamente con funciones de derivación de claves robustas y salteadas (Argon2id o Bcrypt, nunca MD5/SHA1/SHA256 plano).
  - Tráfico HTTP sensible protegido; cabecera HSTS forzada en producción.
  - Cero secretos o tokens API hardcodeados en el código fuente (verificable con `git-secrets`, `trufflehog` o escaneo estático).
- **A03: Injection (Inyecciones SQL, NoSQL, OS Command):**
  - Consultas a base de datos ejecutadas 100% mediante ORM parametrizado o sentencias preparadas; cero concatenación de cadenas SQL (`f"SELECT * FROM ... WHERE id={id}"` es `❌ Gap P0` inmediato).
  - Llamadas a comandos del sistema (`subprocess`) sin `shell=True` con datos provenientes del usuario.
- **A04: Insecure Design & Rate Limiting:**
  - Control de tasa de peticiones (Rate Limiting) implementado y probado en rutas críticas (ej. `/auth/login`, exportaciones masivas) para prevenir denegación de servicio o scraping abusivo.
- **A05: Security Misconfiguration (Configuración de Seguridad):**
  - Cabeceras de seguridad activas en respuestas HTTP: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`.
  - Cookies de sesión y autenticación configuradas con flags de protección: `HttpOnly`, `SameSite=Lax` (o `Strict`), y `Secure` (en HTTPS).
  - Modo `DEBUG` desactivado por defecto en configuraciones de producción.
- **A07: Identification and Authentication Failures:**
  - Protección contra ataques de fuerza bruta en endpoints de login.
  - Expiración de tokens JWT acotada (ej. $\le$ 30-60 min para access token) con tiempo definido para refresh tokens.
- **A08: Software and Data Integrity Failures:**
  - Validación y tipado estricto de todos los payloads de entrada mediante esquemas (Pydantic, Zod, etc.) antes de alcanzar la capa de dominio.
  - Escaneo de dependencias en busca de CVEs conocidas (`pip audit`, `safety`, `npm audit`).
- **A09: Security Logging and Monitoring:**
  - Registro estructurado de eventos de autenticación, errores de autorización y operaciones administrativas críticas.
  - Sanitización de logs: prohibido registrar contraseñas, tokens JWT, números de tarjetas o PII sin enmascarar.

### 8. Documentación
- README suficiente para que alguien nuevo levante el entorno sin preguntar
- Decisiones arquitectónicas relevantes registradas (ADR o equivalente) — especialmente las que se desviaron de la Constitution original

**Output de esta fase:** tabla de 9 filas (una por categoría, incluyendo Arquitectura Base y Seguridad OWASP) con columnas `Ítem | Veredicto (✅/❌/⚪) | Evidencia o Justificación`. Cualquier `❌` es candidato automático a Fase 3.

---

## Fase 3 — Conversión de brecha en spec (sintaxis EARS)

Cada ítem que no pase Fase 1 o Fase 2 se convierte en spec, no en pendiente de lista. Plantilla:

```
GAP: [categoría] — [qué falta, en una línea]
CONTEXTO: [por qué existe la brecha — decisión consciente diferida vs. omisión]

EARS:
Cuando [condición/trigger del sistema],
el sistema deberá [comportamiento esperado],
de forma que [criterio de aceptación verificable].
```

No se documenta la brecha sin este paso. Una brecha sin spec formal vuelve a perderse en el siguiente ciclo.

---

## Fase 4 — Plan de Remediación

Cada spec generado en Fase 3 se prioriza:

- **P0 — bloqueante:** el sistema no debería llamarse "terminado" sin esto (ejemplo típico: backup ausente, secretos hardcoded, rama principal sin protección — y **todo `❌` de la categoría 0**, sin excepción)
- **P1 — diferible:** mejora la madurez del sistema pero no bloquea el release actual (ejemplo típico: telemetría de eventos de negocio más granular, cobertura de accesibilidad AA completa)

**Output final del CAB-RP** — un documento con:

1. Matriz de trazabilidad (Fase 1)
2. Tabla de checklist por categoría con veredicto seleccionable ✅/❌/⚪ y evidencia o justificación por ítem (Fase 2, incluyendo OWASP Top 10)
3. Lote de specs nuevos en formato EARS, uno por gap (Fase 3)
4. Plan priorizado P0/P1 con los specs de Fase 3 ordenados (Fase 4)
5. Evaluación de Impacto de Negocio y Plan de Mejora Estratégico (Alineación entre el objetivo de negocio, lo que hace, lo que mide, lo que busca, los endpoints, estructura/flujo y roadmap de evolución)

Este documento entra directo al runtime de SDD como si los specs P0 hubieran existido desde el origen — la Constitution del proyecto se actualiza para reflejarlos, y se generan Plan/Task normalmente a partir de ahí.

---

## Ubicación en el pipeline real (P1-P7 + F5-F8)

Lo descrito antes como "Fase 1 a Fase 4" del flujo de 8 fases era una versión parafraseada. Estos son los prompts reales, más precisos y en un par de puntos distintos de lo que se había inferido:

| Descrito antes como | Prompt real | Diferencia que importa |
|---|---|---|
| F1.1 (Ingestión) + F2.1a (Constitution) | **P1 — Discovery & Audit (MAB-PC)** | Mucho más riguroso: etiquetado de evidencia obligatorio, C4 L1/L2, Bounded Context Map, taxonomía de agentes, OWASP LLM Top 10. Produce BLUEPRINT.md + CONSTITUTION.md, con gate humano obligatorio antes de continuar |
| F2.1b (Decisión por Contexto) | **P2 — Context Engineering** | Es la misma pieza de prevención señalada antes — ahora con el detalle real: clasificación de trabajo, arquitectura hexagonal ligera (domain/application/infrastructure, dependencia en un solo sentido), justificación obligatoria de cada patrón, TDD selectivo por criticidad |
| *(sin equivalente previo)* | **P3 — Evolución Arquitectónica** | No estaba en la versión anterior. Reconcilia el blueprint contra el código real ya escrito — mismo movimiento que la Fase 1 de CAB-RP, pero a nivel arquitectura en vez de a nivel feature |
| *(sin equivalente previo)* | **P4 — /propose** | Tampoco estaba. Define IN/OUT SCOPE formal antes del spec — importa directamente a CAB-RP, ver abajo |
| F3.1a (spec.md) | **P5 — /spec (BDD)** | Formato Gherkin explícito, prohíbe detalles de implementación dentro del spec |
| F3.1b (design.md) | **P6 — /design** | Incluye matriz de mitigación de riesgos que la versión anterior no tenía |
| F4.1a (tasks.md) | **P7 — /tasks** | Orden de capas explícito, máximo 15 tareas por fase, tag `[TDD]` por tarea |

F5 (Implementación/TDD), F6 (Quality Gates/Seguridad), F7 (Loops/Entrega) y F8 (Operación/Incidentes) siguen válidos tal como se describieron — no llegó reemplazo para esos todavía, ahí no cambia nada.

**Dos conexiones nuevas que sí modifican a CAB-RP:**

1. **P4 es la fuente de verdad de `⚪ No aplica`.** Si un ítem quedó fuera de alcance, ya debería figurar en el "OUT OF SCOPE (Diferido)" de `proposal.md`. Antes de correr CAB-RP, cruzar cada `⚪ No aplica` contra ese documento: si coincide, la justificación ya existe y solo se cita; si no coincide, no es un `⚪` limpio — es scope drift no documentado cuando se decidió, y eso en sí mismo es un hallazgo de la categoría 8 (Documentación).

2. **Un drift detectado en la Fase 1 de CAB-RP dispara P3, no se resuelve dentro de CAB-RP.** Si la matriz de trazabilidad encuentra `⚠️ Drift no documentado`, el output correcto no es que CAB-RP intente reconciliarlo por su cuenta — es invocar P3 para producir BLUEPRINT_V2.md + DIFF_V1_VS_V2.md, y que ese diff sea el insumo real del spec de Fase 3.

**Sigue vigente:** que P2 se haya ejecutado por feature durante el desarrollo, no solo al final, es la condición para que CAB-RP encuentre pocos gaps. P2 previene la sobre-especificación; CAB-RP la detecta si de todos modos ocurrió, o detecta lo contrario — features sub-especificadas porque se les asignó menos rigor del que en realidad necesitaban.

---

## Nota de portabilidad

Este documento es agnóstico de herramienta — funciona igual como prompt para cualquier LLM con acceso a lectura de repositorio, o como checklist manual. No depende de tool calls específicos de ningún asistente. Si se ejecuta con un agente que tiene acceso real al repo, pedirle explícitamente que **muestre evidencia** (ruta de archivo, línea, commit) por cada ítem marcado `✅ Cumple` — sin evidencia, el ítem baja a `❓ No verificable`, nunca sube a aprobado por default.
