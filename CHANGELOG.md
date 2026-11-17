# Historial de cambios

## Sin publicar

- Se organizan scripts por dependencias, compilación, paquetes, CI y herramientas.
- Se centraliza el mapa en `scripts/package/package-map.json` y se traslada el
  gamedata a su ruta SourceMod, sin cambiar su contenido ni destino de instalación.
- Make comparte las fases de local y CI, incluida la validación del árbol y ZIP.
- Los paquetes comprueban contenido, arquitectura y procedencia del build actual;
  rechazan recursos ausentes, archivos ajenos, enlaces y resultados desactualizados.
- Se conserva el nombre nativo con sufijo `2.l4d2` y se corrige la instalación documentada.
- Se incorporan pruebas de paquetes y análisis Sonar explícito local separado de CI.
- Se organiza documentación por funcionalidad y se inventarían dependencias móviles.
