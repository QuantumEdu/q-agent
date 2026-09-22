#!/usr/bin/env python3
"""
q-checklist: Interactive Pre-Flight Architectural Decision Matrix for q-agent.
Zero external dependencies. Generates CONSTITUTION.md, ADR-0001, and .q-agent.json.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

DECISION_OPTIONS = {
    "architecture": {
        "title": "Arquitectura y Organización del Código",
        "options": [
            ("hexagonal", "Arquitectura Hexagonal Pura (Puertos y Adaptadores - Dominio Aislado)", True),
            ("clean", "Clean Architecture (Uncle Bob - Casos de Uso y Entidades)", False),
            ("layered", "Arquitectura en Capas (Dominio / Servicio / Repositorio)", False),
            ("modular_monolith", "Monolito Modular Basado en Componentes", False),
        ],
    },
    "persistence": {
        "title": "Estrategia de Persistencia y Base de Datos",
        "options": [
            ("sqlite_wal", "SQLite con WAL Mode y busy_timeout=5000 (Local Determinista)", True),
            ("postgres", "PostgreSQL con Connection Pooling (Producción)", False),
            ("duckdb", "DuckDB Embebido (Analítica / OLAP)", False),
            ("in_memory", "Repositorio en Memoria (Zero I/O / Prototipo Rápido)", False),
        ],
    },
    "transport": {
        "title": "Interfaz Primaria y Transporte",
        "options": [
            ("cli", "Interfaz de Línea de Comandos (CLI / Typer / Argparse)", True),
            ("rest_api", "API RESTful (FastAPI / Express / Gin)", False),
            ("tui", "Terminal User Interface (TUI / Textual)", False),
            ("library", "Biblioteca / SDK Interno (Sin Servidor ni UI)", False),
        ],
    },
    "testing": {
        "title": "Estrategia de Calidad y Pruebas",
        "options": [
            ("reproduction_first", "TDD Reproduction-First Obligatorio (Fase Roja Antes de Tocar Código)", True),
            ("bdd", "BDD con Escenarios Gherkin (Given / When / Then)", False),
            ("property_based", "Property-Based Testing (Hypothesis / Invariantes)", False),
        ],
    },
    "isolation": {
        "title": "Aislamiento de Workspace",
        "options": [
            ("worktree", "Git Worktrees en Directorio Hermano (Zero-Interference con IDE)", True),
            ("inline", "Ramas Git Locales Inline (git checkout -b tradicional)", False),
        ],
    },
}


def prompt_choice(category_key: str) -> tuple:
    data = DECISION_OPTIONS[category_key]
    print(f"\n[?] {data['title']}:")
    default_idx = 1
    for idx, (opt_id, opt_desc, is_default) in enumerate(data["options"], start=1):
        def_tag = " (Recomendado / Por defecto)" if is_default else ""
        if is_default:
            default_idx = idx
        print(f"    [{idx}] {opt_desc}{def_tag}")

    while True:
        try:
            choice = input(f"    Selecciona [1-{len(data['options'])}] (default: {default_idx}): ").strip()
            if not choice:
                return data["options"][default_idx - 1]
            val = int(choice)
            if 1 <= val <= len(data["options"]):
                return data["options"][val - 1]
            print(f"    Por favor ingresa un número entre 1 y {len(data['options'])}.")
        except ValueError:
            print("    Entrada inválida. Ingresa un número.")
        except (KeyboardInterrupt, EOFError):
            print("\nOperación cancelada por el usuario.")
            sys.exit(0)


def generate_artifacts(project_root: Path, project_name: str, selections: dict):
    os.makedirs(project_root, exist_ok=True)
    os.makedirs(project_root / "docs" / "adr", exist_ok=True)
    os.makedirs(project_root / ".q-agent", exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")

    # 1. CONSTITUTION.md
    constitution_content = f"""# CONSTITUCIÓN ARQUITECTÓNICA — {project_name.upper()}
Fecha de Aprobación: {today}
Estado: [VIGENTE]

## 1. Declaración de Principios Inmutables
1. **Aislamiento Estricto de Capas**: {selections['architecture'][1]}. Las reglas de negocio del dominio no importan librerías de infraestructura, frameworks ni adaptadores de persistencia.
2. **Estrategia de Persistencia**: {selections['persistence'][1]}.
3. **Transporte**: {selections['transport'][1]}.
4. **Disciplina de Testing**: {selections['testing'][1]}.
5. **Aislamiento de Trabajo**: {selections['isolation'][1]}.

## 2. Registro de Decisiones de Arquitectura (ADR)
| ADR ID | Título | Estado | Fecha | Archivo |
|---|---|---|---|---|
| ADR-0001 | Selección de Stack y Patrones Fundacionales | [ACEPTADO] | {today} | `docs/adr/0001-stack-decisions.md` |

