# Historial de cambios

## Sin publicar

- Se amplían las pruebas reales de consola y automatización, sin modificar el
  código del producto ni excluir líneas de la medición.
- El harness x86 ejecuta la implementación canónica con proveedores controlados,
  shim de consola real y archivos reales, también bajo ASan/UBSan.
- Los recibos de cobertura validan contadores en subdirectorios y rechazan
  alteraciones o rutas que escapen de la ejecución medida.

- Se corrige el contexto de sonar-cxx para ignorar únicamente directorios de include
  opcionales ausentes, conservando los flags del build y el parser estricto.
- Los errores del scanner impiden aceptar un análisis aunque su proceso devuelva éxito.
- Se reduce complejidad del tooling y se conserva la convención de llamada x86
  con sintaxis GNU de atributos compatible con el parser.
- Se incorpora cobertura real local con hashes de fuentes, informes y contadores;
  el código de consola sin ejecutar se mantiene como no cubierto.

- La configuración Sonar se carga desde `.env`, con plantilla pública `env.example`,
  sin depender de `sonar-project.properties`; conserva el parser estricto.

- Se corrige la decodificación hexadecimal de firmas: las secuencias malformadas
  se conservan literales y no leen valores sin inicializar. Se mantienen bytes
  NUL, límites del buffer y escapes válidos.
- Se valida la longitud de una sugerencia antes de calcular el texto restante.
- Se explicitan overrides, const y conversiones C++ sin cambiar la ABI de consola.

- Se organizan scripts por dependencias, compilación, paquetes, CI y herramientas.
- Se centraliza el mapa en `scripts/package/package-map.json` y se traslada el
  gamedata a su ruta SourceMod, sin cambiar su contenido ni destino de instalación.
- Make comparte las fases de local y CI, incluida la validación del árbol y ZIP.
- Los paquetes comprueban contenido, arquitectura y procedencia del build actual;
  rechazan recursos ausentes, archivos ajenos, enlaces y resultados desactualizados.
- Se conserva el nombre nativo con sufijo `2.l4d2` y se corrige la instalación documentada.
- Se incorporan pruebas de paquetes y análisis Sonar explícito local separado de CI.
- Se organiza documentación por funcionalidad y se inventarían dependencias móviles.
