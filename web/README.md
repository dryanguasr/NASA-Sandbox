# Jezero · Mission Control

Borrador web en español para explorar misiones registradas de seis agentes.
Incluye demo guiada, mapa temporal, selección de agentes y objetivos,
comparación de políticas, tres videos integrados, evidencia descargable y
los documentos originales de preparación.

Es una presentación estática de resultados existentes. Cambiar de política
selecciona información guardada y no recalcula la misión. La política de
proximidad muestra sus resultados finales porque no tiene una trayectoria
inmutable incluida. Belva, la reproducción cinemática y el piloto sintético
conservan sus propias etiquetas, métricas e informes.

## Requisitos

- Node 22 o posterior y Git.
- `ffmpeg` y `ffprobe` disponibles en `PATH` para el build y la validación
  de los medios. No hacen falta Gazebo, ROS ni Python para construir la web.
- Historia Git que contenga los dos commits fijados abajo. El workflow
  de Pages utiliza `fetch-depth: 0` por este motivo.

La aplicación no tiene dependencias npm, CDN obligatorios ni backend; no
es necesario ejecutar `npm install`. Se probó con Node `v24.18.0` en Windows.

## Construir y abrir localmente

Desde la raíz del repositorio:

```text
node web/build.mjs
npm --prefix web test
node web/serve.mjs
```

