# q-checklist (Herramienta Secundaria de Apoyo)

Matriz interactiva de selección rápida de decisiones arquitectónicas para `q-agent`.

Permite a arquitectos y desarrolladores con experiencia saltarse la deliberación dialéctica (`q-deliberate`) cuando ya conocen de antemano el stack y las decisiones técnicas de su proyecto.

---

## ¿Qué hace?

Al ejecutarse en la terminal, te presenta un menú interactivo tipo checklist con las decisiones arquitectónicas fundamentales:
1. **Arquitectura:** Hexagonal Pura, Clean, Capas o Monolito Modular.
2. **Persistencia:** SQLite WAL Mode, PostgreSQL, DuckDB o In-Memory.
3. **Transporte:** CLI, API REST, TUI o Biblioteca interna.
4. **Testing:** TDD Reproduction-First, BDD Gherkin o Property-Based.
5. **Aislamiento de Workspace:** Git Worktrees o Ramas Inline.

Con esas respuestas, genera instantáneamente:
- `CONSTITUTION.md` (Constitución arquitectónica con principios inmutables).
- `docs/adr/0001-stack-decisions.md` (Registro canónico de la decisión).
- `.q-agent.json` (Configuración declarativa para que el agente arranque en modo supervisado y con aislamiento).

---

## Cómo usarla

```bash
# Desde la raíz de tu nuevo proyecto:
python path/to/q-agent/tools/q-checklist/q_checklist.py
```

*Cero dependencias externas — usa Python 3.10+ como el resto de q-agent.*

## Coherencia y configuración del entorno

La constitución y el ADR describen la arquitectura seleccionada: hexagonal,
Clean, capas o monolito modular con slices verticales. Elegir monolito modular
no impone puertos ni capas globales. Las opciones numéricas y los valores por
defecto del menú se conservan.

El JSON parte de `templates/q-agent.json` y aplica el aislamiento elegido.
`runtime.executor`, `models.tier1_frontier` y `models.tier2_local` quedan en
`null` (sin configurar). Antes de usarlos, establece el ejecutor real y los
identificadores de modelos cuya disponibilidad hayas comprobado con su proveedor.
No se deducen por tener un CLI instalado ni se comprueban credenciales al generar.
La generación de archivos no instala ni activa ejecutores o modelos.

BDD y property-based son estrategias complementarias: el gate general de
reproducción de fallos de q-agent permanece activo en todas las opciones.

Esta corrección se aplica a nuevas generaciones. Para proyectos existentes,
revisa los tres artefactos manualmente; volver a ejecutar el checklist sobrescribe
esos archivos y puede perder decisiones personalizadas.
