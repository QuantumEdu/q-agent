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

*Cero dependencias externas — funciona con cualquier intérprete estándar de Python 3.8+.*
