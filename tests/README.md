# Pruebas

`make test TEST_OUTPUT=<directorio-nuevo>` ejecuta regresiones de staging, ZIP,
identidad y Make desde un cwd externo con espacios y fuentes sin `.git`.
`make test-ci` usa la misma suite. El directorio existente se rechaza, no se
reutilizan logs y no se descargan SDKs.

Los binarios de esas pruebas son cabeceras ELF32/PE32 sintéticas: permiten probar
rechazo de arquitectura, contenido y manipulación, pero no se pueden cargar.
La compilación real se comprueba por separado mediante `build-exts-*` y los ZIP
se validan mediante `validate-artifact-*`. Ni esas pruebas ni compilar acreditan
funcionamiento de hooks, terminales o carga en SRCDS.

`make sonar-tooling-test` prueba configuración, parser y contexto del analizador
sin acceder al servidor. Es local y no forma parte de `make test-ci`.

`make test-hex-string` compila el decodificador real en x86 con ASan/UBSan;
comprueba los 256 bytes, escapes mixtos, malformados/truncados, capacidades y
canarios. Forma parte de `test-ci`, que requiere GCC/G++ multilib y sanitizadores.
`make test-exports ABI_BASELINE_ZIP=<zip-linux-anterior>` compara arquitectura ELF
y nombres/tipos de símbolos exportados; no acredita toda la ABI ni carga SRCDS.

La medición local usa `test-python-coverage` y `test-coverage` con `TEST_OUTPUT`
nuevo. `coverage-tooling-test` rechaza fuentes/informes obsoletos y contadores
no ejecutados con hits. Estas herramientas no forman parte de `test-ci` ni Actions.
`test-exports TEST_EXPORT_OPTIONS=--same-text` exige además código máquina `.text`
idéntico al ZIP de referencia, útil para cambios puramente sintácticos.

`make test-console` ejecuta el código canónico de `extension.cpp` en x86 con
ASan/UBSan y proveedores controlados del SDK. Conserva el shim `CTextConsole`
real y usa archivos/directorios reales. Comprueba autocompletado manual y del
motor, clasificación/orden, tablas y prefijos comunes, truncamiento, buffers,
logging, gamedata, carga, descarga y fallos controlados. No carga el engine de
SRCDS ni acredita su ABI: el build nativo con SDKs reales se valida por separado.
La suite forma parte de `test-ci`; solo su medición gcov es local.

`canonical_cli_test.py` invoca los scripts canónicos sobre entradas de prueba
aisladas, incluida exportación de órdenes compiladas, recibos, staging/ZIP,
validación, identidad, limpieza y scanner con ejecutables simulados sin red.
No se remapean hits desde copias temporales a fuentes del repositorio.
