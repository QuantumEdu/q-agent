## 📋 Resumen del Cambio

<!-- Explica de forma concisa QUÉ hace este PR y POR QUÉ es necesario. -->

- **Tipo de cambio:** [ ] Fix (`type:fix`) | [ ] Feature (`type:feature`) | [ ] Docs / Chore (`type:chore`) | [ ] Arquitectura (`type:adr`)
- **Issue relacionado:** Resuelve #

---

## 🛠️ Cambios Realizados

- [x] Descripción concisa del cambio 1
- [x] Descripción concisa del cambio 2

---

## 🧪 Evidencia de Validación (Zero-Mock Evidence)

<!-- Pega aquí la salida real del comando de pruebas en terminal local -->

```bash
python3 -m unittest discover -s tests -v
```

---

## ✅ Checklist de Calidad

- [ ] Cumple con **Article ARQ-01**: Vertical slice completa, mínima indirección, sin abstracciones prematuras.
- [ ] No utiliza mocks sintéticos donde se requiere verificación real sobre el sistema de archivos / CLI.
- [ ] La suite de tests unitarios y de integración pasa al 100%.
- [ ] La documentación maestra (`SKILL.md`, `references/`, `README.md`) y `CHANGELOG.md` han sido actualizadas de ser necesario.
- [ ] Los esquemas (`skill.json`, manifiestos) son válidos.
