# Manifiesto de Atribución, Reconocimiento y Autoría: q-agent v2.0
> **Firma Oficial:** Gabriel Magallón / QuantumEdu (Quantum)  
> **Licencia:** Apache License 2.0 | **Año:** 2026

---

## 🏛️ 1. Declaración de Autoría y Creaciones Propias de Quantum

El proyecto **`q-agent`** ha sido concebido, diseñado y orquestado por **Gabriel Magallón (QuantumEdu)** para establecer un estándar riguroso, determinista y libre de alucinaciones en el desarrollo asistido por Inteligencia Artificial (*Concepts > Code*).

### Módulos y Skills Propias Originales de Quantum:
1. **`q-agent` (Master Project Orchestrator v2.0):**
   - Arquitectura de **Motor Dual** (Gentle-AI Integrated ODD vs q-agent Standalone) con detección determinista en runtime.
   - Pipeline estructurado de 7 pasos: Pasos 0–3 guiados socráticos (una pregunta por turno) y Pasos 4–7 autónomos.
2. **Gobernanza Constitucional y Artículo ARQ-01:**
   - Ley suprema de diseño de software: Vertical Slices por defecto, umbral de dominio rico (>15 reglas de negocio), persistencia pragmática (SQLite WAL con timeout), higiene estricta de plantillas `.html` empaquetadas y 100% de consultas SQL parametrizadas.
3. **Terminal Evidence Gate (Compuerta de Evidencia en Terminal):**
   - Protocolo inquebrantable contra falsas completitudes (anti-mocks y anti-fakes) que exige la captura de comandos de terminal, código de salida `0` y pruebas observables antes de dar cualquier tarea por concluida.
4. **Suite de Skills Especializadas de Quantum:**
   - **`q-deliberate`:** Motor de deliberación dialéctica tripartita (*Proponent*, *Adversary*, *Synthesizer*) para evaluar disyuntivas arquitectónicas complejas.
   - **`q-grill-me`:** Elicitación socrática profunda para desafiar supuestos no validados en fases de diseño.
   - **`q-delegate-context`:** Patrón FirstMate para aislamiento y compresión de lecturas multifichero sin saturar la ventana de contexto del LLM.
   - **`q-gbrain-assistant`:** Interfaz unificada de memoria persistente a largo plazo con GBrain y Engram.
   - **`q-audit-readonly`:** Protocolo de auditoría forense con inmutabilidad absoluta en disco (`git status -s` idéntico de principio a fin).
   - **`q-ci-fixer`:** Reparación quirúrgica de errores de linters locales acotada a un límite estricto de 2 pasadas (*Bounded Turns*).
   - **`q-session-wrap`:** Consolidación de sesión, telemetría y snapshots de estado.
5. **Herramientas de Auditoría Determinista:**
   - `tools/q-audit-validator`: Validador sintáctico y estructural de reportes de auditoría.
   - `tools/q-audit-aggregator`: Agregador algorítmico determinista de brechas EARS y planes de remediación.

---

## 🤝 2. Reconocimiento y Atribución a Fundaciones y Terceros

`q-agent` se construye sobre hombros de gigantes, integrando y adaptando con el debido respeto y atribución conceptos clave de la industria y la comunidad de código abierto:

1. **Vertical Slice Architecture:**
   - **Autor / Referente:** Jimmy Bogard.
   - **Contribución:** La filosofía de organizar el código por características verticales cohesivas (handlers + storage + vistas) con mínima indirección en lugar de capas horizontales redundantes.
2. **Organic Driven Development (ODD) y Flujos Adaptativos:**
   - **Autor / Referente:** Alan Buscaglia / Ecosistema Gentle-AI.
   - **Contribución:** Inspiración conceptual del flujo orgánico guiado por bitácoras vivas únicas (`odd/tasks/`), heurística de tareas atómicas (~400 LOC) y la eliminación de la burocracia documental del SDD clásico.
3. **Reproduction-First Pattern (Fase Roja Obligatoria):**
   - **Autor / Referente:** Equipo de SWE-agent y SWE-bench (Princeton University / Stanford University).
   - **Contribución:** El principio de verificación previa obligatoria: ningún bugfix o funcionalidad se implementa sin haber ejecutado un test automatizado que falle de forma reproducible.
4. **Lente de Producto BMAD (Squad Path):**
   - **Autor / Referente:** Framework BMAD Method.
   - **Contribución:** Formulación ágil de User Persona, Fricción Actual, Historias de Usuario (`US-01`) y Criterios de Aceptación Observables (`UAC`) para mantener el código firmemente anclado al valor de negocio.
5. **Enfoques Didácticos y de Tipado:**
   - **Autor / Referente:** Matt Pocock.
   - **Contribución:** Pautas para la elicitación clara y simplificación de contratos en el desarrollo asistido por agentes.
6. **Aislamiento de Workspace mediante Git Worktrees:**
   - **Autor / Referente:** Comunidad Git / Linux Kernel.
   - **Contribución:** El patrón de carpetas hermanas aisladas (`../{repo}-worktrees/`) para garantizar que el agente nunca altere el árbol de trabajo activo del IDE del desarrollador.

---

## 📜 3. Licencia de Software

Todo el paquete `q-agent v2.0` se distribuye bajo la **Apache License, Version 2.0**:
- Permite el uso comercial, modificación, distribución y sublicenciamiento.
- Otorga una **concesión expresa de patentes** que protege tanto al autor como a los usuarios.
- Protege la marca comercial y el nombre de **Quantum** y **Gabriel Magallón**.
- Exige la preservación de los avisos de derechos de autor y este manifiesto de atribución en toda redistribución.

Para más detalles, consultar el archivo [`LICENSE`](LICENSE).
