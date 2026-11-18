# CI y canales

Actions configura hosts, cachés y transporte. El producto se prueba, compila,
empaqueta y valida mediante Make. Sonar, cobertura y pruebas de sus herramientas
permanecen fuera del pipeline y de `make test-ci`.

El workflow se activa por push a main/develop, tags `v*`, PRs con rutas relevantes
y ejecución manual. Linux usa Ubuntu 22.04; Windows, Windows 2022. Cada plataforma
restaura sus dependencias y conserva el build junto con su recibo para empaquetarlo
en un job posterior. La caché incluye scripts/mapa/Make/configuración del build;
no equivale a un lock de las ramas móviles descargadas.

`make release-identity-linux` / `make release-identity-windows` resuelven identidad
sin publicar. Las variables `AOC_REF_TYPE`, `AOC_REF_NAME` y `AOC_COMMIT_SHA`
seleccionan ref; por defecto se genera identidad local.

| Ref | Assets | Release |
|---|---|---|
| main | `srcds-autocomplete-latest-<platform>.zip` | `channel/latest`, Latest |
| develop | `srcds-autocomplete-develop-<platform>.zip` | `channel/develop`, prerelease |
| tag `v1.2.3` | `srcds-autocomplete-1.2.3-<platform>.zip` | Tag versionado |
| PR u otra rama | Artefactos temporales | Sin publicación |

La publicación espera pruebas y los dos paquetes validados. Solo ese job dispone
de escritura. En canales comprueba ambos ZIP, mueve el tag, retira la release
anterior, crea borrador, carga ambos assets y después publica. Puede existir una
ventana sin descarga; un fallo de upload deja un borrador y necesita reintento.
Las releases versionadas conservan upload con `--clobber`; no son inmutables.
Las notas de canal contienen canal, UTC, commit y ejecución/intento de CI.

Modificar el workflow localmente no ejecuta Actions ni publica. Validarlo con
`make check-ci`; su ejecución remota requiere una publicación autorizada posterior.
