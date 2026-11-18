# Sonar C/C++ local

`make sonar-cppcheck` ejecuta Cppcheck local con la base real exportada por
`make build-exts-linux`. `make sonar` añade un envío explícito al servidor
configurado y espera el quality gate. No se ejecuta en CI ni desde `make test`.

Instala Cppcheck y SonarScanner explícitamente. El servidor debe tener un plugin
sonar-cxx compatible; no es SonarCFamily. No se crean proyectos, tokens ni plugins
automáticamente. Copia `env.example` a `.env` y configura URL y proyecto propios;
Copia `env.secret.example` a `env.secret`, aplica permisos `600` y completa
`SONAR_TOKEN` con un token de análisis limitado al proyecto. También puedes
aportarlo mediante el entorno. `env.secret` está ignorado por Git; las plantillas
versionadas no contienen credenciales. No incluyas el token en argumentos ni documentación. HTTPS es obligatorio salvo loopback.
Las variables de entorno tienen precedencia sobre los archivos locales.
Todas las propiedades del análisis se cargan desde `.env` (plantilla `env.example`);
el ejecutor las pasa al scanner sin necesitar `sonar-project.properties`.
El parser estricto permanece obligatorio aunque se cambie la configuración local.

```bash
make sonar-tooling-test
make sonar-cppcheck
make sonar
```

La base debe incluir exactamente las unidades propias de `extension/`, con cwd
absoluto y flags x86 reales. Se consultan macros e includes del compilador con los
mismos flags, conservando el orden de `-D`/`-U`. Cada ejecución usa una salida
nueva en `.build/sonar/`; los errores de parser o XML incompleto impiden el envío.
El scanner usa parser estricto (`sonar.cxx.errorRecoveryEnabled=false`) y espera
el gate; un fallo no se transforma en PASS ni se relajan umbrales.

La cobertura se mide explícitamente, fuera de CI, sobre fuentes canónicas:

```bash
make deps-test-coverage
make test-python-coverage TEST_OUTPUT=.build/coverage-python
make test-coverage TEST_OUTPUT=.build/coverage-native
make coverage-tooling-test
```

`COVERAGE_PYTHON` permite usar un Python existente con coverage.py 7.13.5 sin
instalar ni actualizar dependencias. Configura `SONAR_PYTHON_COVERAGE_RECEIPT`
y `SONAR_COVERAGE_RECEIPT` con los recibos generados. Sonar comprueba hashes de
fuentes/pruebas, informe y datos originales antes y después del envío. Un cambio
relevante exige regenerar la cobertura; no se aceptan resultados desactualizados.

Python mide líneas realmente ejecutadas, incluidos subprocesos; las copias de
fuentes en directorios temporales de pruebas no aportan hits a las canónicas.
GCC/gcov mide el decodificador y la implementación completa de consola en x86.
El harness incluye sin modificar `extension.cpp`, usa el shim real de consola,
proveedores controlados para SDK/engine y directorios reales para los archivos.
El baseline compila además todas las unidades con los flags reales del build;
las líneas que ningún ensayo ejecuta permanecen sin hits. No se atribuyen hits
al SDK, a los proveedores ni a copias temporales del producto. Estas pruebas
controladas no acreditan carga ni jugabilidad en un servidor SRCDS real.
No se importan contadores de binarios mutados ni se estima cobertura desde la
compilación. Las pruebas ASan/UBSan continúan por separado mediante `test-ci`.

El gate mantiene sus umbrales. Cobertura parcial, errores de parser, un servidor
sin configurar o herramientas ausentes no acreditan una validación aprobada.
El análisis tampoco sustituye aceptación de carga y hooks en SRCDS.

## Avisos procedentes de proveedores externos

El informe completo conserva los diagnósticos de headers del HL2SDK, SourceMod
y MetaMod. No se excluyen ni se consideran resueltos por no pertenecer al proyecto.
En particular, los avisos `memleakOnRealloc` del HL2SDK señalan asignaciones
directas del resultado de `realloc` al puntero original; su tratamiento de fallo
de asignación requiere revisión del proveedor, sin parchear el SDK durante una
corrección de la extensión.

Las macros `GET_V_IFACE_CURRENT` de MetaMod y `DETOUR_CREATE_MEMBER`/callbacks
de CDetour contienen conversiones C. Cppcheck puede atribuirlas a la línea que
invoca la macro en `extension.cpp`. Se mantienen para conservar el contrato de
interfaces y callbacks; son avisos de estilo de esas expansiones, no conversiones
C propias pendientes de sustituir. No se suprimen en el analizador.

Las regresiones de comportamiento del decodificador se ejecutan con
`make test-hex-string`, también desde `make test-ci`. Esta suite usa el código
real del producto en x86 y ASan/UBSan; no equivale a aceptación de hooks en SRCDS.
