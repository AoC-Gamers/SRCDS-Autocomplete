# Licencias y procedencia

El repositorio original incluye el texto de la GPL versión 3 desde su primer
commit. El fork conserva [LICENSE](../../LICENSE) y los avisos de los archivos
que proceden de otros proyectos. La siguiente relación organiza su procedencia
por rutas. El historial de Git conserva los autores de las contribuciones.

| Rutas | Licencia y procedencia |
| --- | --- |
| `extension/src/extension.cpp`, `extension/config/smsdk_config.h` | GPL versión 3 con las excepciones descritas en las cabeceras originales de AlliedModders LLC. Conservan las contribuciones del proyecto original de peace-maker y del fork. |
| `extension/include/extension.h`, `extension/autocomplete.autoload`, `addons/sourcemod/gamedata/autocomplete.games.txt` | Licencia GPL versión 3 del proyecto. Son parte de la extensión y sus recursos, derivados del proyecto original y adaptados en el fork. |
| `extension/include/textconsole.h`, `extension/include/hex-string.h`, `extension/src/hex-string.cpp` | GPL versión 3 del proyecto. El shim modela la interfaz usada por el motor y el decodificador procede del código de la propia extensión. |
| `AMBuilder`, `AMBuildScript`, `PackageScript`, `configure.py` | Archivos de build heredados del proyecto original y adaptados en el fork bajo la licencia del proyecto. La procedencia de las plantillas heredadas queda por confirmar. |
| `scripts/`, `tests/`, `.github/`, `Makefile`, `.gitattributes`, `.gitignore`, `.env.example`, `.env.secret.example`, `AGENTS.md`, `README.md`, `CHANGELOG.md`, `docs/` | Archivos de soporte bajo la licencia del proyecto. Los proveedores en `tests/native/providers/` son dobles de prueba que modelan interfaces de los SDK. |
| `LICENSE` | Textos legales y avisos conservados con las condiciones y atribuciones que indican sus propias fuentes. |

El anexo de [LICENSE](../../LICENSE) recoge las excepciones de
SourceMod y los avisos revisados de AMTL, SourceHook, SafetyHook y Zydis/Zycore
para el binario de la extensión. Los textos se contrastaron con SourceMod
`3f7460671f7adc4a3c6791a47d21ba3e7b5fba91` (AMTL `2d3b1a3`, SafetyHook
`8c6692c`) y Metamod:Source `4e031eb571f5978eea8207b5d915c9cd0e8d6c58`.
La excepción de SourceMod se reproduce con sus referencias originales. El
texto GPLv3 de este proyecto está en `LICENSE`. No se incluyen los SDK completos.

Antes de publicar otro binario, revisar el inventario de dependencias y las
entradas de compilación/enlace de **ambas** plataformas. Las ramas de SourceMod
y Metamod pueden cambiar los componentes incorporados. Falta confirmar las
condiciones de redistribución del código de Valve incorporado por los archivos
estáticos del SDK L4D2 (Linux enlaza `tier1_i486.a` y `mathlib_i486.a`) y completar la comprobación de avisos para cada plataforma.

Para cumplir las obligaciones de fuentes correspondientes, hay que verificar
qué fuentes, revisiones de dependencias, cambios y scripts del build se deben
poner a disposición de quien descargue el binario. El enlace del README al
commit del proyecto facilita localizar sus fuentes. Por sí solo no demuestra
que se puedan obtener las fuentes correspondientes completas.