Abrir [Mission Control local](http://127.0.0.1:4173/NASA-Sandbox/).
El servidor solo escucha en `127.0.0.1`. También sirve la raíz `/`, pero
la subruta `/NASA-Sandbox/` es la utilizada en validación. `Ctrl+C` detiene
el servidor. Para elegir otro puerto, definir la variable de entorno
`PORT` antes de iniciarlo.

Los cambios de HTML, CSS o JavaScript requieren repetir el build y recargar
la página. El build reemplaza únicamente `web/dist` y regenera los datos y
copias web bajo `web/public`; no escribe en los pilotos ni en la evidencia
científica original. `web/public`, `web/dist` y los archivos ZIP no están
versionados: se obtienen reproduciblemente con los scripts del repositorio.

No abrir `index.html` mediante `file://`: los módulos y las peticiones
`fetch` requieren un servidor HTTP. Para usar el build no hacen falta
internet, Node para cálculos científicos ni servicios remotos; Node solo
sirve los archivos. Los enlaces externos de atribución y el archivo
histórico no incluido sí requieren conexión al abrirlos.

## Fuentes y estructura

| Recurso | Función |
|---|---|
| `index.html`, `style.css`, `app.js`, `copy.js` | Interfaz, diseño y textos. |
| `replay.js` | Validación y selección temporal de registros; adaptador futuro desactivado. |
| `../scripts/build_web_data.mjs` | Exporta la misión, comparación y resumen Belva desde blobs de Git. |
| `../scripts/build_web_media.mjs` | Copia medios y documentos, extrae posters, calcula hashes y verifica decodificación. |
| `public/data/` | Contrato v1, JSON de pantalla y fuentes descargables generadas. |
| `public/media/` | Tres MP4 originales seleccionados y posters de fotogramas reales. |
| `public/media-manifest.json` | Videos, catálogo de evidencia y procedencia de las copias. |
| `public/evidence/`, `public/preparacion/` | Informes, originales descargables y manual interactivo. |
| `dist/` | Único directorio estático destinado a publicación. |

La evidencia científica está fijada a
`450fa0c57b4073e0d96060a2a28c5c50d6393dd9`; la preparación a
`87574fc99a11b20870481426e93178bdd87d21a0`. No se incorporan silenciosamente
resultados modificados en el checkout. Cambiar una fuente exige revisar
el contrato, la fidelidad y las pruebas, no editar cifras para mejorar
la demostración. Consultar [data-contract.md](data-contract.md).

El mapa de pantalla reutiliza una cuadrícula de 64×64 a 8 m del visor
existente; el cálculo original usó 128×128 a 4 m. El contenido nativo de
CTX sigue siendo de 20 m. Las alturas visuales tienen escala normalizada;
la incertidumbre conserva su escala condicional de 0 a 3 m. Los objetivos
solo se muestran después de su detección registrada.

## Pruebas y recorrido manual

```text
npm --prefix web test
node web/serve.mjs
```

Con el servidor activo, abrir el
[arnés de navegador](http://127.0.0.1:4173/__tests__/browser.html), pulsar
**Ejecutar pruebas** y descargar la evidencia JSON. Prueba la aplicación
construida, videos, enlaces, estados, errores recuperables, tamaños de
pantalla y el manual. Las pruebas de preparación usan otra clave de
almacenamiento local para preservar las notas existentes.

El arnés bloquea conexiones externas con CSP y no se publica dentro de
`dist`. Su reflow a 910 px no equivale a cambiar el zoom real del navegador,
y detectar una regla de movimiento reducido no equivale a emularla.
Completar la revisión con teclado, zoom al 150 %, movimiento reducido y
capturas inspeccionadas de 1366×768, 1920×1080 y 390×844.

El estado exacto de las pruebas ejecutadas, las limitaciones y las imágenes
están en [el informe de validación](../docs/web_interface_validation.md).
No se realizó un estudio con usuarios.

## Respaldo portable

El build medido en esta revisión tiene 92 archivos y 10,78 MB decimales.
Conserva los tres videos y los datos esenciales, sin descargar todo el
archivo audiovisual histórico.

Para preparar un ZIP portable en Windows después del build:

```powershell
node web/package-portable.mjs
Compress-Archive -Path web/portable/* -DestinationPath web/mission-control-portable.zip -Force
```

Descomprimir en una carpeta vacía. Deben quedar `dist/` y `serve.mjs` al
mismo nivel. Con Node instalado:

```text
node serve.mjs dist
```

Abrir la URL local anunciada. El servidor conserva la subruta
`/NASA-Sandbox/` y las peticiones parciales necesarias para seek de video.
Alternativamente, desde `dist/`, `python3 -m http.server 4173` permite
abrir la raíz `http://127.0.0.1:4173/` si Python está disponible.
El arnés de desarrollo no está incluido en este paquete portable.

El ZIP permite consumir el sitio sin la historia Git ni FFmpeg; estos son
requisitos para reconstruirlo desde código fuente. El ZIP entregado tiene
8.422.693 bytes y SHA-256
`340cb86ceae92ad6c7d1e150c1d0f90531cba5268cdcb64cf3eb85a92f443cb3`.
Se extrajo en una carpeta independiente: sus 92 archivos estáticos coinciden
byte por byte con el build. Se abrió en el puerto 4174 y se recorrió la demo
con teclado sin errores de consola. Ver `evidence/ui_draft/portable-validation.json`.

## Publicación

Sites es el destino primario. `web/.openai/hosting.json` conserva la
identidad del sitio y declara `dist` como salida estática. No reemplazar el
ID ni crear otro sitio al reintentar. El estado y la URL comprobada se
registran en el informe de validación. Esta revisión se publicó como
[sitio privado de Sites](https://jezero-mission-control-lab.davidyr.chatgpt.site).
La visita anónima redirige al inicio de sesión de OpenAI. Hacerlo público
requiere la autorización explícita pendiente; no se afirma acceso sin
autenticación. Un build o una identidad de Sites, por sí solos, no prueban
publicación.

Como alternativa, el [workflow de Pages](../.github/workflows/pages.yml)
construye y prueba el proyecto y carga únicamente `web/dist`. El despliegue
requiere ejecución manual con `deploy: true`, Pages configurado y aprobación
del entorno `github-pages` cuando corresponda. No se activa automáticamente
al subir la rama. No se ha declarado una URL de Pages publicada.

## Límites de uso

Los sensores y marcadores científicos son simulados o ficticios. Los
humanos y drones conservan componentes cinemáticos; la interfaz no valida
vuelo marciano, biomecánica, seguridad EVA ni operaciones reales. Los casos
principales mantienen comunicación global ideal. El manual de preparación
guarda notas en el navegador, sin sincronización entre personas.

Es un laboratorio independiente y un borrador, no un producto oficial de
NASA ni una entrega competitiva. La reutilización en una competencia
requiere resolver las reglas sobre trabajo previo con sus organizadores.
