---
name: q:ci-fixer
description: "Trigger: /q-ci-fixer, /fix-ci, arreglar ci, fallo github actions, reparar test linteo, coverage gate fail, resolver pyright ruff. Diagnostica y repara quirúrgicamente fallos en pipelines de CI/CD (ruff, eslint, pyright, tsc, pytest, deno test) sin debilitar las reglas ni reducir los umbrales de cobertura."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "1.0.0"
  date: "2026-09-03"
---

# q:ci-fixer

## Goal
Diagnosticar y resolver fallos de pipelines de integración continua (CI/CD) de forma sistemática y quirúrgica, garantizando que el build vuelva a verde sin relajar las reglas de calidad ni comprometer los umbrales de cobertura requeridos.

## When to Use
- Un workflow de GitHub Actions falló en un PR o commit reciente.
- Un paso de linteo (`ruff`, `eslint`, `flake8`) o análisis de tipos (`pyright`, `tsc`, `mypy`) arrojó errores.
- La suite de pruebas falló por aserciones rotas (`AssertionError`) o por no alcanzar el umbral del coverage gate.

---

## Invariantes Operativos No Negociables
1. **Regla de No Debilitamiento de Contratos**:
   - **PROHIBIDO** editar `ci.yml` o configuraciones de test para bajar el porcentaje de cobertura exigido.
   - **PROHIBIDO** silenciar errores con supresores indiscriminados (`# noqa`, `# type: ignore`, `eslint-disable`) salvo defecto verificado del compilador o herramienta.
2. **Blast Radius Mínimo**: Modificar únicamente las líneas indispensables para resolver el error; no aprovechar para refactorizaciones estéticas fuera de alcance.
3. **Verificación Local Obligatoria**: Antes de proponer commit o dar por concluida la tarea, ejecutar localmente el comando exacto que falló en CI hasta obtener código de salida `0`.

---

## Protocolo Paso a Paso en 4 Capas

### Capa 1: Formato y Linteo Automático
1. Identificar si el fallo involucra importaciones desordenadas o espaciado (`I001`, `format`).
2. Ejecutar auto-fix focalizado en los archivos señalados:
   - Python: `uv run ruff check --fix <archivos>` y `uv run ruff format <archivos>`
   - JS/TS: `pnpm eslint --fix <archivos>` y `pnpm prettier --write <archivos>`

### Capa 2: Tipado Estático y Firmas
1. Analizar el reporte del comprobador de tipos (`pyright` / `tsc`).
2. Resolver tipos `None` no manejados mediante guardas tempranas (`if value is None: return`).
3. Corregir anotaciones de tipos incorrectas asegurando que coincidan con la firma de dominio.

### Capa 3: Aserciones de Lógica de Negocio
1. Si falla un test unitario con `AssertionError`:
   - Determinar si el código de producción introdujo una regresión o si el test esperaba un formato desactualizado.
   - Si es una regresión en el código: reparar la lógica en el componente de producción.
   - Si cambió una regla de negocio legítimamente autorizada: actualizar el test para reflejar el nuevo contrato.

### Capa 4: Cobertura de Ramas (Coverage Gate)
1. Si el CI falla con "Coverage below threshold":
   - Inspeccionar el reporte de cobertura (`--cov-report=term-missing` o HTML).
   - Identificar las líneas y bifurcaciones (`if/else`, bloques `except/catch`) no ejecutadas.
   - Agregar casos de prueba unitarios específicos que cubran esos caminos de código.
2. Ejecutar la suite completa y certificar código de salida `0`.
