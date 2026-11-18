# Instalar SRCDS Autocomplete

La extensión añade autocompletado con Tab a la consola dedicada de Left 4 Dead 2.
Requiere L4D2 dedicado x86 con `-console`, SourceMod 1.12 y MetaMod:Source 1.12.

1. Elige el ZIP de tu plataforma. Si ya tienes una versión instalada, detén el
   servidor y guarda una copia de los archivos que vas a reemplazar.
2. Copia solo `addons/` del ZIP a la raíz del juego. El paquete instala
   `addons/sourcemod/extensions/autocomplete.ext.2.l4d2.so` en Linux o
   `autocomplete.ext.2.l4d2.dll` en Windows, con `autocomplete.autoload` junto al
   binario y `addons/sourcemod/gamedata/autocomplete.games.txt` para las firmas.
   Retira el binario antiguo si se llama `autocomplete.ext.so` o
   `autocomplete.ext.dll`. Conserva los documentos fuera del árbol del juego.
3. Arranca el servidor. Comprueba que la extensión aparece cargada en
   `sm exts list` y pulsa Tab tras escribir `statu` en la consola dedicada.
4. Para revertir, detén el servidor, retira los archivos instalados y restaura
   la copia de la versión anterior antes de arrancar de nuevo.

Las sugerencias dependen del comando y del soporte de Tab del terminal.
