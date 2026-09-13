---
name: delegate-context-work
description: "Coordina lectura de archivos, boilerplate e implementación acotada mediante subagentes del mismo entorno o ejecutores externos como Codex y Antigravity. Selecciona ejecutor, modelo y esfuerzo de forma automática o explícita, y valida resultados."
metadata:
  version: "1.1.0"
---

# Delegación agnóstica de contexto y código

## Propósito

Mantener al agente principal como coordinador y delegar trabajo
delimitado cuando mejore el uso de contexto, costo, tiempo o calidad.

Separar cuatro conceptos:
- Coordinador: agente que mantiene el objetivo y acepta resultados.
- Ejecutor: subagente nativo o herramienta externa.
- Modelo: modelo usado por el ejecutor.
- Esfuerzo: nivel de razonamiento de esa ejecución.

Cambiar de modelo no requiere cambiar de herramienta.
Cambiar el modelo de la sesión principal no crea un subagente.

## 1. Resolver preferencias

Aceptar instrucciones en lenguaje natural, sin exigir parámetros.

Modos:
- auto: decidir qué delegar según contexto y complejidad.
- explicit: delegar únicamente lo señalado por el usuario.
- off: resolver directamente sin delegar.

Permitir fijar por tarea o rol:
- Ejecutor.
- Modelo.
- Esfuerzo.
- Alcance.
- Paralelismo.
- Límite de correcciones.

Ejemplos:
- “Mantén Astra Medium como coordinador y usa Luna High para lectores”.
- “Desde Pi, delega boilerplate a agy y lo complejo a Codex”.
- “Delega únicamente esta lectura; implementa tú los cambios”.
- “No delegues esta tarea”.

Respetar instrucciones superiores y políticas del proyecto.
No duplicar esta política en AGENTS.md cuando ya está cargada.
No interpretar la skill como sustituto de las demás reglas del repositorio.

## 2. Descubrir capacidades y elegir ruta

Aplicar este orden:
1. Elección explícita del usuario.
2. Configuración aplicable del proyecto o sesión.
3. Selección automática entre capacidades disponibles y autorizadas.

Examinar herramientas nativas, agentes configurados, ayuda local
y catálogos accesibles. No buscar ni instalar ejecutores arbitrarios.

Comprobar:
- Que el mecanismo de delegación existe.
- Que admite el ejecutor elegido.
- Que el modelo y esfuerzo solicitados están disponibles.
- Que existe acceso al directorio de trabajo.
- Que autenticación y permisos son suficientes.

No confundir un modelo accesible desde Pi con ejecutar Codex CLI.

Si una ruta explícita no está disponible, informar el bloqueo.
No cambiar ejecutor, proveedor, modelo o esfuerzo silenciosamente.

Si el coordinador está en la nube y la CLI en otra computadora,
verificar que existe un canal autorizado. Un prompt no conecta equipos.

Registrar la ruta elegida una vez por sesión y sus cambios posteriores.
No preguntar nuevamente por preferencias ya establecidas.

## 3. Elegir qué delegar

Resolver primero con herramientas deterministas cuando basten:
- rg para búsquedas exactas.
- Lecturas por rango para fragmentos conocidos.
- Plantillas o scripts para sustituciones repetitivas.

Delegar lectura cuando:
- Haya varios archivos o contenido extenso.
- Se necesite interpretación semántica.
- Una respuesta breve pueda evitar cargar todo al coordinador.

Delegar boilerplate cuando:
- Exista un contrato completo.
- Haya referencias reales del proyecto.
- El resultado sea mayormente predecible.

Ejemplos:
- Esquemas y DTO.
- Fixtures.
- Estructuras repetitivas.
- Configuración delimitada.
- Documentación basada en hechos comprobables.

Mantener en el coordinador o un especialista capaz:
- Arquitectura y decisiones de negocio.
- Diagnóstico ambiguo.
- Seguridad y autorización.
- Cambios complejos de integración.

No tratar código crítico como boilerplate por ser corto.
Agrupar cambios mecánicos similares si comparten referencias.

No delegar tareas pequeñas cuyo costo de coordinación supere
el beneficio esperado.

## 4. Seleccionar modelo y esfuerzo

Elegir ambos de forma explícita cuando el entorno lo permita.

Usar la combinación menos costosa que pueda cumplir la tarea,
basándose en resultados observados y complejidad.

No asumir que:
- El modelo más barato produce el menor costo total.
- High tiene idéntico significado en diferentes modelos.
- Un nombre de rol selecciona automáticamente otro modelo.
- Escribir “usa Luna” en el prompt cambia la configuración real.

Ejemplo válido de intención:
- Coordinador: Astra, medium.
- Lector o implementador mecánico: Luna, high.

