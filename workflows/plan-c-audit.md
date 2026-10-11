# Protocolo Plan C — Auditoría Forense Atómica CAB-RP 2.0 & MAB-PC

> **Principio Fundamental:** *"Completeness is a filesystem property, not an LLM output property."*  
> (La completitud es una propiedad del sistema de archivos, jamás del texto libre generado por un LLM).

Este workflow se ejecuta cuando el usuario selecciona **Plan C (Audit)** en el Paso 0 de `q-agent` o se ejecuta una auditoría pre-release formal de código.

---

## ⛔ INVARIANTES NO NEGOCIABLES DEL AUDITOR (Reglas Duras de Bloqueo):

1. **Inmutabilidad Absoluta en Disco & Cero Modo Mixto (Audit + Fix):**
   - El auditor es estrictamente de solo lectura sobre el código del sistema (`src/`, `internal/`, `cmd/`, `tests/`).
   - ⛔ **PROHIBIDO SALTAR A PLAN F:** Queda terminantemente prohibido modificar código, crear parches en caliente o intentar corregir errores antes de que la auditoría completa esté validada y certificada en disco. Un auditor que codifica en caliente corrompe la auditoría.
2. **Prohibición de Informes Monolíticos Generados por LLM:**
   - ⛔ **PROHIBIDO redactar `AUDIT_REPORT.md` o conclusiones a mano en el chat.** Ningún LLM puede "resumir" la auditoría en texto libre. Todos los entregables finales son generados deterministamente por herramientas de software a partir de archivos individuales en disco.

---

## 🔄 PIPELINE OBLIGATORIO DE ATOMIC DISPATCH (5 Fases Secuenciales):

### Fase C1: Descubrimiento y Constitución Base
1. Crear la rama de auditoría aislada: `git checkout -b audit/$(date +%Y%m%d)-<nombre-proyecto>`.
2. Verificar o inicializar `CONSTITUTION.md` en la raíz (usando `templates/CONSTITUTION.md` con el Artículo Constitucional ARQ-01).
3. Ejecutar `prompts/P01_auditoria_mab_pc.md` para producir el mapa estructural base `BLUEPRINT.md`.

### Fase C2: Atomic Wave Dispatch (Olas Paralelas y Generación de Archivos Atómicos)
1. Cargar el manifiesto canónico: `references/audit-manifest.yml`.
2. Identificar el nivel de madurez exigido (por defecto **Nivel 0: MVP/Bootstrap** [5 ítems], **Nivel 1: Growth** [13 ítems], o **Nivel 2: Maturity** [17 ítems]).
3. **Despacho Concurrente en 4 Olas Paralelas (Parallel Audit Waves):**
   Para evitar la saturación de tokens y el fenómeno *Lost in the Middle*, los ítems se despachan agrupados temáticamente por afinidad de alcance (`scope_patterns`). Cada ola puede ejecutarse mediante subagentes concurrentes (`invoke_subagent`) o llamadas atómicas aisladas en lote:
   - 🌊 **Wave 1: Seguridad & Secretos** (`A02`, `A09`, `A10`, `A11`): Escaneo perimetral sin efectos colaterales (fugas de credenciales, inyecciones, RBAC y SSRF).
   - 🌊 **Wave 2: Arquitectura, Capas & Contratos** (`A01`, `A06`, `A13`, `A16`): Límites estructurales, acoplamiento hexagonal, catálogo REST/OpenAPI, complejidad y multi-tenancy.
   - 🌊 **Wave 3: DevOps, Calidad & Confiabilidad** (`A03`, `A04`, `A05`, `A12`, `A14`, `A17`): Gates CI/CD, infraestructura de tests, errores fatales/500, drift de dependencias, observabilidad y resiliencia.
   - 🌊 **Wave 4: Frontend, Diseño & Accesibilidad** (`A07`, `A08`, `A15`): Adherencia al design system, WCAG 2.1 AA (a11y/focus traps) y rendimiento de renderizado.
   - 🌊 **Wave 5: Evolución Estratégica MAB-PC** (`E01` a `E05`, opcional): Latencia asíncrona, UX ergonomía, dominio de negocio, benchmarking competitivo e innovación no contemplada.
4. **Por cada ítem forense (`A01` a `A17`) del nivel activo:**
   - Invocar `prompts/P01b_audit_item.md` asignando estrictamente sus `scope_patterns`.
   - Inspeccionar solo los archivos asignados (aislamiento total de contexto; prohíbese inyectar el repositorio completo).
   - Generar el archivo atómico formal: `audit/A{ID}-{slug}.md` respetando la plantilla `templates/audit-item.md` (frontmatter obligatorio, veredicto `passed|failed`, severidad, tags de evidencia `[OBSERVADO: ...]` y especificación EARS en caso de fallo).
5. **Por cada ítem de evolución estratégica MAB-PC (`E01` a `E05`):**
   - Invocar `prompts/P01c_strategic_item.md` con su alcance asignado.
   - Generar el archivo atómico formal: `audit/E{ID}-{slug}.md`.

### Fase C3: COMPUERTA MECÁNICA DE VALIDACIÓN (Hard Blocking Gate)
El agente DEBE ejecutar en la terminal del host:
```bash
python3 tools/q-audit-validator/validate_audit.py --mode manifest --level [0|1|2]
```
⛔ **CANDADO DE BLOQUEO ABSOLUTO:**
- Si el código de salida es `1` (`RESULT: REJECTED — Audit items are incomplete`):
  - El agente tiene **ESTRICTAMENTE PROHIBIDO** interactuar con el usuario, dar por terminada la auditoría o proponer soluciones.
  - El agente DEBE leer `audit/AUDIT_GAPS.json` generado por el validador, identificar los ítems faltantes o con frontmatter inválido, y ejecutar las pasadas necesarias hasta que todos los archivos existan y cumplan la especificación.
  - Solo cuando el validador retorne código de salida `0` (`RESULT: PASSED`), el agente tiene autorización para proceder a la Fase C4.

### Fase C4: Agregación Determinista (Cero Tokens / Cero Alucinación)
Con el 100% de los archivos atómicos validados en el filesystem, el agente ejecuta:
```bash
python3 tools/q-audit-aggregator/generate_report.py --level [0|1|2]
```
Este script en Python ensambla deterministamente sin consumir tokens del LLM:
1. `audit/AUDIT_REPORT.md` (Informe integral consolidado y matriz de trazabilidad).
2. `audit/PLAN_DE_MEJORA.md` (Plan priorizado de remediación P0/P1/P2).
3. `audit/REMEDIATION_ISSUES.md` (Taxonomía de issues lista para GitHub Issues).
4. `audit/PROPUESTA_EVOLUTIVA.md` (Evolución estratégica de producto y UX E01–E05).

### Fase C5: Presentación Ejecutiva y Retrospectiva
1. Presentar en el chat el resumen ejecutivo estructurado **únicamente a partir de los datos consolidados por `generate_report.py`**.
2. Mostrar tabla de Gaps detectados con severidades.
3. Proporcionar enlaces a los archivos en `audit/`.
4. Invocar `skills/q-session-wrap` for local-first audit persistence; external stores remain optional.
