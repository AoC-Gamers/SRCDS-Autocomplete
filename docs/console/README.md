# Autocompletado de consola

## Qué Resuelve

El uso de la consola vanilla de SRCDS es incómodo para trabajo operativo. Esta extensión mejora:

- el descubrimiento de comandos al trabajar directamente en la terminal del servidor
- el autocompletado de comandos largos del motor o de plugins
- las sugerencias de argumentos para comandos como `changelevel`
- la navegación de ramas comunes de SourceMod y MetaMod

Ejemplos:

```text
statu<Tab>           -> status
changelev<Tab>       -> changelevel
changelevel <Tab>    -> sugerencias de mapas
sm e<Tab>            -> sm exts
sm exts l<Tab>       -> sm exts list
sm plugins lo<Tab>   -> sm plugins load
sm exts lo<Tab>      -> sm exts load
meta ve<Tab>         -> meta version
```

## Alcance

Este repositorio apunta deliberadamente a:

- `Left 4 Dead 2`
- SourceMod `1.12`
- MetaMod:Source `1.12`
- servidores dedicados Linux y Windows

Los caminos legacy multi-engine del proyecto original fueron removidos para reducir costo de mantenimiento y dejar la extensión alineada con el target real de despliegue.

## Instalación

Debes desplegar estos archivos en el servidor:

- `addons/sourcemod/extensions/autocomplete.ext.2.l4d2.so` o `autocomplete.ext.2.l4d2.dll`
- `addons/sourcemod/extensions/autocomplete.autoload`
- `addons/sourcemod/gamedata/autocomplete.games.txt`

Notas:

- la extensión está pensada para uso en consola del servidor dedicado
- `autocomplete.autoload` debe permanecer junto a la extensión para que SourceMod la cargue automáticamente

## Depuración

La extensión expone las siguientes `ConVar`:

```text
sm_autocomplete_debug
sm_autocomplete_max_results
```

`sm_autocomplete_debug`

- `0` = desactivado
- `1` = escribe información de depuración en los logs de SourceMod

Ejemplo:

```text
sm_cvar sm_autocomplete_debug 1
```

Cuando está activo, la extensión registra:

- la línea de entrada actual
- la cantidad de coincidencias encontradas
- los primeros resultados encontrados
- si tomó la ruta de match único o múltiples matches

`sm_autocomplete_max_results`

- define el máximo de sugerencias que se mostrarán en una tabla
- valor por defecto: `32`
- rango: `1` a `256`

Ejemplo:

```text
sm_cvar sm_autocomplete_max_results 16
```

## Providers Manuales

Además del autocompletado normal del motor, la extensión agrega soporte manual para ramas comunes de comandos.

### SourceMod

Primer nivel:

- `sm credits`
- `sm cvars`
- `sm dump_handles`
- `sm exts`
- `sm info`
- `sm plugins`
- `sm profiler`
- `sm reload_translations`
- `sm version`

Segundo nivel:

- `sm exts info`
- `sm exts list`
- `sm exts load`
- `sm exts reload`
- `sm exts unload`
- `sm plugins info`
- `sm plugins list`
- `sm plugins load`
- `sm plugins reload`
- `sm plugins unload`

### MetaMod

- `meta clear`
- `meta credits`
- `meta game`
- `meta list`
- `meta load`
- `meta pause`
- `meta refresh`
- `meta retry`
- `meta unload`
- `meta unpause`
- `meta version`

## Sugerencias de Archivos

La extensión también puede sugerir archivos reales del servidor en estos contextos:

- `sm plugins load`
- `sm plugins reload`
- `sm plugins unload`
- `sm exts load`
- `sm exts reload`
- `sm exts unload`

Resolución actual:

- plugins:
  - `addons/sourcemod/plugins`
  - extensión `.smx`
- extensiones:
  - `addons/sourcemod/extensions`
  - `.so` en Linux
  - `.dll` en Windows


Ver [límites del terminal](terminal.md).
