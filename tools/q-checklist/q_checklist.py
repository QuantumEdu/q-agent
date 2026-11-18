#!/usr/bin/env python3
"""
q-checklist: Interactive Pre-Flight Architectural Decision Matrix for q-agent.
Zero external dependencies. Generates CONSTITUTION.md, ADR-0001, and .q-agent.json.
"""

import re
import shutil
import subprocess
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
    "skillvault": {
        "title": "Memoria de Proyecto con SkillVault",
        "options": [
            ("disabled", "Sin memoria SkillVault (backend deshabilitado por defecto)", True),
            ("enabled", "Habilitar SkillVault como memoria del proyecto (escribe el marcador en AGENTS.md)", False),
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


MARKER_START = "<!-- skillvault:start -->"
MARKER_END = "<!-- skillvault:end -->"


def slugify_project_name(name: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in name.strip())
    return re.sub(r"-+", "-", slug).strip("-") or "project"


def resolve_skillvault_paths() -> tuple:
    """Resolve the SkillVault binary and vault paths from the environment.

    Returns (binary, vault_path): binary is the absolute path of the
    `skillvault` binary found via PATH (None when no binary is available);
    vault_path is the absolute path of the vault database,
    <SKILLVAULT_HOME>/vault.db, or ~/.skillvault/vault.db by default.
    The generated .q-agent.json provider and the verbatim AGENTS.md marker
    both use these resolved paths, so the two agree (same binary, same
    vault) instead of the config pointing at the default vault while the
    marker names the binary by short name.
    """
    binary = shutil.which("skillvault")
    vault_home = os.environ.get("SKILLVAULT_HOME") or "~/.skillvault"
    vault_path = os.path.join(os.path.abspath(os.path.expanduser(vault_home)), "vault.db")
    return (os.path.abspath(binary) if binary else None, vault_path)


def skillvault_marker_section(project_name: str, slug: str, binary: str = "skillvault", vault_path: str = "~/.skillvault/vault.db") -> str:
    # Same marked section `skillvault link-project` writes (q-skillvault
    # internal/cli/handlers_context.go). The fallback below uses id = slug;
    # re-running link-project refreshes it with the real vault project id.
    # binary/vault_path are the resolved paths from resolve_skillvault_paths,
    # so the marker agrees with the generated .q-agent.json provider.
    return (
        f"{MARKER_START}\n"
        "## SkillVault (project memory)\n"
        "\n"
        "This project keeps its decisions in SkillVault, a local knowledge vault.\n"
        "\n"
        f"- Vault: `{vault_path}` (binary: `{binary}`)\n"
        f"- Project: {project_name} (slug `{slug}`, id `{slug}`)\n"
        f"- Before answering about project conventions or changing code, check the vault first: `{binary} find \"<topic>\" --project {slug}`\n"
        f"- For a full context pack: `{binary} context --project {slug}`\n"
        f"{MARKER_END}"
    )


def upsert_marker_section(existing: str, section: str) -> str:
    start = existing.find(MARKER_START)
    end = existing.find(MARKER_END)
    if start != -1 and end != -1 and end > start:
        return existing[:start] + section + existing[end + len(MARKER_END):]
    if not existing.strip():
        return section + "\n"
    return existing.rstrip() + "\n\n" + section + "\n"


def link_skillvault_marker(project_root: Path, project_name: str, slug: str, binary=None, vault_path=None) -> str:
    """Write the SkillVault marker into <project_root>/AGENTS.md.

    Prefers `skillvault link-project` when the binary is available (it
    resolves the real vault project id); if the project is not in the vault
    yet, creates it first with `add-project`. Falls back to writing the
    marked section verbatim when the binary is missing or the CLI fails.
    binary/vault_path default to resolve_skillvault_paths(); passing them
    in keeps the marker and the generated .q-agent.json in agreement.
    Returns "cli" or "verbatim".
    """
    resolved_binary, resolved_vault = resolve_skillvault_paths()
    binary = binary if binary is not None else resolved_binary
    vault_path = vault_path or resolved_vault
    cli_attempted = False
    if binary:
        cli_attempted = True
        try:
            linked = subprocess.run(
                [binary, "link-project", "--project", slug, "--path", str(project_root)],
                capture_output=True, text=True, timeout=30,
            )
            if linked.returncode != 0:
                created = subprocess.run(
                    [binary, "add-project", "--name", project_name],
                    capture_output=True, text=True, timeout=30,
                )
                if created.returncode == 0:
                    linked = subprocess.run(
                        [binary, "link-project", "--project", slug, "--path", str(project_root)],
                        capture_output=True, text=True, timeout=30,
                    )
            if linked.returncode == 0:
                return "cli"
        except (OSError, subprocess.SubprocessError):
            pass
    if cli_attempted:
        # The CLI was available but linking failed: the verbatim marker
        # below carries id = slug, which may not match the vault project.
        # Say so instead of failing silently.
        print(
            "[WARN] `skillvault link-project` falló; el marcador se escribió "
            "verbatim con id = slug. Si el proyecto se creó ahora, su slug en "
            "el vault puede diferir del slug de q-agent: revisa "
            "`skillvault list-projects` y re-ejecuta link-project con el "
            "id/slug real del vault.",
            file=sys.stderr,
        )
    agents_md = project_root / "AGENTS.md"
    existing = agents_md.read_text(encoding="utf-8") if agents_md.exists() else ""
    agents_md.write_text(
        upsert_marker_section(
            existing,
            skillvault_marker_section(project_name, slug, binary=binary or "skillvault", vault_path=vault_path),
        ),
        encoding="utf-8",
    )
    return "verbatim"


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
    # 4. SkillVault memory backend (optional; disabled by default). Enabling
    # it here is the operator's human authorization for read lookups on this
    # project; the marker makes the vault discoverable to the host agent.
    skillvault_enabled = selections.get("skillvault", ("disabled",))[0] == "enabled"
    binary = vault_path = None
    if skillvault_enabled:
        slug = slugify_project_name(project_name)
        provider = configuration["context_retrieval"]["providers"]["skillvault"]
        # Resolve the real binary and vault once, from the environment
        # (PATH + SKILLVAULT_HOME), and write them into the provider so the
        # generated config is usable without hand-editing: the pilot
        # (e2e-pilot) needed exactly this correction by hand. When no
        # binary is found the template defaults stand (short name,
        # availability unknown, no capabilities).
        binary, vault_path = resolve_skillvault_paths()
        provider["enabled"] = True
        provider["project_slug"] = slug
        if binary is not None:
            provider["binary"] = binary
            provider["availability"] = "available"
            provider["capabilities"] = ["search", "read"]
        provider["vault_path"] = vault_path
        provider["authorization"] = "read"
        provider["authorization_evidence"] = {
            "source_ref": "q-checklist interactive selection (operator)",
            "operations": ["search", "read"],
            "destination": "local SkillVault vault",
            "credential_session": None,
            "expires_at": None,
            "revoked": False,
        }
        provider["project_scope"] = slug
        configuration["context_retrieval"]["project_id"] = slug
    (project_root / ".q-agent.json").write_text(
        json.dumps(configuration, indent=2) + "\n", encoding="utf-8"
    )
    if skillvault_enabled:
        link_skillvault_marker(project_root, project_name, slug, binary=binary, vault_path=vault_path)


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
        if selections["skillvault"][0] == "enabled":
            print("  - AGENTS.md (marcador SkillVault para descubrir el vault)")
        print("  [PENDIENTE] Configura runtime.executor y models con valores verificados en tu entorno.")
        print("\n¡Listo para entrar a P04 (/propose) con tu arquitectura pre-configurada!")
    else:
        print("\nGeneración cancelada.")


if __name__ == "__main__":
    main()
