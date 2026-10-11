# External CLI Delegation Adapters (Antigravity & Codex)

> **Propósito:** Guía de referencia y adaptadores de comando para invocar ejecutores externos por línea de comandos desde el orquestador o coordinadores de agentes. Cargar bajo demanda solo al ejecutar vía CLI externa.

---

## 1. Adaptador Google Antigravity (`agy`)

Invoca un subproceso aislado mediante la CLI de Antigravity:

```bash
agy -p "Lee /ruta/tarea.md y ejecuta esa tarea" \
  --model MODELO_VALIDO \
  --effort ESFUERZO_VALIDO \
  --output-format json
```

### Reglas del Adaptador Antigravity:
- **Sandbox:** Un prompt de "solo lectura" no es un sandbox del sistema. Verificar la política efectiva de permisos antes de permitir escrituras.
- **Formato:** `--output-format json` produce una envoltura JSON estándar en `stdout`. Redirigir siempre `stderr` a un archivo independiente por intento:
  ```bash
  agy -p "..." --output-format json > /tmp/agy_out_$$.json 2> /tmp/agy_err_$$.log
  ```

---

## 2. Adaptador OpenAI Codex (`codex`)

Invoca un subproceso aislado mediante la CLI de Codex:

```bash
codex exec \
  --model MODELO_VALIDO \
  -c 'model_reasoning_effort="high"' \
  --sandbox read-only \
  --json \
  "Lee /ruta/tarea.md y ejecuta esa tarea"
```

### Reglas del Adaptador Codex:
- **Sandboxing Nativo:** Usar siempre `--sandbox read-only` para tareas de inspección o lectura. Solo remover para implementación autorizada.
- **Formato de Salida:** `--json` emite un flujo de eventos en formato **JSONL**. Monitorear el progreso por eventos sin asumir que salida parcial es completitud.

---

## 3. Presupuestos de Tiempo (Timeouts)

Establecer un límite estricto por proceso y registrar `timeout_seconds`, PID y rutas de log:
- **Lectura / Consulta acotada:** 180 s (3 min).
- **Investigación web con fuentes:** 600 s (10 min).
- **Implementación acotada de código:** 900 s (15 min).
- ⛔ Tareas de más de 900 s requieren **autorización explícita del usuario**.

---

## 4. Protocolo de Recuperación ante Timeout o Fallo

Tras cumplirse el timeout:
1. Confirmar si el proceso sigue vivo (`ps -p $PID`) y detener únicamente el PID conocido (`kill -TERM $PID`).
2. Inspeccionar `stdout`, `stderr` y cambios en disco (`git status -s`).
3. ⛔ **PROHIBIDO relanzar a ciegas**: No reintentar automáticamente ni presentar un fragmento parcial como reporte final.
4. Si la CLI admite reanudación de sesión con contexto previo, invocar **una única vez** con instrucción de sintetizar la evidencia existente sin repetir la investigación.
5. Solicitar confirmación humana antes de reiniciar la tarea o ampliar el presupuesto de tiempo.
