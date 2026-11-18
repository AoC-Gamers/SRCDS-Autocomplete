# Changelog

## [Unreleased]

### Cambiado

- **Distribución:** el ZIP incluye una guía de instalación y reversión que
  identifica la plataforma y enlaza al commit base. Los manuales técnicos se
  consultan en el repositorio y los avisos se reúnen en `LICENSE`.

### Corregido

- **Consola:** al decodificar firmas, los escapes hexadecimales incompletos o
  inválidos se conservan como texto literal. Los escapes válidos, incluido
  `\x00`, siguen decodificándose.
- **Consola:** se descartan sugerencias más cortas que el texto que deben
  completar antes de calcular el sufijo.
- **Carga:** se libera la referencia a gamedata si falla su lectura o no se
  puede abrir la biblioteca del servidor dedicado.

### Desarrollo

- **CI:** los builds nativos seleccionan el runner con las variables de
  organización `L4D2_EXT_LINUX_RUNNER` y `L4D2_EXT_WINDOWS_RUNNER`. Habilita
  ambas para el repositorio antes de ejecutar el workflow.

- **Compilación:** Make unifica la compilación, las pruebas y el empaquetado en
  local y en CI. El empaquetador comprueba que el binario tenga la arquitectura
  esperada, corresponda a las fuentes usadas y lleve los recursos y la licencia.
- **Rutas de salida:** **INCOMPATIBLE** si se configuraron destinos de compilación
  o staging fuera del repositorio. Mueve esas salidas a un subdirectorio de
  `.build/` o `dist/`. Los SDK aún pueden residir fuera del repositorio.
- **Sonar:** el análisis local se configura con `.env` y `.env.secret` en lugar
  de `sonar-project.properties`. Usa las plantillas versionadas
  `.env.example` y `.env.secret.example` para preparar ambos archivos.
