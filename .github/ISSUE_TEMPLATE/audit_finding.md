---
name: "Audit Finding / NFR Gap"
about: "Reporta un hallazgo o déficit arquitectónico derivado de Plan C o revisión de calidad"
title: "[NFR-GAP] "
labels: ["type:audit", "type:nfr-gap"]
assignees: []
---

## 1. Identificación del Hallazgo
- **Eje / Regla Afectada:** (e.g. `A01-architecture-layers`, `A02-security-secrets`, `A03-ci-pipeline-integrity`)
- **Severidad:** (critical | high | medium | low)

## 2. Evidencia y Ubicación
- **Archivos / Módulos:** `path/to/file.ext`
- **Fragmento o Diagnóstico:**
```text
# Detalle de la violación o hallazgo
```

## 3. Especificación de Remediación (EARS)
- **WHEN:** ...
- **THE SYSTEM SHALL:** ...

## 4. Plan de Acción
- [ ] Definir test de reproducción rojo (Red Phase).
- [ ] Implementar corrección sin introducir regresiones ni debilitar linters/cobertura.
- [ ] Validar con `python tools/q-audit-validator/validate_audit.py`.
