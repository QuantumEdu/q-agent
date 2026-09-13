---
name: q:session-wrap
description: "Trigger: /q-session-wrap, /session-wrap, /wrap, cerrar sesion, respaldar progreso, consolidar sesion, informe de entrega, backup sesion. Sintetiza los avances de la sesión actual, persiste la memoria en Engram, registra notas y artefactos en SkillVault y genera un snapshot atómico SQLite (VACUUM INTO)."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "1.0.0"
  date: "2026-09-03"
---

# q:session-wrap

## Goal
Cerrar ordenadamente una sesión de trabajo de ingeniería de software, sintetizando los avances técnicos, persistiendo la memoria operativa en **Engram**, catalogando notas y artefactos en **SkillVault** y generando un **respaldo atómico de base de datos** para que la siguiente sesión arranque con contexto completo.

## When to Use
- Al concluir una sesión de desarrollo o jornada de trabajo.
- Cuando el usuario indica: *"Terminamos por hoy"*, *"Haz un wrap del progreso"*, *"Cierra la sesión y respalda"*.
- Invocado directamente mediante `/q-session-wrap` o `/wrap`.

---

## Invariantes Operativos No Negociables
1. **Entrega Visible al Usuario**: Guardar memoria o respaldar es un proceso interno; **NUNCA** sustituye la respuesta visible final para el usuario. La sesión siempre finaliza entregando el informe ejecutivo en el chat.
2. **Persistencia Multi-Nivel**:
   - Memoria episódica en **Engram** (`mem_session_summary`).
   - Catalogación en **SkillVault** (`skillvault add-entry --type session`).
   - Snapshot consistente sin bloqueo de WAL mediante SQLite `VACUUM INTO`.
3. **Cero Suposiciones sobre Git**: Ejecutar `git status` y `git log` reales para registrar únicamente cambios comprobados.

---

## Protocolo Paso a Paso

### Paso 1: Recolección de Telemetría
1. Ejecutar `git status -s` para detectar archivos pendientes o modificaciones no commiteadas.
2. Ejecutar `git log -n 5 --oneline` para extraer los commits realizados durante la sesión.
3. Extraer el diff de cambios si quedan modificaciones en staging.

### Paso 2: Persistencia en Engram
Consolidar el resumen de sesión en Engram con la estructura obligatoria:
- **## Goal**: Qué objetivo se persiguió en la sesión.
- **## Instructions**: Preferencias o directivas fijadas por el usuario.
- **## Discoveries**: Hallazgos técnicos, bugs resueltos, causas raíz o gotchas.
- **## Accomplished**: Tareas completadas con evidencia de tests.
- **## Next Steps**: Próximas prioridades desbloqueadas para la siguiente sesión.
- **## Relevant Files**: Archivos modificados y su función.

### Paso 3: Registro en SkillVault
1. Registrar la sesión en SkillVault:
   `skillvault add-entry --title "Sesión [Proyecto] - [Fecha]" --summary "Resumen ejecutivo" --type session --project "[Proyecto]" --tags "session,wrap,[proyecto]"`
2. Si se crearon documentos o artefactos relevantes, guardarlos con `skillvault save-artifact`.

### Paso 4: Respaldo Atómico SQLite (VACUUM INTO)
1. Ejecutar `skillvault backup` para generar el snapshot JSON fechado.
2. Ejecutar `VACUUM INTO` en SQLite sobre `~/.skillvault/vault.db` generando copias atómicas en `~/.skillvault/exports/` y `~/backups/skillvaults.db`.

### Paso 5: Emisión del Reporte Ejecutivo al Usuario
Presentar en el mensaje final el resumen claro con:
- Lo logrado en la sesión.
- Commits generados.
- Estado de los respaldos y memorias.
- Siguiente paso sugerido al reanudar.
