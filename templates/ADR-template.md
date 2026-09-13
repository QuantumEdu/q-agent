# ADR-[NNN] — [Título corto de la decisión]
> Architecture Decision Record — Quantum SDD Pipeline
> Path: `openspec/adrs/ADR-[NNN]-[slug].md`

| Campo | Valor |
|---|---|
| **ID** | ADR-[NNN] |
| **Fecha** | [YYYY-MM-DD] |
| **Estado** | [PROPUESTO / ACEPTADO / OBSOLETO / REEMPLAZADO por ADR-XXX] |
| **Deciders** | [quién tomó la decisión] |
| **Revisado en** | [P2 / P5 / P9 / ad-hoc] |

---

## Contexto

> ¿Qué situación, problema o restricción nos llevó a tomar esta decisión?
> Describir el estado del mundo ANTES de la decisión. Incluir las fuerzas en tensión
> (rendimiento vs. consistencia, velocidad vs. deuda técnica, etc.).

[Descripción del contexto. 2-5 párrafos.]

**Bounded Contexts afectados:**
- [Context A] — [cómo se ve afectado]
- [Context B] — [cómo se ve afectado]

**NFRs relevantes:**
- [NFR relacionada de CONSTITUTION.md sección 4]

---

## Decisión

> La decisión que se tomó. Formulada como frase de acción en presente.

**Adoptamos [solución] porque [razón principal].**

[Descripción más detallada de exactamente qué se decide: tecnología elegida,
patrón seleccionado, convención establecida, etc.]

---

## Consecuencias

### Positivas
- [beneficio concreto]
- [beneficio concreto]

### Negativas / Trade-offs
- [costo o restricción aceptada]
- [costo o restricción aceptada]

### Neutrales / Notas de implementación
- [efecto colateral sin valoración moral]

---

## Alternativas consideradas

| Opción | Por qué se descartó |
|---|---|
| [alternativa A] | [razón concreta] |
| [alternativa B] | [razón concreta] |

---

## Validación

> ¿Cómo se verifica que la decisión se cumple? ¿Dónde puede detectarse drift?

- **Gate de cumplimiento:** [P5 BC Check / P9 CAB-RP / CI lint / pre-commit hook]
- **Evidencia esperada:** [qué debe existir en el código o artefactos]
- **Señal de drift:** [qué indicaría que la decisión ya no se respeta]

---

## Historial de cambios a este ADR

| Fecha | Autor | Cambio |
|---|---|---|
| [YYYY-MM-DD] | [autor] | Creación inicial |
| [YYYY-MM-DD] | [autor] | [descripción] |

---

> **Nota:** Este ADR NO se modifica para reflejar el estado actual; se crea uno nuevo
> que lo reemplaza. El estado del ADR cambia a `REEMPLAZADO por ADR-[NNN]`.
