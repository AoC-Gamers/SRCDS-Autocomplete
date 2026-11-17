# Sonar C/C++ local

`make sonar-cppcheck` ejecuta Cppcheck local con la base real exportada por
`make build-exts-linux`. `make sonar` añade un envío explícito al servidor
configurado y espera el quality gate. No se ejecuta en CI ni desde `make test`.

Instala Cppcheck y SonarScanner explícitamente. El servidor debe tener un plugin
sonar-cxx compatible; no es SonarCFamily. No se crean proyectos, tokens ni plugins
automáticamente. Copia `.env.example` a `.env` y configura URL y proyecto propios;
`SONAR_TOKEN` se aporta por entorno o `env.secret` ignorado (modo 600). No lo
incluyas en argumentos ni documentación. HTTPS es obligatorio salvo loopback.
Las variables de entorno tienen precedencia sobre los archivos locales.

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
