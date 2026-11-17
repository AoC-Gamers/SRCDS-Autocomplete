# SRCDS Autocomplete para L4D2

`srcds-autocomplete` es una extensión nativa de SourceMod que agrega autocompletado con `Tab` a la entrada de consola `-console` usada por servidores dedicados de Left 4 Dead 2.

La extensión intercepta la ruta de entrada de la consola dedicada y entrega:

- autocompletado por prefijo para comandos y cvars
- sugerencias de argumentos para comandos que exponen `AutoCompleteSuggest()`
- salida en tabla cuando existen múltiples coincidencias
- providers manuales para ramas comunes de comandos `sm` y `meta`
- sugerencias de archivos reales del servidor para carga/recarga de plugins y extensiones

Este repositorio se mantiene de forma intencional como una versión **solo para L4D2**.

## Instalación

Requiere L4D2 dedicado x86, SourceMod 1.12 y MetaMod:Source 1.12.
Copia `addons/` del ZIP de tu plataforma a la raíz del juego:

- `addons/sourcemod/extensions/autocomplete.ext.2.l4d2.so` (Linux) o `.dll` (Windows).
- `addons/sourcemod/extensions/autocomplete.autoload`.
- `addons/sourcemod/gamedata/autocomplete.games.txt`.

Conserva la documentación fuera del servidor para evitar colisiones con otros
paquetes. Al migrar nombres antiguos `autocomplete.ext.so` / `.dll`, descarga de
memoria la copia antigua y retírala antes de instalar la canónica; deja una sola
copia de la extensión.

El [contrato de consola](docs/console/README.md) describe cvars, providers y ejemplos.
Consulta también los [límites del terminal](docs/console/terminal.md).

## Estructura del Repositorio

- `extension/src/` implementación de la extensión nativa
- `extension/include/` headers locales y shims del motor
- `extension/config/` header de configuración de la extensión SourceMod
- `addons/sourcemod/gamedata/` firmas y símbolos del juego
- `extension/` también contiene `autocomplete.autoload`, ya que pertenece canónicamente a la extensión
- `scripts/{deps,build,package,ci,tools}/` automatización por responsabilidad
- `docs/` notas del repositorio y documentación del alcance L4D2

## Compilación y paquetes

El [flujo de build](docs/build/README.md) usa GNU Make tanto en local como en CI:

```bash
make deps-exts-linux
make build-exts-linux
make package-exts-linux
make release-linux RELEASE_BASENAME=srcds-autocomplete-develop-linux
make validate-artifact-linux RELEASE_BASENAME=srcds-autocomplete-develop-linux
```

Windows usa los targets equivalentes con sufijo `windows` y MSVC x86.
Las descargas son explícitas; build, pruebas y release no actualizan SDKs.
El [mapa canónico](scripts/package/package-map.json) y el contrato compartido
controlan el contenido. `release-*` produce un ZIP local, sin publicarlo.

## Créditos

Este repositorio está basado en el proyecto original de peace-maker:

- [peace-maker/srcds-autocomplete](https://github.com/peace-maker/srcds-autocomplete)

También se conserva el crédito histórico del proyecto original a:

- Didrole, por ModuleScanner y el trabajo relacionado con SourceCurses

## Compilación con Ubuntu 26.04

El build Linux x86 admite GCC 15. Con GCC 14 o posterior se conserva `-Werror`
y se degrada únicamente `template-id-cdtor`, emitida por los constructores
antiguos del HL2SDK. La excepción no se aplica a Clang ni a versiones de GCC
anteriores. El SDK y el código de la extensión conservan el resto de sus gates.

La definicion `_stricmp=stricmp` coincide con el SDK L4D2 actual y evita una
redefinicion fatal; `stricmp` sigue resolviendose a `strcasecmp`. El build se
comprueba tambien con el SDK anterior, que no declara ese alias.

Compatibilidad comprobada: ejecución en Ubuntu 26.04 amd64 con las bibliotecas
i386 del motor L4D2 y compilación ELF32 con GCC/G++ 15.2.0 y multilib. El entorno
verificado usa glibc 2.43, libstdc++6 y libgcc-s1 en ambas arquitecturas; sus
paquetes de runtime proceden de GCC 16 y no cambian el compilador GCC 15 usado
para generar el candidato. Python 3.14.4 y AMBuild conducen la compilación;
SourceMod 1.12, Metamod 1.12 y HL2SDK L4D2 son dependencias de desarrollo.

Los ZIP Linux publicados por CI se generan en Ubuntu 22.04 con GCC 11.4.0;
son artefactos distintos de los candidatos compilados localmente con GCC 15.2.
Ambos se validan como ELF32: compatibilidad de carga no acredita pruebas con
jugadores ni establece esas versiones como mínimos del producto. Registrar el
commit de cada SDK y los SHA256 del ZIP al repetir una validación.

Consulta el [índice de documentación](docs/README.md) para contratos, dependencias, CI y análisis local.
