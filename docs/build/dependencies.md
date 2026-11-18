# Dependencias

Producto: una extensión C++ propia (`extension/src/extension.cpp`), un shim de
consola propio, autoload y gamedata. No hay plugins SourcePawn, modos ni API include
pública que distribuir. La versión del producto permanece en
`extension/config/smsdk_config.h`.

| Dependencia / origen | Rol y consumidor | Selección | Resolución y distribución |
|---|---|---|---|
| [HL2SDK](https://github.com/alliedmodders/hl2sdk) | Headers y bibliotecas de build nativo | `l4d2` móvil | SHA efectivo en recibo; no distribuir SDK ni bibliotecas del motor |
| [SourceMod](https://github.com/alliedmodders/sourcemod) | SDK, CDetour y soporte de extensión; runtime externo | `1.12-dev` móvil / runtime 1.12 | SHA y submódulos en recibo; no distribuir instalación base |
| [MetaMod:Source](https://github.com/alliedmodders/metamod-source) | SDK SourceHook; runtime externo | `1.12-dev` móvil / runtime 1.12 | SHA y submódulos en recibo; externo |
| [AMBuild](https://github.com/alliedmodders/ambuild) | Configuración/build y base de compilación | `master` móvil | SHA efectivo; externo; el adaptador exporta compdb del grafo AMBuild 2.1 |
| Paquete oficial SourceMod | Bootstrap heredado | `sourcemod-latest-linux/windows` 1.12 móvil | No consumido por el build nativo; no se empaqueta |
| Python 3, pip, venv | Automatización y AMBuild | Host; pip actualizado solo al ejecutar deps | Versiones del host; externos |
| GCC/G++ multilib o MSVC x86 | Compilador y linker | Host | No fijados; conservar warnings y flags de arquitectura |
| GNU Make, Bash, PowerShell, Git, curl | Automatización por plataforma | Host | Externos |
| coverage.py 7.13.5, GCC/gcov | Cobertura local de pruebas Python y C++ | Python fijado en `tests/requirements-coverage.txt`; gcov del compilador | Externos; recibos con hashes; fuera de CI y paquetes |
| Cppcheck, SonarScanner, plugin sonar-cxx | Análisis local opcional | Instalación explícita del usuario | No descargados por build/tests; no empaquetados |

Los fetch conservan las ramas existentes y actualizan solo al invocar explícitamente
`make deps-exts-linux` / `make deps-exts-windows`. No constituyen un lock reproducible:
la selección de ramas, pip y las descargas oficiales siguen móviles. No se cambiaron
versiones de SDK por esta reorganización. Los avisos y licencias revisados se describen en
[licencias y procedencia](licensing.md).

Para validar con SDKs ya disponibles, seleccionar `LINUX_DEPS_DIR` o
`WINDOWS_DEPS_DIR`. El build escribe `dependency-revisions.json` con SHA, submódulos
y estado dirty de los repositorios efectivamente usados; es evidencia de build,
no configuración de actualización ni contenido instalable.

Al actualizar dependencias: seleccionar revisiones deliberadamente, revisar APIs,
registrar hashes/SHA, invalidar caché, ejecutar Make de build/pruebas/paquete en
cada SO y validar runtime por separado cuando cambien ABI o hooks.

`HL2SDK_DIR` selecciona un directorio L4D2 concreto, incluso fuera de
`LINUX_DEPS_DIR` / `WINDOWS_DEPS_DIR`. Build e inventario usan la misma ruta
absoluta mediante `--hl2sdk-path`; no se actualiza el SDK seleccionado.
