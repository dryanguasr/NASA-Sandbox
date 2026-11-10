# Validación del borrador Mission Control

Fecha: 10 de noviembre de 2026, America/Bogota. Rama de trabajo:
`ui/mission-control-draft`. Este informe documenta una interfaz de registros
existentes; las pruebas web no son nuevas ejecuciones científicas.

## Resultado comprobado

El build local contiene 92 archivos y 10.778.832 bytes (10,78 MB decimales)
en la medición de esta revisión. Pasaron 17 pruebas de Node y las 16 pruebas
de navegador registradas en
[browser-validation.json](../evidence/ui_draft/browser-validation.json).
Las dos regresiones estáticas originales también pasaron. No se ejecutaron
Gazebo, los planificadores ni nuevos pilotos para producir la interfaz.

Se inspeccionaron capturas de escritorio y móvil y se comprobó la selección
de un objetivo mediante Enter, conservando el foco. La comprobación de zoom
real al 150 % y la emulación de movimiento reducido siguen pendientes en
este registro; el reflow a 910 px y la presencia de una regla CSS no se
presentan como sustitutos de esas verificaciones.
Los atajos enviados por la extensión no cambiaron el zoom del navegador;
el acceso al control nativo de Chrome agotó su espera de autorización.
En la revisión posterior, el navegador rechazó también abrir su página
de configuración de apariencia: la política de la herramienta admite solo
HTTP/HTTPS y prohíbe eludir ese bloqueo mediante otras superficies o
comandos. No se intentó hacerlo. Tampoco se ha ejecutado el paquete con
Internet efectivamente desconectado: el aislamiento por CSP comprueba
independencia de recursos externos, pero no sustituye esa prueba literal.
No se declaran cerrados AC09, AC10 ni el conjunto completo de AC01–AC12.

## Criterios AC01–AC12

