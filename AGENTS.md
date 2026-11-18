# Instrucciones del repositorio

Extensión nativa SourceMod para L4D2 x86, Linux y Windows. Las fuentes están en
`extension/`; el gamedata instalable en `addons/sourcemod/gamedata/`.

- Usa el Makefile raíz para compilar, probar, analizar y empaquetar, también en CI.
  Consulta `make help` y `docs/README.md`. Los scripts son backends versionados.
- Conserva `autocomplete.ext.2.l4d2.so` / `.dll`, el autoload y el contrato runtime.
  No cambies comportamiento de consola como efecto secundario de mantenimiento.
- Mantén un solo mapa en `scripts/package/package-map.json`; staging, ZIP y
  validación comparten `artifact_contract.py`. No distribuyas SDKs ni herramientas.
- Las descargas son explícitas mediante `deps-exts-*`. No actualices dependencias
  runtime sin autorización. Registra revisiones efectivas; las ramas siguen móviles.
- `make test TEST_OUTPUT=<directorio-nuevo>` y `make test-ci` ejecutan regresiones
  de paquetes/interfaz. Los ensayos con cabeceras ELF/PE sintéticas no son builds.
- Sonar y sus pruebas de tooling son locales y quedan fuera de `test-ci` y Actions.
  `make sonar` requiere configuración y autorización de envío; espera el gate.
- Revisa manualmente documentación, enlaces y privacidad. Documenta en español,
  bajo `docs/<feature>/`, con rutas inglesas. Actualiza CHANGELOG sin inventar versión.
- No conviertas compilación/paquete en aceptación SRCDS; informa plataformas no
  comprobadas. No publiques, despliegues ni toques servidores sin autorización.
