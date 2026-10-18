#!/usr/bin/env python3
"""
q-checklist: Interactive Pre-Flight Architectural Decision Matrix for q-agent.
Zero external dependencies. Generates CONSTITUTION.md, ADR-0001, and .q-agent.json.
"""

import sys
import json
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


ARCHITECTURE_GUIDANCE = {
    "hexagonal": {
        "principle": "El dominio permanece independiente de infraestructura; los puertos definen los contratos y los adaptadores los implementan.",
        "components": "- **Domain Layer**: Entidades y reglas de negocio.\n- **Ports Layer**: Contratos de entrada y salida.\n- **Adapters Layer**: Persistencia y transporte seleccionados.",
        "rationale": "Permite sustituir infraestructura manteniendo estables los contratos del dominio.",
        "tradeoff": "Mantener puertos explícitos y sus adaptadores añade código y exige revisar sus contratos.",
    },
    "clean": {
        "principle": "Las dependencias apuntan hacia entidades y casos de uso; los detalles externos quedan fuera de las reglas de negocio.",
        "components": "- **Entidades**: Reglas de negocio.\n- **Casos de uso**: Flujos de aplicación.\n- **Interfaces e infraestructura**: Presentación, persistencia y frameworks.",
        "rationale": "Separa las políticas de negocio de los detalles externos.",
        "tradeoff": "Mantener dependencias hacia el interior puede requerir contratos en las fronteras externas.",
    },
    "layered": {
        "principle": "Separar presentación, servicios y acceso a datos; explicitar la dirección de las dependencias entre capas.",
        "components": "- **Presentación**: Transporte seleccionado.\n- **Servicios**: Operaciones y reglas de negocio.\n- **Repositorios**: Acceso a la persistencia seleccionada.",
        "rationale": "Organiza responsabilidades por capas con una dirección de dependencias explícita.",
        "tradeoff": "Vigilar dependencias entre capas y evitar servicios que solo reenvían llamadas.",
    },
    "modular_monolith": {
        "principle": "Organizar por módulos funcionales y slices verticales; mantener juntos almacenamiento, operaciones y presentación de cada funcionalidad, sin imponer capas globales.",
        "components": "- **Slices por funcionalidad**: Almacenamiento, operaciones, presentación y pruebas del módulo.\n- **Límites entre módulos**: Contratos solo cuando exista una frontera real; evitar interfaces pasamanos.",
        "rationale": "Los slices verticales concentran cada cambio funcional dentro de su módulo.",
        "tradeoff": "Mantener límites entre módulos y extraer contratos compartidos solo cuando sean necesarios.",
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

    architecture = ARCHITECTURE_GUIDANCE[selections["architecture"][0]]

    # 1. CONSTITUTION.md
    constitution_content = f"""# CONSTITUCIÓN ARQUITECTÓNICA — {project_name.upper()}
Fecha de Aprobación: {today}
Estado: [VIGENTE]

## 1. Declaración de Principios Inmutables
1. **Organización del Código**: {selections['architecture'][1]}. {architecture['principle']}
2. **Estrategia de Persistencia**: {selections['persistence'][1]}.
3. **Transporte**: {selections['transport'][1]}.
4. **Disciplina de Testing**: {selections['testing'][1]}.
5. **Aislamiento de Trabajo**: {selections['isolation'][1]}.

## 2. Registro de Decisiones de Arquitectura (ADR)
| ADR ID | Título | Estado | Fecha | Archivo |
|---|---|---|---|---|
| ADR-0001 | Selección de Stack y Patrones Fundacionales | [ACEPTADO] | {today} | `docs/adr/0001-stack-decisions.md` |

## 3. Componentes de la Arquitectura Seleccionada
{architecture['components']}

Persistencia: `{selections['persistence'][0]}`. Transporte: `{selections['transport'][0]}`.
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
- {architecture['rationale']}
- La persistencia y el transporte seleccionados definen las integraciones que deben validarse.
- El rendimiento y la concurrencia requieren mediciones en el entorno real.

## Consecuencias
- **Positivas:** Responsabilidades explícitas conforme a la arquitectura seleccionada.
- **Compromisos:** {architecture['tradeoff']}
"""
    (project_root / "docs" / "adr" / "0001-stack-decisions.md").write_text(adr_content, encoding="utf-8")

    # 3. .q-agent.json
    # Load a fresh template so all defaults stay aligned without mutating it.
    template_path = Path(__file__).resolve().parents[2] / "templates" / "q-agent.json"
    configuration = json.loads(template_path.read_text(encoding="utf-8"))
    configuration["workspace"]["isolation"] = selections["isolation"][0]
    (project_root / ".q-agent.json").write_text(
        json.dumps(configuration, indent=2) + "\n", encoding="utf-8"
    )


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
        print("  [PENDIENTE] Configura runtime.executor y models con valores verificados en tu entorno.")
        print("\n¡Listo para entrar a P04 (/propose) con tu arquitectura pre-configurada!")
    else:
        print("\nGeneración cancelada.")


if __name__ == "__main__":
    main()
