# Taxonomía de GitHub Issue Labels — q-agent

Crear estos labels en cada repositorio nuevo (Plan A) al inicializar.
Para Plan B/C, verificar existencia y crear los faltantes.

---

## Dimensión: type (qué es el issue)

| Label | Color | Descripción |
|-------|-------|-------------|
| `type:feature` | `#0075ca` | Nueva funcionalidad |
| `type:fix` | `#d73a4a` | Corrección de bug |
| `type:adr` | `#7057ff` | Architecture Decision Record |
| `type:nfr-gap` | `#e4e669` | Gap de Non-Functional Requirement |
| `type:retrospective` | `#0e8a16` | Retrospectiva de ciclo completo |
| `type:audit` | `#f9d0c4` | Hallazgo de auditoría |
| `type:setup` | `#cfd3d7` | Infraestructura y configuración inicial |
| `type:chore` | `#fef2c0` | Mantenimiento sin impacto funcional |

---

## Dimensión: priority (urgencia)

| Label | Color | Descripción |
|-------|-------|-------------|
| `priority:critical` | `#b60205` | Bloquea el avance, P0 automático |
| `priority:high` | `#e99695` | Debe resolverse en el sprint actual |
| `priority:medium` | `#f9d0c4` | Próximo sprint |
| `priority:low` | `#fef2c0` | Backlog, sin urgencia |

---

## Dimensión: status (estado del issue)

| Label | Color | Descripción |
|-------|-------|-------------|
| `status:open` | `#0e8a16` | Activo, en progreso |
| `status:blocked` | `#d93f0b` | Bloqueado por dependencia externa |
| `status:in-review` | `#0075ca` | En revisión o PR abierto |
| `status:wontfix` | `#ffffff` | Descartado con justificación |

---

## Dimensión: scope (a qué capa del sistema afecta)

| Label | Color | Descripción |
|-------|-------|-------------|
| `scope:arch` | `#7057ff` | Arquitectura y patrones de diseño |
| `scope:api` | `#0075ca` | Endpoints y contratos de API |
| `scope:ui` | `#e4e669` | Interfaz de usuario |
| `scope:data` | `#cfd3d7` | Modelos de datos y migraciones |
| `scope:security` | `#d73a4a` | Seguridad y autenticación |
| `scope:telemetry` | `#f9d0c4` | Observabilidad y métricas |
| `scope:test` | `#0e8a16` | Cobertura y calidad de tests |
| `scope:infra` | `#cfd3d7` | CI/CD, deploy, configuración |

---

## Issues que el agente crea automáticamente

### Al iniciar Plan A
```
[SETUP] Infraestructura inicializada          type:setup, priority:high
[ADR-001] Decisión de runtime y arquitectura  type:adr, scope:arch
[SCOPE] MVP definido                          type:feature, priority:high
```

### Al iniciar Plan B
```
[FEATURE] <nombre de la feature>              type:feature, priority:high
[ADR-001] Análisis P1 MAB-PC completado       type:adr, scope:arch
```

### Al iniciar Plan C
```
[AUDIT] Inicio de auditoría — <fecha>         type:audit, priority:high
```

### Al cerrar cualquier plan
```
[RETRO] Retrospectiva — <nombre> — <fecha>    type:retrospective
[NFR-GAP-N] <descripción del gap>             type:nfr-gap, priority:<según severidad>
```

---

## Convención de títulos de Issues

```
[TIPO] Descripción imperativa breve
```

Ejemplos correctos:
- `[ADR-002] Elegir base de datos: SQLite vs PostgreSQL`
- `[NFR-GAP-01] Telemetría no implementada en módulo de pagos`
- `[FEATURE] Agregar autenticación con JWT`
- `[FIX] Error 500 en endpoint /api/orders cuando qty es null`

Ejemplos incorrectos:
- `bug en login` (sin tipo, no imperativo)
- `mejoras generales` (demasiado vago)
