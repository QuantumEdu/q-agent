# Guía de Contribución a q-agent

¡Gracias por tu interés en contribuir a **q-agent**! Este proyecto es un orquestador maestro de desarrollo agéntico multimodelo diseñado para garantizar calidad determinista, ejecución disciplinada y trazabilidad completa.

---

## 🧭 1. Principios de Diseño y Filosofía

Cualquier contribución a este repositorio debe respetar los principios arquitectónicos centrales:

1. **Article ARQ-01 (Vertical Slices by Default):**
   - Prefiere siempre una rebanada vertical completa (de extremo a extremo: CLI, lógica y persistencia/salida) antes que capas horizontales abstractas incompletas.
   - Mínima indirección: no añadas fábricas, adaptadores o capas de indirección especulativas a menos que existan al menos dos implementaciones concretas activas.
2. **"Completeness is a filesystem property, not an LLM output property":**
   - Los artefactos de salida deben validarse contra el sistema de archivos real y esquemas estructurados, nunca asumiendo que el texto generado por un modelo es suficiente.
3. **Zero-Mock Terminal Evidence:**
   - Toda verificación, fix o feature debe incluir evidencia de ejecución real en terminal con salida y código de retorno verificables (`exit 0`). Nunca emplees mocks sintéticos que oculten errores de entorno o CLI.
4. **Cero Dependencias Externas en CLI Core:**
   - Las utilidades en `tools/` (`q_cockpit.py`, `q_checklist.py`, `validate_audit.py`, `generate_report.py`) utilizan exclusivamente la biblioteca estándar de Python (>= 3.10). No agregues dependencias pesadas de terceros sin discusión previa vía ADR.

---

## 🏷️ 2. Taxonomía de Issues y Clasificación

El repositorio utiliza una taxonomía multidimensional de etiquetas (labels) para clasificar todo trabajo:

### A. Dimensión `type` (Naturaleza del trabajo)
- `type:feature`: Nueva funcionalidad o capacidad agéntica.
- `type:fix`: Corrección de un fallo o regresión.
- `type:adr`: Architecture Decision Record formal.
- `type:nfr-gap`: Déficit en requerimientos no funcionales detectado en auditoría.
- `type:retrospective`: Análisis de cierre de ciclo o lecciones aprendidas.
- `type:audit`: Hallazgo directo de auditoría.
- `type:setup`: Configuración de entorno o infraestructura.
- `type:chore`: Tareas de mantenimiento o refactor sin impacto funcional directo.

### B. Dimensión `priority` (Urgencia)
- `priority:critical`: Bloquea el flujo del orquestador (P0 inmediato).
- `priority:high`: Debe resolverse en la iteración actual.
- `priority:medium`: Programado para el siguiente ciclo.
- `priority:low`: Backlog o mejora incremental.

### C. Dimensión `scope` (Área del sistema)
- `scope:arch`: Arquitectura, contratos y `SKILL.md`.
- `scope:api`: Interfaces de línea de comandos (CLI) y contratos de entrada/salida.
- `scope:ui`: Interfaz gráfica web embebida (`q-cockpit`).
- `scope:data`: Esquemas, manifiestos y persistencia local (`.q-agent.json`).
- `scope:security`: Seguridad y validación de secretos.
- `scope:telemetry`: Métricas, flight recorder y eventos.
- `scope:test`: Cobertura, tests unitarios y suites de regresión.
- `scope:infra`: CI/CD, automatización de GitHub Actions y release packaging.

Para mayor detalle, consulta [`references/issue-labels.md`](references/issue-labels.md).

---

## 🔀 3. Estrategia de Ramas (Git Flow)

- `main`: Código listo para producción. Cada commit en `main` debe ser estable y pasar todos los checks de CI.
- `develop`: Rama de integración donde convergen las nuevas features antes de un release.
- Ramas temáticas (branches):
  - `feature/<nombre-descriptivo>`: Para nuevas funciones.
  - `fix/<nombre-descriptivo>`: Para resolución de bugs.
  - `docs/<nombre-descriptivo>`: Para mejoras exclusivas de documentación.

---

## 🧪 4. Ejecución de Tests y Validación Local

Antes de abrir un Pull Request, ejecuta la suite de validación localmente:

```bash
# 1. Validar sintaxis y compilación de scripts Python
python3 -m py_compile tools/q-cockpit/q_cockpit.py
python3 -m py_compile tools/q-checklist/q_checklist.py
python3 -m py_compile tools/q-audit-validator/validate_audit.py
python3 -m py_compile tools/q-audit-aggregator/generate_report.py
python3 -m py_compile tests/*.py

# 2. Ejecutar la suite completa de tests unitarios
python3 -m unittest discover -s tests -v

# 3. Validar integridad de JSON
python3 -m json.tool skill.json > /dev/null

# 4. Verificar ejecución smoke (--help) de las herramientas
python3 tools/q-cockpit/q_cockpit.py --help
python3 tools/q-checklist/q_checklist.py --help
python3 tools/q-audit-validator/validate_audit.py --help
python3 tools/q-audit-aggregator/generate_report.py --help
```

---

## 🚀 5. Proceso de Pull Request (PR)

1. Crea tu rama a partir de `develop` (o `main` si es un hotfix urgente).
2. Asegúrate de que todos los tests pasen localmente (`Ran X tests ... OK`).
3. Completa la plantilla del PR (`.github/pull_request_template.md`), adjuntando la evidencia de terminal real.
4. Vincula el issue correspondiente (e.g. `Closes #12`).
5. Espera a que el pipeline de GitHub Actions (`CI Pipeline`) se ejecute y apruebe en verde.
