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
