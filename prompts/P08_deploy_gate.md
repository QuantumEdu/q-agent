---
id: P08_DEPLOY_GATE
titulo: "Gate de Despliegue y Autorización Humana — /deploy-gate"
cuando_usar: "Antes de fusionar a rama de producción o ejecutar scripts de despliegue/release."
prerequisitos: "P06 (Terminal Evidence Gate exitoso), P07 (Higiene linters limpia) y P09 (CAB-RP 2.0 sin Gaps P0)."
entregables: "Artefacto versionado REVIEW.md firmado por el operador humano."
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P08 — Gate de Despliegue y Autorización Humana
> `/deploy-gate`

Actúa como Arquitecto de Software Senior y Release Gatekeeper.

## Misión:
Compilar toda la evidencia observable acumulada durante el ciclo ODD y generar el documento de decisión `REVIEW.md`. El agente **TIENE PROHIBIDO** ejecutar despliegues o merges a producción por iniciativa propia; su rol es preparar la bandeja de evidencia para la firma humana.

---

### REGLA DE ORO: EL AGENTE NO DESPLIEGA
1. El agente recopila y verifica los 6 puntos de evidencia.
2. Si algún test o linter falló, el veredicto es automáticamente `NO_DEPLOY` y se detiene el flujo.
3. Si todo está limpio, emite `READY_FOR_HUMAN_SIGNATURE` y espera la confirmación explícita del usuario en el chat.

---

### PROTOCOLO DE GENERACIÓN (`REVIEW.md`):

Crea en la raíz del proyecto (o en `docs/releases/`) el archivo `REVIEW.md` con la siguiente estructura:

```markdown
# RELEASE REVIEW & DEPLOY GATE: {{FEATURE_NAME}}
- **Fecha:** {{TIMESTAMP_ISO8601}}
- **Commit SHA:** {{GIT_COMMIT_SHA}}
- **Motor Ejecutor:** {{MOTOR_A_GENTLE_AI | MOTOR_B_STANDALONE}}

## 1. Evidencia Terminal Observable (P06)
| Suite / Slice | Comando Ejecutado | Exit Code | Salida Resumida |
|---|---|---|---|
| Tests Unitarios & Slices | `go test -v ./features/...` | 0 | PASS (0.04s) |
| Chequeo Estático / Tipos | `go vet ./... && tsc --noEmit` | 0 | Clean |
| Linters (q-ci-fixer) | `golangci-lint run` | 0 | 0 errors |

## 2. Verificación Constitucional ARQ-01
- [x] **ARQ-01.1 (Vertical Slices):** Handler consume directamente storage del slice; cero interfaces pasamanos.
- [x] **ARQ-01.3 (SQLite WAL):** WAL activado, busy_timeout >= 5000, 1 writer pool verificado en runtime.
- [x] **ARQ-01.4 (Higiene Templates):** Vistas en archivos .html independientes, cero HTML concatenado en backend.
- [x] **ARQ-01.5 (Ciberseguridad):** 100% queries parametrizadas; variables sensibles en `.env` (no commiteadas).
- [x] **ARQ-01.6 (Anti-Mocking):** Pruebas contra base de datos de test real o memoria WAL, cero mocks de SQLite.

## 3. Matriz de Criterios de Aceptación (UAC)
| ID | Criterio de Aceptación (BMAD) | Estado | Evidencia en Código |
|---|---|---|---|
| UAC-01 | Creación de acuerdos con reunión asociada | CUMPLIDO | `internal/storage/sqlite_test.go:42` |
| UAC-02 | Soporte de acuerdos independientes (nullable) | CUMPLIDO | `internal/storage/sqlite_test.go:68` |

## 4. Análisis de Impacto y Riesgos
- **Archivos Modificados:** {{TOTAL_ARCHIVOS}} archivos (~{{LINEAS_AUTHORED}} LOC).
- **Riesgo de Regresión:** BAJO / MEDIO / ALTO (Detalle técnico).
- **Plan de Rollback Inmediato:**
  ```bash
  git revert {{GIT_COMMIT_SHA}} -m "revert: rollback de emergencia de {{FEATURE_NAME}}"
  ```

## 5. Recomendación del Agente
[ ] NO DEPLOY — Bloqueado por: (indicar gaps si existieran)
[x] READY FOR DEPLOY — Cumplimiento total verificado al 100%.

## 6. AUTORIZACIÓN HUMANA (OBLIGATORIA)
> Esta sección DEBE ser firmada por el operador humano. Sin esta firma el release carece de validez.

- **Aprobado por:** Gabriel Magallón Sánchez / QuantumEdu
- **Firma / Hash de Aprobación:** [APROBADO_PARA_PRODUCCION]
- **Timestamp de Aprobación:** {{TIMESTAMP}}
```

4. **Instrucción de Pausa:** Tras escribir `REVIEW.md`, emite el mensaje:
   `"Gate de Despliegue preparado en REVIEW.md con 100% de evidencia verificada. ¿Autorizas el paso a producción? (Sí/No)"`
   **DETÉN LA EJECUCIÓN Y ESPERA RESPUESTA.**
