#!/usr/bin/env python3
"""
q-audit-validator: Deterministic Output Quality Gate for q-agent Plan C.
Zero external dependencies. Enforces complete, non-truncated audit deliverables.
Validates: BLUEPRINT.md, CONSTITUTION.md, CAB_RP_AUDIT.md, REMEDIATION_ISSUES.md.
"""

import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


MANDATORY_BLUEPRINT_SECTIONS = [
    ("Visión / Alcance / Topología", [r"visi[oó]n", r"alcance", r"topolog[ií]a", r"bounded context"]),
    ("Interfaz Gráfica / Frontend UI/UX", [r"interfaz gr[aá]fica", r"frontend", r"ui/ux", r"design system", r"a11y"]),
    ("DevOps / GitHub CI/CD", [r"devops", r"github", r"ci/cd", r"pipeline", r"workflow"]),
    ("Seguridad / OWASP", [r"seguridad", r"owasp"]),
    ("Catálogo de Endpoints / Flujo", [r"endpoints?", r"cat[aá]logo", r"flujo"]),
    ("Plan de Mejora Accionable (P0/P1/P2)", [r"plan de mejora", r"quick wins", r"p0", r"p1", r"p2"]),
]


def validate_audit(cwd: Path) -> int:
    errors = []
    warnings = []

    print(f"\n🛡️  [q-agent] Validando Entregables de Auditoría Plan C en: {cwd.resolve()}\n")

    # 1. Validar BLUEPRINT.md
    blueprint_path = cwd / "BLUEPRINT.md"
    if not blueprint_path.exists():
        errors.append("❌ [CRÍTICO] BLUEPRINT.md no existe en la raíz del proyecto.")
    else:
        content = blueprint_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        
        if len(lines) < 80:
            errors.append(
                f"❌ [CRÍTICO] BLUEPRINT.md es superficial o truncado ({len(lines)} líneas). "
                "Un Blueprint completo de q-agent requiere al menos 80 líneas detalladas."
            )
        
        for section_name, patterns in MANDATORY_BLUEPRINT_SECTIONS:
            found = False
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    found = True
                    break
            if not found:
                errors.append(f"❌ [OMISIÓN] BLUEPRINT.md no contiene la sección obligatoria: '{section_name}'.")

    # 2. Validar CONSTITUTION.md
    constitution_path = cwd / "CONSTITUTION.md"
    if not constitution_path.exists():
        errors.append("❌ [CRÍTICO] CONSTITUTION.md no existe en la raíz del proyecto.")
    else:
        c_content = constitution_path.read_text(encoding="utf-8", errors="replace")
        if "ADR-" not in c_content:
            warnings.append("⚠️  CONSTITUTION.md no contiene tabla de ADRs iniciales.")

    # 3. Validar CAB_RP_AUDIT.md
    cab_paths = [
        cwd / "audit" / "CAB_RP_AUDIT.md",
        cwd / "audit" / "AUDIT_REPORT.md",
        cwd / "CAB_RP_AUDIT.md"
    ]
    cab_file = next((p for p in cab_paths if p.exists()), None)
    if not cab_file:
        errors.append("❌ [CRÍTICO] No se encontró el reporte de cumplimiento CAB-RP (audit/CAB_RP_AUDIT.md o audit/AUDIT_REPORT.md).")
    else:
        cab_content = cab_file.read_text(encoding="utf-8", errors="replace")
        if "Release" not in cab_content and "Veredicto" not in cab_content:
            warnings.append("⚠️  El reporte CAB-RP no declara explícitamente el Veredicto de Release.")

    # 4. Validar REMEDIATION_ISSUES.md
    remediation_paths = [
        cwd / "audit" / "REMEDIATION_ISSUES.md",
        cwd / "REMEDIATION_ISSUES.md"
    ]
    rem_file = next((p for p in remediation_paths if p.exists()), None)
    if not rem_file:
        errors.append("❌ [CRÍTICO] No se encontró el archivo de especificaciones de remediación (audit/REMEDIATION_ISSUES.md).")
    else:
        rem_content = rem_file.read_text(encoding="utf-8", errors="replace")
        ears_indicators = ["WHEN", "THE SYSTEM SHALL", "SO THAT", "IF"]
        ears_matches = sum(1 for kw in ears_indicators if kw in rem_content.upper())
        if ears_matches < 2:
            errors.append("❌ [FORMATO] REMEDIATION_ISSUES.md no utiliza el formato EARS requerido para alimentar al pipeline SDD.")

    # Imprimir Diagnóstico
    if warnings:
        print("⚠️  Advertencias detectadas:")
        for w in warnings:
            print(f"   {w}")
        print()

    if errors:
        print("⛔ Fallas de Validación Determinista:")
        for e in errors:
            print(f"   {e}")
        print("\n💥 Resultado: RECHAZADO. El agente intentó cerrar la auditoría con omisiones críticas.")
        print("   Acción requerida: Obligar al agente a completar las secciones faltantes antes de dar por cerrada la tarea.\n")
        return 1

    print("✅ Validación exitosa: Todos los entregables de auditoría cumplen con el estándar estricto de q-agent v1.2.\n")
    return 0


def main():
    target_dir = Path.cwd()
    if len(sys.argv) > 1:
        if sys.argv[1] == "--cwd" and len(sys.argv) > 2:
            target_dir = Path(sys.argv[2])
        else:
            target_dir = Path(sys.argv[1])
    
    sys.exit(validate_audit(target_dir))


if __name__ == "__main__":
    main()