Verificar identificadores y esfuerzos aceptados antes de ejecutarlo.

Si la herramienta permite modelo y esfuerzo en el lanzamiento,
pasarlos en sus parámetros reales.

Si requiere un agente configurado, comprobar su configuración efectiva.

Si no permite cambiar esos valores, declarar la limitación.
No afirmar que el ejecutor usó una configuración que no se aplicó.

Para cada CLI externa, registrar antes de lanzar:
- `model_requested` y `effort_requested`.
- `model_effective` y `effort_effective`, si la CLI los informa.
- `default` cuando el usuario eligió automático y no se pasó una opción.
- `unknown` cuando el valor efectivo no sea verificable.

Si la CLI admite `--model` y el parámetro de esfuerzo, pasarlos
explícitamente cuando ya se hayan resuelto identificadores válidos.
No simular un esfuerzo con texto del prompt ni atribuirlo al nombre
del rol.

Registrar modelo y esfuerzo solicitados, y los efectivos si
la plataforma los informa. Marcar como desconocidos los no verificables.

## 5. Preparar una tarea delimitada

Crear un brief por tarea con:
- Identificador y rol.
- Objetivo o pregunta.
- Contexto indispensable.
- Referencias y archivos de entrada.
- Archivos permitidos para escritura.
- Contrato de salida.
- Criterios de aceptación.
- Verificaciones pertinentes.
- Restricciones y dependencias.

Pasar el contexto mínimo necesario.
Preferir archivos a copiar historiales extensos.

No leer previamente todo el material en el coordinador solo
para volver a enviarlo al lector.

Instruir al ejecutor:
- No lanzar otros agentes.
- No ampliar el alcance.
- No modificar políticas ni desactivar validaciones.
- No agregar dependencias sin autorización.
- No publicar ni realizar cambios externos no autorizados.
- Reportar información faltante o bloqueos.
- No presentar pruebas no ejecutadas como realizadas.

Las instrucciones delimitan comportamiento; los permisos
del entorno determinan el acceso efectivo.

## 6. Ejecutar dentro del mismo entorno

Preferir subagentes nativos cuando satisfagan la ruta elegida.

Crear una ejecución hija con:
- Rol.
- Brief.
- Modelo.
- Esfuerzo.
- Contexto mínimo.
- Permisos apropiados.

Usar únicamente parámetros soportados por la herramienta real.
No inventar nombres de herramientas o campos.

Cuando la selección de modelo exija contexto nuevo, enviar un brief
autosuficiente en lugar de heredar toda la conversación.

Mantener el coordinador en su configuración original.

## 7. Ejecutar mediante otra CLI

Usar este camino cuando el usuario lo pida o aporte un beneficio
concreto frente al subagente nativo.

Comprobar ayuda local, autenticación y permisos antes de invocar.

Patrones orientativos; sustituir marcadores y verificar la versión:

Antigravity:
    agy -p "Lee /ruta/tarea.md y ejecuta esa tarea" \
      --model MODELO_VALIDO \
      --effort ESFUERZO_VALIDO \
      --output-format json

Codex:
    codex exec \
      --model MODELO_VALIDO \
      -c 'model_reasoning_effort="high"' \
      --sandbox read-only \
      --json \
      "Lee /ruta/tarea.md y ejecuta esa tarea"

El ejemplo Codex usa solo lectura.
Para escritura autorizada, seleccionar los permisos apropiados;
no cambiar a permisos irrestrictos como solución a un bloqueo.

Antigravity requiere verificar su política efectiva de permisos.
Un prompt de “solo lectura” no constituye un sandbox.

Guardar stdout y stderr en archivos separados y exclusivos por intento.
No sobrescribir reportes anteriores.

Establecer un tiempo límite mediante la herramienta de procesos y
registrar `timeout_seconds`, hora de inicio, PID cuando esté disponible
y rutas exclusivas de stdout/stderr.

Presupuestos por defecto:
- Lectura o consulta acotada: 180 s.
- Investigación web con fuentes: 600 s.
- Implementación acotada: 900 s.
- Más de 900 s requiere autorización explícita del usuario.

Durante una ejecución JSON/JSONL, monitorear vida del proceso y avance
por stdout sin asumir que salida parcial equivale a resultado final.

Después de un timeout:
1. Confirmar si el proceso sigue vivo y detener sólo el proceso conocido.
2. Inspeccionar stdout, stderr y cambios del repositorio.
3. No relanzar a ciegas ni presentar salida parcial como informe final.
4. Si la CLI soporta reanudar y conserva contexto, reutilizar una vez la
   sesión con una instrucción de sintetizar la evidencia existente sin
   repetir investigación.
5. Registrar duración, estado y decisión de recuperación; pedir decisión
   humana antes de iniciar una investigación nueva o ampliar el presupuesto.

