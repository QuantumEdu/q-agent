---
name: q:ci-fixer
description: "Trigger: /q-ci-fixer, /fix-ci, arreglar ci, fallo github actions, reparar test linteo, coverage gate fail, resolver pyright ruff. Diagnostica y repara quirúrgicamente fallos en pipelines de CI/CD (ruff, eslint, pyright, tsc, pytest, deno test) sin debilitar las reglas ni reducir los umbrales de cobertura."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "2.0.0"
  date: "2026-10-10"
  context_policy: "COMPACT"
  requires: ["CI logs or test failure output"]
  produces: ["Surgical CI Fix", "Exit 0 Local Verification"]
---

# q:ci-fixer v2.0 — Reparación Quirúrgica de CI/CD

## 1. Quick Bootstrap & Triggers
- **Propósito**: Diagnosticar y corregir fallos en pipelines de CI/CD (GitHub Actions, linters, types, tests) de forma sistemática y quirúrgica, devolviendo el build a verde.
- **Cuándo Aplica**:
  - Un workflow de CI falló en un PR o commit reciente.
  - Pasos de linteo (`ruff`, `eslint`, `flake8`) o análisis de tipos (`pyright`, `tsc`, `mypy`) arrojaron errores.
  - La suite de pruebas falló por aserciones rotas (`AssertionError`) o por caer bajo el umbral de cobertura.
- **Cuándo NO Aplica (Anti-Triggers)**:
  - ⛔ **PROHIBIDO debilitar contratos**: Jamás editar `ci.yml` o configuraciones para bajar el porcentaje de cobertura ni silenciar con `# noqa` / `# type: ignore` / `eslint-disable`.
  - ⛔ **PROHIBIDO refactors cosméticos o nuevas features**: Modificar únicamente las líneas indispensables para resolver el error.
  - No usar si el fallo responde a una falta de definición de producto o cambio arquitectónico no acordado.
- **Límite Duro**: Máximo **2 pasadas de corrección**. Si no compila en la 2da pasada, detenerse y declarar bloqueo.

## 2. Contrato de Ejecución Paso a Paso (4 Capas)
- [ ] **M1 (Linteo y Formato Automático)**:
  - Python: `uv run ruff check --fix <archivos>` y `uv run ruff format <archivos>`.
  - JS/TS: `pnpm eslint --fix <archivos>` y `pnpm prettier --write <archivos>`.
- [ ] **M2 (Tipado Estático y Firmas)**:
  - Resolver `None` no manejados mediante guardas tempranas (`if val is None: return`).
  - Corregir anotaciones asegurando coincidencia con la firma de dominio.
- [ ] **M3 (Aserciones de Tests)**:
  - Si es regresión de código: reparar lógica en el componente de producción.
  - Si cambió legítimamente la regla de negocio: actualizar el test autorizado.
- [ ] **M4 (Cobertura de Ramas)**:
  - Agregar casos de prueba unitarios específicos para bifurcaciones (`if/else`, `except`) no cubiertas.

## 3. Completion Gate
Antes de declarar resuelto el CI:
- [ ] Ejecutar localmente el comando exacto que falló en CI y verificar **código de salida `0`**.
- [ ] Comprobar que `ci.yml` y umbrales de cobertura permanecen inalterados.
- [ ] Estado final declarado:
  - `[COMPLETE]` ──► Build local pasando en verde con exit code 0.
  - `[BLOCKED - reason]` ──► Error requiere decisión humana de arquitectura o se agotó el límite de 2 pasadas.
  - `[FAILED - reason]` ──► Imposible resolver sin debilitar contratos.