## 3. Matriz de Componentes y Puertos
- **Domain Layer**: Entidades puras, Value Objects, excepciones de dominio (`DomainError`).
- **Ports Layer**: Interfaces/Protocolos tipados que definen contratos de entrada y salida.
- **Adapters Layer**: Implementaciones concretas ({selections['persistence'][0]}, {selections['transport'][0]}).
"""
    (project_root / "CONSTITUTION.md").write_text(constitution_content, encoding="utf-8")

    # 2. docs/adr/0001-stack-decisions.md
    adr_content = f"""# ADR-0001: Selección de Stack y Patrones Fundacionales

- **Fecha:** {today}
- **Estado:** Aceptado
- **Decisor:** Arquitecto / Matriz de Decisiones Pre-Flight (q-checklist)

## Contexto
Se requiere establecer las bases arquitectónicas de {project_name} para garantizar determinismo, velocidad de desarrollo y facilidad de mantenimiento antes de iniciar el ciclo SDD.

## Decisiones Tomadas
1. **Arquitectura:** {selections['architecture'][1]}.
2. **Persistencia:** {selections['persistence'][1]}.
3. **Transporte:** {selections['transport'][1]}.
4. **Testing:** {selections['testing'][1]}.
5. **Aislamiento:** {selections['isolation'][1]}.

## Racional
- Garantiza desacoplamiento absoluto del dominio de negocio.
- Facilita pruebas unitarias de menos de 1 segundo sin dependencias de red.
- Minimiza el riesgo de bloqueos en concurrencia y sobrecarga en el entorno del desarrollador.

## Consecuencias
- **Positivas:** Estructura limpia, modularidad garantizada, cero dependencias pesadas innecesarias.
- **Compromisos:** Requiere escribir puertos (interfaces) explícitos antes de implementar adaptadores.
"""
    (project_root / "docs" / "adr" / "0001-stack-decisions.md").write_text(adr_content, encoding="utf-8")

    # 3. .q-agent.json
    isolation_mode = "worktree" if selections["isolation"][0] == "worktree" else "inline"
    q_agent_json = f"""{{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "version": "1.2",
  "runtime": {{
    "executor": "antigravity",
    "mode": "single-agent",
    "interaction_mode": "supervised",
    "interactive_gates": [
      "P03_blueprint",
      "P04_propose",
      "P09_compliance"
    ]
  }},
  "workspace": {{
    "isolation": "{isolation_mode}",
    "worktree_pattern": "../{{repo}}-worktrees/{{branch}}"
  }},
  "quality_gates": {{
    "reproduction_test_mandatory": true,
    "ast_skeleton_first": true,
    "max_consecutive_failures_before_rollback": 3
  }},
  "models": {{
    "tier1_frontier": "gemini-3.8-flash",
    "tier2_local": "qwen-2.5-7b-rocm"
  }},
  "observability": {{
    "flight_recorder": true,
    "log_path": ".q-agent/flight_recorder.log",
    "eval_level": "standard"
  }},
  "integrations": {{
    "github_issues": true,
    "gbrain_mcp": false,
    "engram_mcp": false
  }},
  "guardrails": {{
    "fs_write_allowed": ["src/**", "tests/**", "docs/**", "features/**", "odd/**", "q-tasks/**"],
    "fs_write_denied": [".git/**", "references/**", "templates/**"],
    "shell_denied": ["rm -rf /", "rm -rf ~*", "git push --force*", "sudo *"]
  }}
}}
"""
    (project_root / ".q-agent.json").write_text(q_agent_json, encoding="utf-8")


def main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print("usage: q_checklist.py [-h]")
        print("\nq-checklist: Interactive Pre-Flight Architectural Decision Matrix for q-agent")
        print("Generates CONSTITUTION.md, ADR-0001, and .q-agent.json.")
        sys.exit(0)

    print("=" * 70)
    print("  q-checklist: Matriz de Selección Rápida de Decisiones Arquitectónicas")
    print("=" * 70)

    cwd = Path.cwd()
    project_name_default = cwd.name
    project_name = input(f"\n[?] Nombre del Proyecto (default: '{project_name_default}'): ").strip()
    if not project_name:
        project_name = project_name_default

    target_dir_input = input(f"[?] Directorio de destino (default: '{cwd}'): ").strip()
    target_dir = Path(target_dir_input) if target_dir_input else cwd

    selections = {}
    for cat_key in DECISION_OPTIONS:
        selections[cat_key] = prompt_choice(cat_key)

    print("\n" + "=" * 70)
    print("  Resumen de Decisiones Seleccionadas:")
    for cat_key, sel in selections.items():
        print(f"  - {DECISION_OPTIONS[cat_key]['title']}: {sel[1]}")
    print("=" * 70)

    confirm = input("\n¿Confirmar y generar CONSTITUTION.md, ADR-0001 y .q-agent.json? [Y/n]: ").strip().lower()
    if confirm in ("", "y", "s", "yes", "si"):
        generate_artifacts(target_dir, project_name, selections)
        print(f"\n[OK] Artefactos generados con éxito en: {target_dir}")
        print("  - CONSTITUTION.md")
        print("  - docs/adr/0001-stack-decisions.md")
        print("  - .q-agent.json")
        print("\n¡Listo para entrar a P04 (/propose) con tu arquitectura pre-configurada!")
    else:
        print("\nGeneración cancelada.")


if __name__ == "__main__":
    main()
