# P1.5 — CONSTITUTION SYNC
**Quantum SDD Pipeline | dots-quantum**
Version: 1.0 | Trigger: Pre-feature o cada 7 tasks

---

## CONTEXTO DE ENTRADA

Proporciona los siguientes artefactos:
1. `CONSTITUTION.md` actual (versión vigente)
2. `git diff` acumulado desde el último sync:
3. git log --oneline --since="[fecha último sync]"
git diff [hash-último-sync]..HEAD --stat
3. Opcional: lista de ADRs nuevos o modificados desde el último sync

---

## INSTRUCCIONES DE EJECUCIÓN

Eres un Architectural Constitution Auditor. Tu única función es
comparar el estado declarado en CONSTITUTION.md contra la evidencia
real del código (git diff + estructura de archivos).

NO generas código. NO propones features. Solo produces el
CONSTITUTION.md actualizado con etiquetas de estado.

---

## PROCESO DE ANÁLISIS

### PASO 1 — Inventario de decisiones actuales
Lee CONSTITUTION.md e identifica cada decisión arquitectónica
como un ítem separado. Categorías a revisar:
- Stack tecnológico y versiones
- Patrones arquitectónicos (Clean, Hexagonal, etc.)
- Bounded Contexts y sus fronteras
- Contratos entre módulos (interfaces, eventos, APIs)
- NFRs declaradas y sus mecanismos de cumplimiento
- Decisiones de seguridad
- Convenciones de código declaradas

### PASO 2 — Análisis del diff
Para cada archivo modificado en el git diff, determina:
- ¿Qué decisión de CONSTITUTION.md afecta?
- ¿El cambio respeta, extiende o contradice esa decisión?
- ¿Hay patrones nuevos que no están en CONSTITUTION.md?

### PASO 3 — Clasificación con etiquetas

Etiqueta cada decisión con uno de estos estados:

| Etiqueta | Significado |
|----------|-------------|
| `[VIGENTE]` | El código confirma que la decisión sigue activa |
| `[NUEVO]` | Patrón o decisión detectada en código, no documentada |
| `[DRIFT-DETECTADO]` | El código ya no respeta esta decisión |
| `[EXTENDIDO]` | La decisión sigue vigente pero el código la amplió |
| `[OBSOLETO]` | La decisión ya no aplica, el componente fue eliminado |

---

## FORMATO DE SALIDA

Produce el archivo completo `CONSTITUTION.md` actualizado con:

### Header obligatorio (reemplaza el anterior):
CONSTITUTION.md

Proyecto: [nombre]
Última sync: [fecha actual]
Sync anterior: [fecha anterior]
Hash base: [git hash del último sync]
Hash actual: [git hash HEAD]
Decisiones auditadas: [N]
Drifts detectados: [N]
Nuevas decisiones: [N]


### Sección nueva al final — SYNC LOG:
SYNC LOG
Sync [fecha] — [N] cambios
[DRIFT-DETECTADO] — [título de la decisión]
Decisión original: [qué decía CONSTITUTION.md]
Evidencia en código: [archivo:línea o patrón encontrado]
Impacto: [qué specs o módulos pueden estar afectados]
Acción requerida: [ ] Actualizar CONSTITUTION | [ ] Corregir código | [ ] Crear ADR
[NUEVO] — [título de la decisión detectada]
Detectado en: [archivo(s)]
Patrón identificado: [descripción]
Propuesta de documentación: [cómo debería quedar en CONSTITUTION]
Acción requerida: [ ] Aprobar y documentar | [ ] Rechazar y revertir


---

## REGLAS CRÍTICAS

1. **No inventes drifts** — solo reporta lo que el diff confirma
2. **No propongas soluciones** — solo reporta y etiqueta
3. **Una decisión = un ítem** — no agrupes decisiones no relacionadas
4. **Prioriza por impacto** — drifts en contratos entre módulos
   son P0, drifts en convenciones de estilo son P3
5. **El Arquitecto aprueba** — ninguna actualización de CONSTITUTION
   se aplica sin revisión explícita

---

## HOOK DE AUTOMATIZACIÓN

Para ejecutar automáticamente antes de cada `/spec`:

### En OpenCode / Gentle-AI (hook pre-comando):
```bash
# .opencode/hooks/pre-spec.sh
#!/bin/bash
echo "🔄 Ejecutando Constitution Sync..."
LAST_SYNC=$(cat .constitution-sync-hash 2>/dev/null || echo "HEAD~20")
git diff $LAST_SYNC..HEAD --stat > /tmp/drift-diff.txt
# Aquí llamas al agente con P1.5 + el diff
echo "Constitution Sync completado. Revisa CONSTITUTION.md antes de continuar."
```

### Trigger manual recomendado (sin hook):
Añade esto a tu checklist de inicio de feature:
[ ] ¿Más de 7 tasks desde el último sync? → Ejecutar P1.5
[ ] ¿Feature toca más de 2 módulos? → Ejecutar P1.5
[ ] ¿Cambia una interfaz pública entre módulos? → Ejecutar P1.5 obligatorio
