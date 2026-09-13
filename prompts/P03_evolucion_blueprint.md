---
id: P3_EVOLUCION_BLUEPRINT
titulo: "Evolución Arquitectónica — Blueprint v2 e Ingeniería Inversa del Código Fuente"
cuando_usar: "Para incorporar mecanismos reales descubiertos en el código fuente reconstruido o implementaciones de referencia."
prerequisitos: "BLUEPRINT.md v1 completado y aprobado. Acceso al repositorio fuente."
entregables: "BLUEPRINT_V2.md + DIFF_V1_VS_V2.md + actualización de la propuesta de arquitectura."
proyecto: "{{PROYECTO_NOMBRE}}"
---

# P3 — Evolución Arquitectónica
> Blueprint v2 e Ingeniería Inversa del Código Fuente

---

Actúa como Arquitecto de Sistemas Multi-Agente y Especialista en Ingeniería Inversa.

Misión:
Analiza el repositorio {{URL_REPO_FUENTE}} e inspecciona sus rutas clave ({{RUTAS_CLAVE}}) contrastándolas con el documento base original.

Protocolo de Inspección Dual-Mode:
- **Modo A (Con GBrain disponible):** Ejecuta consultas semánticas y de grafo (`gbrain query "{{URL_REPO_FUENTE}}"` / `gbrain inspect`) para extraer rápidamente el mapa de dependencias, relaciones de llamadas y componentes existentes.
- **Modo B (Standalone / Sin GBrain):** Ejecuta comandos estándar de inspección de código (`ripgrep`, `fd`, `git log -p`, lectura dirigida de archivos) sobre el árbol de directorios sin requerir dependencias externas.

Tareas y Requisitos:

1. Minería de Mecanismos Reales:
   Extrae y documenta con precisión los componentes que la especificación v1 omitió o simplificó:
   - {{COMPONENTE_1}}: {{DESCRIPCION}}
   - {{COMPONENTE_2}}: {{DESCRIPCION}}
   - {{COMPONENTE_N}}: {{DESCRIPCION}}

   Categorías arquitectónicas típicas a minar (adaptar según el dominio):
   - Routing / API Gateway: multiplexación de peticiones, autenticación, rate limiting y ruteo dinámico
   - Sandboxing & Aislamiento: límites de privilegios, entornos de ejecución aislados (Docker, VMs, subprocesos)
   - Protocolos de Streaming / Eventos: WebSocket, SSE, colas pub/sub, eventos en tiempo real
   - Persistencia & Caché: motores de almacenamiento, esquemas de migración, WAL, índices y transacciones
   - Almacén de Artefactos / Storage: almacenamiento indexado por hash criptográfico o rutas canónicas
   - Manejo de Fallos & Resiliencia: circuit breakers, reintentos con backoff, degradación elegante

2. Entregables:
   - Genera `{{RUTA_SALIDA}}/BLUEPRINT_V2.md` con la especificación completa v2.
   - Genera `{{RUTA_SALIDA}}/DIFF_V1_VS_V2.md` con la matriz de diferencias.
   - Actualiza la propuesta formal de arquitectura incorporando los módulos nuevos.

3. Etiquetas de evidencia obligatorias:
   - [IMPLEMENTADO: ruta/archivo] — mecanismo presente en el código.
   - [AUSENTE-EN-V1] — mecanismo real que el documento v1 no describía.
   - [SIMPLIFICADO-EN-V1] — mecanismo que v1 mencionaba pero sin detalle suficiente.