| ID | Estado y comprobación | Evidencia y alcance |
|---|---|---|
| AC01 | Verificado: build estático y servidor local documentados; 17 pruebas Node aprobadas. | [Instrucciones](../web/README.md), [build](../web/build.mjs), [pruebas](../web/tests/). Node v24.18.0 en Windows; el requisito mínimo es Node 22. |
| AC02 | Verificado: portada, acceso al explorador, siete pasos guiados y llegada al comparador. | Prueba de navegador AC02; hitos reales 0, 40, 85, 525, 920, 1335 y 1930 s. Capturas de escritorio y móvil enlazadas abajo. |
| AC03 | Verificado: seis identificadores, coordenadas y tareas registradas; capas temporalmente coherentes. | Pruebas Node y navegador. S2 no aparece a 80 s; aparece a 85 s. La inspección a 525 s habilita el muestreo. Mapas y posiciones muestran el tiempo de su última muestra; no se inventa interpolación científica. HiRISE está desactivado inicialmente y rotulado como evaluación. |
| AC04 | Verificado: play/pausa, seek, doble clic, reinicio, final y cambio de ejecución. | Pruebas del adaptador y navegador. Cambiar a proximidad limpia selección y reproducción y muestra que no hay trayectoria inmutable incluida. No se calcula una misión ni se reutiliza la animación informativa. |
| AC05 | Verificado: valores visibles comparados directamente con el JSON de origen. | Tres semillas por política; t80 de 320 frente a 440 s, duración de 1930 frente a 1660 s y distancia aérea de 5270,5461 frente a 4364,0619 m. El beneficio y sus costos se muestran juntos. Estas cifras no pertenecen a Belva. |
| AC06 | Verificado: tres MP4 integrados, etiquetas, informes, posters, reproducción y seek nativos. | [Metadatos y decodificación](../evidence/ui_draft/media-verification.json), pruebas de navegador de los tres videos y del recurso ausente. Sin pista de audio; se ofrece resumen textual, sin subtítulos inventados. `preload="none"`, controles y `playsinline`. |
| AC07 | Verificado: fuentes, límites, licencia y los tres documentos de preparación son accesibles. | Auditoría estática de enlaces y 17 enlaces principales comprobados por HTTP. Manual original con 42 criterios: filtros, persistencia, exportación e importación probados con una clave de almacenamiento aislada. Las notas del usuario no se tocaron. |
| AC08 | Verificado en el recorrido probado: cero errores JS, promesas rechazadas o errores de consola sin gestionar. | JSON de navegador: recursos normales con HTTP 200, `errors`, `rejections`, `consoleErrors` y `cspViolations` vacíos. Casos deliberados de JSON ausente/incompatible y MP4 ausente muestran recuperación explicativa. Sus 404 esperados no son fallos ocultos. |
| AC09 | Parcial: disposiciones 1366×768, 1920×1080 y 390×844 inspeccionadas; foco de teclado comprobado. | Capturas reales y pruebas sin desbordamiento horizontal. Enter sobre objetivo conserva selección/foco. Reflow adicional 910×512 aprobado; equivale solo a una aproximación del ancho al 150 %. Zoom real al 150 % y emulación de `prefers-reduced-motion` pendientes; la regla CSS existe. No se hizo auditoría con lector de pantalla. |
| AC10 | Parcial: subruta, copia portable e independencia de recursos externos verificadas; desconexión real pendiente. | Aplicación servida bajo `/NASA-Sandbox/`, enlaces relativos y navegación hash. El arnés bloquea conexiones externas con CSP `connect-src 'self'`. Esto no acredita una ejecución con Internet desconectado, exigida literalmente por la especificación. Los tres MP4, datos y preparación pertenecen al build; las fuentes externas del archivo requieren red si se abren. |
| AC11 | Verificado dentro del alcance documentado: pilotos, algoritmos, modelos, datos y evidencia científica no se modificaron por el trabajo web. | [Regresiones](../evidence/ui_draft/regression.txt), pruebas de preservación y [checkpoint de originales](../evidence/ui_draft/original-preservation.json). Los seis archivos Jezero previamente modificados y seis archivos replay previamente no versionados permanecen separados. El checkpoint de hashes fue tomado durante el trabajo, no antes; no prueba por sí solo la historia previa. |
| AC12 | Atendido por la alternativa de bloqueo administrativo documentado y artefacto local probado. | [Sitio privado](https://jezero-mission-control-lab.davidyr.chatgpt.site): despliegue confirmado por Sites; la visita sin autenticación redirigió al inicio de sesión de OpenAI. No se afirma acceso anónimo ni validación funcional del contenido alojado. Cambiar la audiencia requiere autorización explícita, según la revisión automática. El ZIP, su prueba independiente y el paso administrativo pendiente están documentados abajo. |

## Entorno y comandos ejecutados

### Verificaciones pendientes para cerrar AC09 y AC10

Estas comprobaciones requieren intervención manual o una herramienta que
permita realizarlas; no están incluidas entre los resultados aprobados.
El paquete local ya está preparado y no necesita publicar el sitio.

1. Descomprimir `web/mission-control-portable.zip` en una carpeta vacía y
   ejecutar `node serve.mjs dist` desde ella. Mantener esa terminal abierta
   y abrir `http://127.0.0.1:4173/NASA-Sandbox/`.
2. Usar el zoom real del navegador al **150 %**, recorrer portada,
   explorador, comparador y videos con teclado, y comprobar que los textos,
   controles y foco siguen visibles y utilizables. Registrar navegador,
   resolución, zoom y una captura; restaurar luego el zoom inicial.
3. Activar la preferencia **movimiento reducido** del sistema o su emulación
   en las herramientas de desarrollo. Recargar la página y comprobar la
   navegación por secciones sin desplazamiento suave, ausencia de
   animaciones decorativas, reproducción inicialmente pausada y controles
   de reproducción utilizables. Registrar cómo se activó la preferencia y
   restaurar después el ajuste original.
4. Con el servidor local abierto, desconectar Internet manualmente cuando
   no interrumpa otro trabajo. Recargar sin caché la URL local; recorrer la
   demo, las capas y el comparador, abrir los tres documentos de preparación
   y reproducir y hacer seek en los tres videos. Los enlaces a fuentes
   externas requieren Internet y no son parte del funcionamiento local.
   Registrar el resultado y restablecer la conexión.

Añadir los resultados reales a este informe antes de cerrar esos criterios.
La autorización de audiencia pública es independiente: AC12 admite el
bloqueo administrativo descrito y no obliga a cambiar la audiencia para
terminar las verificaciones locales.

### Ejecución registrada

- Windows, Node `v24.18.0`.
- Navegador Chromium/Chrome `156.0.0.0`, según el user-agent del arnés.
- FFmpeg y FFprobe `N-125875-g5d4d3bdc61-20260731`.
- Regresiones originales en WSL con Python `3.12.3`.

Desde la raíz del repositorio:

```text
node web/build.mjs
npm --prefix web test
node web/serve.mjs
```

El servidor anuncia `http://127.0.0.1:4173/NASA-Sandbox/`. El arnés local
está en `http://127.0.0.1:4173/__tests__/browser.html`; se ejecuta mediante
su botón y permite descargar el JSON. Ese arnés y su instrumentación no
se copian a `web/dist`.

Las regresiones de solo lectura ejecutadas fueron
`python3 scripts/generate_terrain.py --check` y
`python3 scripts/validate_scene.py`, ambas con salida 0. El descubrimiento
inicial de WSL dentro del sandbox devolvió `Wsl/E_ACCESSDENIED`; las
comprobaciones autorizadas con elevación funcionaron. No fue un rechazo
de la revisión automática. Los comandos y salidas completos están en el
[log de regresión](../evidence/ui_draft/regression.txt).

## Carga y medios

La primera vista útil registrada tardó **434,3 ms**, con **2.406.871 bytes
transferidos** y 2.403.271 bytes decodificados. Es una medición local en el
entorno indicado, incluye la instrumentación del arnés y no es una promesa
de rendimiento de hosting o móvil. Antes de reproducir no se descargó
ningún MP4: la lista incluye código, JSON y tres posters.

| Video integrado | Tamaño original | Duración | Resolución | Seek comprobado |
|---|---:|---:|---|---:|
| Belva, ensayo filmado en lazo cerrado | 346.785 B | 14,733333 s | 1176×600 | 8,103332 s |
| Jezero, reproducción cinemática multivista | 6.315.438 B | 52,2 s | 1920×1080 | 28,71 s |
| Piloto base, integración sintética | 479.846 B | 40,3 s | 1280×720 | 22,165 s |

Los tres son H.264, sin pista de audio. Los 18 MP4 versionados del catálogo
se decodificaron íntegros con FFmpeg sin errores; tres se incluyen en el
build. Los posters son fotogramas extraídos a 7, 18 y 18 s respectivamente,
inspeccionados visualmente. El manifiesto registra hashes, tamaños,
duraciones, origen, clasificación, informes y qué recursos están copiados.
La decodificación no se confundió con reproducción en navegador: ambas
comprobaciones tienen evidencia separada.

## Capturas e inspección

El responsable de la interfaz inspeccionó estas imágenes y corrigió el
mapa para preservar ejes de escala uniforme y la selección con foco.

- [Escritorio 1366×768](../evidence/ui_draft/desktop-1366.jpg).
- [Página completa a ancho 1366](../evidence/ui_draft/desktop-full-1366.jpg).
- [Escritorio 1920×1080](../evidence/ui_draft/desktop-1920.jpg).
- [Descubrimiento a ancho 1366](../evidence/ui_draft/discovery-1366.jpg).
- [Portada móvil 390×844](../evidence/ui_draft/mobile-390.jpg).
- [Explorador móvil](../evidence/ui_draft/mobile-explorer-390.jpg).
- [Mapa móvil](../evidence/ui_draft/mobile-map-390.jpg).
- [Objetivo seleccionado en móvil](../evidence/ui_draft/mobile-target-390.jpg).

Las capturas respaldan una revisión visual y heurística. No acreditan
validación con participantes: no se realizó un estudio de usuarios.

## Integridad y fidelidad

Las fuentes científicas se leen de
`450fa0c57b4073e0d96060a2a28c5c50d6393dd9`; los documentos de preparación
de `87574fc99a11b20870481426e93178bdd87d21a0`. El script usa blobs de Git,
evitando incorporar modificaciones locales previas de la evidencia.
Los originales descargables conservan sus bytes y SHA-256. Los 49 recursos
copiados y el catálogo de 74 entradas se verifican con pruebas de activos.

La inspección del diff original sigue mostrando únicamente cambios previos
de versión Python `3.11.18 → 3.12.3` y `runtime_wall_s` en el resumen y su
copia embebida; el informe solo cambia la versión Python. Eventos,
benchmark y tareas son iguales después de normalizar finales de línea.
El HTML del visor fuera del payload tampoco cambia.

La interfaz mantiene separados los resultados 2.5D, la reproducción por
poses y Belva en lazo cerrado. El video de Belva corresponde a 453,77 s;
las cinco repeticiones posteriores tienen sus propias duraciones y no
fueron filmadas. S2 permanece inaccesible y no se presenta como muestreado.
El enlace principal continúa siendo ideal. No se añadieron restricciones
de conectividad ni capacidades físicas o científicas nuevas.

## Publicación privada y acceso público pendiente

Sites confirmó el despliegue privado satisfactorio en
[jezero-mission-control-lab.davidyr.chatgpt.site](https://jezero-mission-control-lab.davidyr.chatgpt.site).
La versión es
`appgprj_6af369f65b408191866f612b6b3a4e23~appgver_4d0180a631848191b67e1272b2283b15`,
con commit del repositorio fuente de Sites
`0eb551d472d44677ec6687ade7be25b082c3b045`. Este SHA identifica la fuente
publicada en Sites; no sustituye los commits científicos fijados arriba.

La visita del navegador sin autenticación redirigió a `auth.openai.com`,
mostrando la pantalla de acceso; no se introdujeron credenciales. Esto
confirma la barrera de acceso privado, no que la aplicación sea accesible
públicamente ni que el recorrido funcional local se haya repetido tras
esa autenticación.

La revisión automática rechazó el cambio de audiencia a pública porque
interpretó la petición de publicar como autorización insuficiente para
permitir acceso público sin autenticación. Ese rechazo corresponde al
cambio de acceso, no a las pruebas locales. No se cambió la audiencia para
eludirlo. La autorización explícita solicitada al usuario para hacer el
sitio público sigue pendiente; hasta recibirla no puede comprobarse acceso
anónimo al contenido. El sitio publicado mantiene su audiencia privada.

GitHub Pages queda como alternativa preparada en
[pages.yml](../.github/workflows/pages.yml). No se afirma que esté activado.
El procedimiento administrativo pendiente es seleccionar **Settings →
Pages → Source: GitHub Actions**, permitir la rama en el entorno
`github-pages` y ejecutar el workflow manual con `deploy: true`, respetando
las revisiones del repositorio. Después se debe verificar la URL devuelta
por el despliegue en una sesión sin autenticación.

La copia entregada es `web/mission-control-portable.zip`: 8.422.693 bytes,
SHA-256 `340cb86ceae92ad6c7d1e150c1d0f90531cba5268cdcb64cf3eb85a92f443cb3`.
Se extrajo en `web/portable-check`: los 92 archivos estáticos, 10.778.832
bytes, coinciden byte por byte con el build. Se sirvió esa copia desde
`http://127.0.0.1:4174/NASA-Sandbox/` y se verificó la portada, la demo y la
selección con Enter y foco visible, sin errores de consola. El puerto 4174
es una comprobación local temporal, no una URL publicada.
[Evidencia del paquete](../evidence/ui_draft/portable-validation.json).
Las instrucciones están en [web/README.md](../web/README.md).

Commit de implementación: `e953ae49cc89535e3af5c677feefd6b4a40d8499`.
El manifiesto [deployment.json](../evidence/ui_draft/deployment.json) conserva
la confirmación nativa del despliegue privado y su barrera de acceso.