Preferir invocación con argumentos separados, sin shell, cuando
el anfitrión lo permita. Si se usa shell, citar correctamente
rutas y argumentos; no interpolar contenido de archivos como código.

Interpretar cada formato:
- Codex --json: eventos JSONL.
- Antigravity --output-format json: envoltura JSON.

El JSON de la CLI no equivale al cumplimiento de la tarea.

## 8. Contrato de respuesta

Solicitar una respuesta breve con:
- status.
- summary.
- changed_files.
- evidence.
- checks.
- concerns.

Estados:
- DONE.
- DONE_WITH_CONCERNS.
- NEEDS_CONTEXT.
- BLOCKED.

DONE es una declaración del ejecutor, no aceptación automática.

Para lectores:
- Responder la pregunta.
- Citar rutas y símbolos; rangos cuando sean verificables.
- Distinguir hechos e inferencias.
- Indicar cobertura y archivos no examinados.
- No modificar archivos.
- Señalar incertidumbre o cobertura parcial.

Para implementadores:
- Escribir el resultado en los archivos autorizados.
- No devolver todo el código en el mensaje.
- Informar cambios y validaciones reales.
- Guardar evidencia extensa en un reporte cuando sea necesario.

Para revisores:
- Separar cumplimiento de requisitos y calidad.
- Fundamentar hallazgos con evidencia e impacto.
- No modificar código durante la revisión.

## 9. Validar antes de aceptar

Distinguir:
1. Transporte completado.
2. Reporte del ejecutor.
3. Resultado aceptado por el coordinador.

Para lecturas:
- Verificar los hechos que cambien decisiones importantes.
- Abrir el fragmento actual antes de editarlo.
- No confiar ciegamente en números de línea del resumen.

Para escrituras:
- Revisar archivos nuevos, modificados y eliminados.
- Incluir archivos no rastreados.
- Contrastar alcance y requisitos.
- Examinar el diff.
- Ejecutar verificaciones proporcionales al cambio.

No derivar todas las expectativas de prueba del propio código generado.

Para cambios sustanciales, usar revisión independiente.
Para boilerplate pequeño, puede revisar el coordinador.

No aceptar solo por exit 0, JSON válido, DONE o autorrevisión.
No repetir suites completas sin una razón concreta.

## 10. Controlar concurrencia y correcciones

Por defecto:
- Hasta dos lectores independientes, si el entorno lo permite.
- Un implementador activo.
- Hasta dos rondas de corrección.

No permitir escrituras concurrentes en el mismo checkout.

Para trabajo concurrente autorizado, separar worktrees y resolver
dependencias e integración. Un worktree no es una barrera de seguridad.

Enviar hallazgos concretos en cada corrección.
Reutilizar la sesión si conserva contexto útil y está disponible.
De lo contrario, enviar brief, reporte y hallazgos a una sesión nueva.

Al alcanzar el límite:
- Registrar pendientes.
- Declarar lo incompleto.
- No reiniciar indefinidamente.
- No escalar modelo o proveedor contra una elección explícita.

No revertir cambios del usuario ni repetir intentos sin inspeccionar
el estado real.

## 11. Conservar progreso y medir

Mantener una bitácora breve por objetivo con:
- Tarea y estado.
- Ejecutor, modelo y esfuerzo.
- Rutas de brief y reporte.
- Revisión base cuando corresponda.
- Verificaciones.
- Correcciones.
- Pendientes.

Tras compactación, contrastar bitácora y archivos antes de reanudar.
No repetir tareas ya verificadas.

Registrar duración y tokens cuando estén disponibles.
Usar desconocido o null si no se reportan.

Evaluar consumo conjunto:
- Coordinador.
- Ejecutores.
- Revisores.
- Correcciones.

No prometer un porcentaje fijo de ahorro.
No convertir cuotas de suscripción en dólares sin datos.

## 12. Convivir con Superpowers

Si existe un flujo activo de Superpowers:
- Mantener un único coordinador.
- Usar esta skill como política de selección y adaptador.
- Conservar las revisiones, límites y seguimiento de ese flujo.
- No duplicar revisiones ni generar una segunda bitácora equivalente.

Si se usa sola, aplicar el procedimiento de este archivo.

La skill orienta decisiones y llamadas a herramientas.
No instala CLIs, no crea credenciales y no garantiza cumplimiento
técnico de restricciones que el entorno no pueda imponer.

## Entrega

Comunicar:
- Qué se completó.
- Qué se delegó y a quién.
- Cómo se verificó.
- Qué quedó pendiente.
- Qué métricas pudieron comprobarse.

Continuar las acciones autorizadas sin pedir confirmación repetida.
Preguntar únicamente cuando falte información indispensable
o autorización real.