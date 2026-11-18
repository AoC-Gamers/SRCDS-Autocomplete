# Compilación y paquetes

GNU Make es la interfaz común de local y CI. Linux requiere Python 3, Bash,
Git y GCC/G++ con multilib x86. Windows requiere GNU Make, Bash, Python,
PowerShell y Visual Studio Build Tools con MSVC x86.

Ejecutar cada fase en orden; ninguna descarga ni ejecuta la fase anterior:

```bash
make deps-exts-linux
make build-exts-linux
make package-exts-linux
make release-linux RELEASE_BASENAME=srcds-autocomplete-develop-linux
make validate-artifact-linux RELEASE_BASENAME=srcds-autocomplete-develop-linux
```

Windows usa los mismos targets con sufijo `windows`. `make help` enumera las
operaciones. `release-*` genera solo un ZIP local: no usa credenciales ni publica.
Los defaults locales son `srcds-autocomplete-local-<platform>.zip`.

Las dependencias se ubican en `.deps/exts-<platform>/`, el build en
`.build/<platform>-l4d2/`, staging en `.build/package-exts-<platform>/`,
el árbol final en `dist/<platform>/artifact/` y ZIP en `dist/release/`.
`LINUX_*_DIR`, `WINDOWS_*_DIR` y `PYTHON` permiten seleccionar otras rutas.
Los destinos destructivos de build y staging deben ser subdirectorios de `.build/`
o `dist/` del repositorio; se rechazan las propias raíces, las fuentes, destinos
externos, enlaces y rutas que se solapen con entradas o SDKs. Los overrides de
salida deben mantenerse dentro de esas áreas gestionadas.
Los directorios de dependencias externos se usan tal como están: no se actualizan
al compilar. Las rutas relativas indicadas por el usuario se interpretan desde su
cwd; los defaults se resuelven desde el Makefile incluso con `make -f` externo.

El [mapa](../../scripts/package/package-map.json) es la única selección de producto.
La extensión mantiene `autocomplete.ext.2.l4d2.so` / `.dll`. El ZIP incluye solo
la extensión propia, autoload, gamedata, el README de instalación, el changelog
y el archivo `LICENSE`. La guía se genera para la plataforma y enlaza al SHA base
si el checkout tiene metadatos Git. Un árbol local sin Git se identifica como tal.
Consulta [licencias y procedencia](licensing.md) antes de distribuir un binario.

El adaptador del backend AMBuild 2.1 exporta `compile_commands.json` desde su
grafo de compilación exitoso, sin reconstruir ni modificar las órdenes. El build emite un recibo de fuentes/binario y un
inventario efectivo `dependency-revisions.json`. El inventario se escribe primero
y el recibo de éxito se instala al final mediante reemplazo atómico. Cada intento
invalida su recibo anterior. Un build fallido no emite recibo
válido. Staging comprueba ese recibo; cambiar fuentes o scripts exige recompilar.
No hay garantía de reproducibilidad byte a byte ni de entradas transitivas fijadas.
La arquitectura se valida como ELF32 i386 shared object o PE32 i386 DLL; esa revisión
no acredita carga, hooks ni autocompletado en SRCDS.

```bash
make test TEST_OUTPUT=.build/tests-local
make check-ci
```

Las pruebas usan un directorio nuevo, no descargan dependencias y tienen controles
negativos sobre contenido, arquitectura, ZIP, procedencia e identidad de canales.
Ver [límites de pruebas](../../tests/README.md).

`clean-linux` y `clean-windows` eliminan salidas de la plataforma; `clean-all`
elimina `.build`, `dist` y `.deps` propios. No apuntar las salidas gestionadas a
fuentes ni datos ajenos. Los SDK externos no se borran mediante `clean-all`.
