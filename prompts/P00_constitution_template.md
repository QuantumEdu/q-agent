# CONSTITUTION.md
Proyecto: [nombre]
Versión: [N]
Creado: [fecha P1 inicial]
Última sync: [fecha P1.5 más reciente]
Hash base sync: [git hash]

---

## 1. IDENTIDAD ARQUITECTÓNICA

- **Patrón principal:** [Clean Architecture / Hexagonal / etc.]
- **Patrones complementarios:** [lista]
- **Stack core:** [tecnologías + versiones]
- **Paradigma:** [MVC / Event-driven / CQRS / etc.]

---

## 2. BOUNDED CONTEXTS [SECCIÓN NUEVA]

### Mapa de dominios

| Context | Owns (entidades) | No toca | Estado |
|---------|-----------------|---------|--------|
| Auth | User, Session, Permission | Cualquier entidad de negocio | [VIGENTE] |
| Catálogo | Product, Category, Price | User, Order | [VIGENTE] |
| Pedidos | Order, OrderItem, Cart | Payment interno | [VIGENTE] |
| Pagos | Payment, Invoice, Refund | Order items | [VIGENTE] |

### Contratos entre contexts

Cada contrato es un acuerdo explícito. Cambiar un contrato
requiere un ADR nuevo y actualización de todos los specs que lo usen.

[Auth] ──► [Pedidos]
Contrato: TokenValidated(userId: string, scopes: string[])
Dirección: Auth emite, Pedidos consume
Mecanismo: Interface AuthService en ports/
Estado: [VIGENTE]

[Pedidos] ──► [Pagos]
Contrato: PaymentRequested(orderId: string, amount: number, currency: string)
Dirección: Pedidos emite, Pagos consume
Mecanismo: Event via EventBus
Estado: [VIGENTE]

[Pagos] ──► [Notificaciones]
Contrato: PaymentConfirmed(orderId: string, userId: string, receipt: string)
Dirección: Pagos emite, Notificaciones consume
Mecanismo: Event via EventBus
Estado: [VIGENTE]

### Regla de violación de frontera

> Ningún Context accede directamente a la implementación interna
> de otro Context. Solo se comunican por los contratos declarados
> arriba. Violaciones detectadas en P5 son bloqueantes.

---

## 3. DECISIONES ARQUITECTÓNICAS ACTIVAS

Lista de ADRs vigentes con estado:

| ADR | Decisión | Estado | Fecha |
|-----|----------|--------|-------|
| ADR-001 | Repository pattern para acceso a datos | [VIGENTE] | 2025-01 |
| ADR-002 | JWT para autenticación stateless | [DRIFT-DETECTADO] | 2025-02 |
| ADR-003 | Redis para caché de sesiones | [NUEVO] | 2025-08 |

---

## 4. NFRs DECLARADAS

| NFR | Mecanismo | Cómo se verifica | Estado |
|-----|-----------|-----------------|--------|
| Tiempo de respuesta < 200ms | Cache layer | Test de carga en CI | [VIGENTE] |
| Cobertura de tests > 80% | Jest + coverage | CI gate | [VIGENTE] |
| Zero secrets en código | git-secrets hook | Pre-commit | [VIGENTE] |

---

## 5. CONVENCIONES DE CÓDIGO

- [convención 1] [VIGENTE]
- [convención 2] [VIGENTE]

---

## 6. SYNC LOG

[Generado automáticamente por P1.5 — no editar manualmente]
