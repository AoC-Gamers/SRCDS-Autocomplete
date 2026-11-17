# Sonar C/C++ local

`make sonar-cppcheck` ejecuta Cppcheck local con la base real exportada por
`make build-exts-linux`. `make sonar` añade un envío explícito al servidor
configurado y espera el quality gate. No se ejecuta en CI ni desde `make test`.

Instala Cppcheck y SonarScanner explícitamente. El servidor debe tener un plugin
sonar-cxx compatible; no es SonarCFamily. No se crean proyectos, tokens ni plugins
automáticamente. Copia `env.example` a `.env` y configura URL y proyecto propios;
`SONAR_TOKEN` se aporta por entorno o `env.secret` ignorado (modo 600). No lo
incluyas en argumentos ni documentación. HTTPS es obligatorio salvo loopback.
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

Esta integración no importa cobertura: no hay un harness nativo de producto que
la mida actualmente. Las líneas sin ejecutar permanecen sin cobertura; compilar o
contar assertions no mide ejecución. No aportar informes ajenos o antiguos para
aprobar un gate. Un servidor sin configurar o un analizador ausente es un límite
explícito, no un análisis aprobado. El análisis tampoco acredita aceptación SRCDS.

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
