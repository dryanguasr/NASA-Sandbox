# GOAL para Codex — Mission Control: borrador web interactivo

Estado: encargo de desarrollo; no acredita que la interfaz o su despliegue existan.
Repositorio: `dryanguasr/NASA-Sandbox`.
Base inspeccionada al redactar: `450fa0c57b4073e0d96060a2a28c5c50d6393dd9`.
Preferencia del usuario: **un sitio accesible por enlace, con videos**, más una copia local de respaldo. No limitarse a un video editado, una captura o una página de enlaces.

## Goal breve para activar en un hilo de Codex

```text
/goal Construye en NASA-Sandbox un borrador web atractivo tipo Mission Control siguiendo docs/codex/GOAL_interfaz_web.md y los tres documentos de docs/space_apps_preparacion/. Entrega una demo guiada, exploración temporal del mapa y de los seis agentes, comparación honesta de estrategias, videoteca reproducible y acceso a evidencia. Prioriza un sitio estático publicable en GitHub Pages y conserva ejecución local sin internet. Reutiliza exclusivamente datos y resultados verificables del repositorio, diferenciando simulación 2.5D, reproducción cinemática y ejecuciones Gazebo en lazo cerrado. No modifiques los algoritmos ni los pilotos y no añadas límites de conectividad. Trabaja en una rama independiente, prueba navegación, datos, videos, accesibilidad y subruta de Pages; inspecciona capturas antes de cerrar. Entrega commits, pruebas, capturas, instrucciones y URL comprobada. Si la publicación requiere permisos que no tienes, entrega el build local probado y el procedimiento exacto pendiente, y declara el despliegue bloqueado, no completado.
```

El archivo es la especificación; no activa por sí solo una Goal. En un cliente sin soporte de `/goal`, utilizar su contenido como instrucción normal. El resultado debe ser una primera versión funcional y visualmente cuidada, no solo una propuesta.

## 1. Resultado y límites del encargo

Construir un **explorador de misiones registradas** que permita entender esta cadena: información orbital parcial → reconocimiento robótico → información nueva → tareas emergentes → asignación → resultado y retorno. La interacción debe ayudar a interpretar decisiones, no aparentar capacidades nuevas.

Por defecto, el sitio reproduce ejecuciones existentes. Cambiar de política selecciona una ejecución compatible ya calculada; no presenta ese cambio como una nueva simulación. Dejar un adaptador para integrar un motor en el futuro, sin construir ahora un servidor de Gazebo, autenticación, chatbot, multijugador, baterías o un editor universal de misiones.

Preservar los seis identificadores: `human_1`, `human_2`, `drone_1`, `drone_2`, `rover_1`, `rover_2`. Mantener enlace ideal en los casos principales. Los ensayos históricos con comunicación degradada, si aparecen, solo pertenecen al archivo, con rótulo propio; no ampliar el alcance actual.

Este trabajo es un borrador del laboratorio. No registrarlo como entrega competitiva, no afirmar elegibilidad ni alterar el historial. Revisar las advertencias de trabajo previo del manual; cualquier reutilización en la competencia necesita resolver esa condición con los organizadores. La autorización para desarrollar este borrador no equivale a aprobación de NASA.

## 2. Lectura inicial y auditoría de recursos

Leer `AGENTS.md`, las instrucciones más específicas que existan, `README.md` y los tres documentos de `docs/space_apps_preparacion/`. Luego comprobar el estado actual: los manuales conservan referencias al piloto 2.5D original y **no describen todos los avances posteriores**.

Recursos comprobados al redactar, a volver a inspeccionar antes de utilizar:

| Recurso | Uso previsto |
|---|---|
| `evidence/jezero/viewer.html` y `pilots/jezero/` | Visor y lógica de exportación existentes: reutilizar datos, no simplemente incrustar la página y dar el diseño por terminado. |
| `evidence/jezero/report.md`, `summary.json`, `benchmark.csv`, `benchmark_summary.json`, `events.jsonl`, `tasks.json`, `trajectory.jsonl` | Fuente del caso 2.5D y de la comparación de políticas. Verificar esquemas y existencia en la revisión actual. |
| `data/jezero/metadata.json` y `terrain.npz` | Procedencia y mapas del caso original. |
| `evidence/jezero_belva/report.md`, `result.json`, `seed-comparison.json` | Caso Gazebo con terreno no convexo, objetivo inaccesible y comparación de semillas. |
| `evidence/jezero_belva/belva.mp4` | Video principal candidato; no atribuir sus cifras a la misión 2.5D. |
| `evidence/jezero_replay/jezero_multivista.mp4` | Reproducción visual por poses: rotularla como tal. |
| `evidence/piloto_marciano.mp4` | Piloto de integración sobre terreno sintético. |
| `evidence/jezero_live/report.md`, `evidence/jezero_56/report.md`, `pilots/jezero/LIVE.md` | Contexto de otros ensayos, sus videos y limitaciones. |

Inventariar videos, imágenes, informes y telemetría en un manifiesto. Registrar ruta, tamaño, tipo de experimento, escenario, política, semilla, commit de origen y duración cuando pueda verificarse. Inspeccionar los archivos: un nombre o una miniatura no prueba su contenido. No renombrar archivos fuente ni borrar resultados anteriores.

## 3. Experiencia mínima — cinco áreas conectadas

### A. Portada y demo guiada

Una pantalla con propósito claro, terreno real o fotograma verificado y dos acciones: **Explorar la misión** y **Ver demostración**. Texto candidato: «Del mapa orbital a las decisiones de campo». Una frase explica a quién ayuda y qué decisión permite comprender.

Preparar una ruta guiada de unos 90 segundos, pausada por el usuario o con avance controlado, que salte a hitos registrados: mapa inicial, observación, descubrimiento, inspección, muestreo, resultado y retorno. El orden y los tiempos salen de los eventos. No inventar hitos para completar el guion. Los 90 segundos son un objetivo de diseño, no un límite oficial.

### B. Explorador de misión

Mapa protagonista con norte, escala, leyenda y seis agentes. Capas: conocimiento orbital inicial, estimación disponible en el instante seleccionado e incertidumbre/cobertura cuando esos campos existan. Referencia HiRISE en una vista de evaluación explícita, desactivada inicialmente; nunca modifica el conocimiento del planificador.

Controles: reproducir/pausar, velocidad, búsqueda temporal, siguiente/anterior hito, trayectorias, selección de agente/objetivo y volver a la vista general. Cambiar el tiempo debe actualizar coherentemente tareas, posiciones, métricas y objetivos visibles. Reiniciar limpia selección y temporizadores. No revelar objetivos antes de su detección.

Panel de contexto: qué observación precedió a la tarea, qué agente la ejecuta y qué condición habilitó la siguiente actividad. Solo justificar costos o candidatos cuando están registrados; si faltan, indicar «criterio detallado no registrado». No deducir retrospectivamente una justificación usando información que el asignador no tenía.

P0: integrar al menos una ejecución con reproducción y selección auténticas. Belva puede encabezar la videoteca y el resumen aunque su telemetría requiera una conversión adicional. No inventar posiciones intermedias científicas a partir de su video.

### C. Comparador

Mostrar `information_hungarian` y `nearest_greedy` solo sobre escenarios comparables. Cargar valores desde los resultados, con unidades, número de ejecuciones y condiciones. Presentar el beneficio y el costo: cobertura temprana frente a duración y recorrido. No trasladar los números históricos de Jezero a Belva.

Cuando existan ambas trayectorias, sincronizar el tiempo simulado o identificar explícitamente la comparación de estados finales. Si solo hay métricas de una política, mostrar la comparación numérica sin fabricar su animación. Distinguir claramente selección de una ejecución grabada de recalcular una política.

### D. Videoteca integrada

Reproductor HTML5 con controles, pantalla completa, `playsinline`, poster y carga diferida (`preload="metadata"` o `none`). No descargar todos los videos al abrir el sitio ni reproducir audio automáticamente.

Incluir los tres MP4 identificados arriba si siguen disponibles y se decodifican. Cada tarjeta explica qué demuestra, qué tipo de simulación es y enlaza a su informe. Utilizar capítulos solo con tiempos verificados. Añadir transcripción/resumen accesible y subtítulos WebVTT cuando haya narración; no inventar audio o subtítulos.

Preparar copias web optimizadas fuera de las carpetas originales si hace falta. Conservar la evidencia original. No convertir todos los videos a GIF ni embutirlos como base64. Medir tamaño/duración/códec con FFprobe y verificar reproducción y seek en navegador. Un archivo ausente debe producir una tarjeta explicativa, no un reproductor roto.

### E. Evidencia y preparación

Fuentes por producto, instrumentos y misión, resolución nativa frente a retícula, hipótesis, identificador de ejecución y commit. Descargar resumen JSON/CSV desde la misma fuente usada por la pantalla. Distinguir terreno real, marcadores ficticios, sensores simulados y control realmente ejecutado.

Añadir una sección secundaria de preparación que permita abrir los dos Markdown y utilizar el manual HTML con sus filtros, notas y exportación/importación. Su avance continúa siendo local al navegador; no simular sincronización de equipo. Esta sección no debe ocupar la portada ni confundir la demo con la checklist interna.

## 4. Dirección visual y carácter interactivo

Diseñar una consola de exploración científica, no un tablero genérico de tarjetas. Terreno y trayectorias dominantes, relieve/curvas de nivel legibles, jerarquía tipográfica fuerte, espacio negativo y pocos acentos. Propuesta: fondo carbón/azul muy oscuro, arena/cobre para ambiente marciano, acento cian para observación; ajustar contraste real. Identificar cada clase también por forma y texto, sin usar solo color.

Un momento visual clave debe mostrar **observación → información nueva → tarea → agente asignado**, resaltando la región y la ruta afectadas. Animaciones breves y basadas en eventos, sin partículas decorativas, cifras aleatorias, parpadeos ni cámara que se mueva sola. La velocidad de reproducción y el tiempo de misión siempre visibles.

Tipografía legible, cifras con unidades, máximo tres indicadores protagonistas y detalles a demanda. Modo presentación, foco visible, navegación por teclado, objetivos táctiles cómodos y `prefers-reduced-motion`. Probar escritorio y móvil. Interfaz en español; preparar textos centralizados para una traducción posterior, sin exigir un segundo idioma para cerrar P0.

El terreno 3D o una vista inclinada son P1: añadirlos si ayudan a comprender la geometría y no comprometen el mapa 2D, la carga o la accesibilidad. No introducir otro motor físico. No utilizar imágenes ilustrativas como si fueran resultados de simulación ni presentar la interfaz como un producto oficial de NASA.

## 5. Arquitectura y entrega web

Preferir sitio estático sin cuentas ni backend, publicado en **GitHub Pages**, con build local idéntico. Elegir HTML/CSS/JS o Vite con TypeScript; usar React solo si reduce complejidad. Justificar la elección brevemente. Empaquetar dependencias y evitar CDN necesarios para funcionar. No cambiar de stack reiteradamente.

Organización sugerida, adaptable al repositorio:

```text
web/                       # aplicación, adaptadores y pruebas
scripts/build_web_data.py  # exportación reproducible de evidencia existente
web/public/data/           # registros seleccionados y manifiestos
web/public/media/          # posters y copias web; no duplicar todo el repositorio
web/public/preparacion/    # copias de los tres documentos durante el build
.github/workflows/pages.yml
docs/web_interface_design.md
docs/web_interface_validation.md
evidence/ui_draft/        # capturas y resultados de pruebas, sin archivos enormes
```

Acordar un contrato versionado: `run_id`, escenario, motor/tipo de ejecución, política, semilla, fuentes, unidades, marco, tiempos, agentes, tareas, eventos, métricas y videos. Mantener adaptadores separados para 2.5D, replay y lazo cerrado; no mezclar observaciones de distintas corridas. Normalizar desde archivos inmutables mediante un script reproducible. Cuando un dato no exista, conservar `null`/estado ausente, no inventarlo.

Los estados de interfaz son listo, cargando, reproduciendo, pausado, finalizado, error y recurso no disponible; usar «calculando» solo cuando realmente haya cálculo nuevo. Proteger cambios de ejecución contra respuestas tardías. Sanear textos cargados como datos y no insertar HTML arbitrario. No incluir tokens, datos personales adicionales, analytics ni formularios.

### Publicación

Preparar un workflow de GitHub Pages que compile, pruebe y publique **solo la carpeta de salida seleccionada**, no todo el repositorio. Respetar el sitio existente si lo hubiera y las protecciones de rama. Validar la subruta de proyecto `/NASA-Sandbox/`, recursos relativos, navegación directa y recarga. Usar enlaces con hash o archivos estáticos cuando eviten problemas de rutas.

Copiar los MP4 seleccionados al artefacto de publicación si el tamaño lo permite, con rutas relativas y origen único; no usar páginas `github.com/.../blob/...` como fuentes de `<video>`. Comprobar límites vigentes de Pages y tamaños antes del despliegue. No basar los enlaces públicos en artefactos de Actions que expiran o requieren login. No contratar alojamiento, dominios ni servicios de pago.

Mantener un ZIP/build portable con videos seleccionados y un comando de servidor local, por ejemplo `python3 -m http.server`. Probar ese build con internet desconectado; no prometer apertura mediante `file://` si usa módulos o `fetch`.

Cuando haya permisos y publicación autorizada en el repositorio, desplegar y verificar la URL desde una sesión sin autenticación. Si activar Pages o aprobar el entorno exige al propietario, dejar el workflow y el artefacto probados, documentar la acción administrativa exacta y reportar ese bloqueo. **No afirmar que un sitio está publicado solo porque el build pasó ni inventar una URL activa.**

## 6. Criterios de aceptación verificables

| ID | Condición de cierre | Evidencia mínima |
|---|---|---|
| AC01 | Build limpio y arranque local documentados. | Comandos, versiones y logs. |
| AC02 | Portada explica propósito y abre demo y videos. | Capturas reales y prueba de navegación. |
| AC03 | Seis agentes, capas y reproducción coherente. | Pruebas en instantes registrados; detecciones no anticipadas. |
| AC04 | Pausa, seek, reinicio y cambio de ejecución no mezclan estados. | Pruebas automatizadas y secuencia manual. |
| AC05 | Comparación procede de resultados compatibles y muestra costos. | Prueba que compara números de UI con archivos fuente. |
| AC06 | Videos se reproducen, permiten seek y tienen informe y etiqueta de fidelidad. | Metadatos, prueba de navegador y comprobación de rutas. |
| AC07 | Fuentes, límites y tres documentos de preparación accesibles. | Enlaces verificados; checklist conserva exportación/importación. |
| AC08 | No hay errores JS no gestionados ni recursos esenciales con 404. | Consola y solicitudes de red registradas. |
| AC09 | Vista legible a 1366×768, 1920×1080 y 390×844; teclado y movimiento reducido. | Capturas inspeccionadas y recorrido de teclado. |
| AC10 | Funciona bajo `/NASA-Sandbox/` y en servidor local sin internet. | Pruebas de base path y copia portable. |
| AC11 | Pilotos, datos y evidencia original permanecen intactos. | Diff y regresiones existentes pertinentes. |
| AC12 | Despliegue verificado, o bloqueo administrativo descrito con precisión. | URL y prueba sin login, o artefacto probado y paso pendiente. |

Medir primera vista útil y tamaño descargado antes de reproducir videos; objetivo interno de carga local <5 s en entorno documentado. Un número aislado no sustituye inspección visual. Las pruebas deben cubrir también archivo ausente, datos incompatibles, reproducción al final, doble clic, retorno al inicio, zoom 150 % y tamaño móvil. No exigir pruebas de Gazebo para un cambio exclusivamente de presentación, pero sí ejecutar las regresiones que correspondan al código tocado.

No afirmar validación de usuarios sin participantes reales. Puede documentarse un recorrido heurístico y dejar el ensayo con dos o tres personas como pendiente del equipo.

## 7. Flujo de trabajo, entregables y condición de parada

1. Inspeccionar el checkout actual y registrar el commit; no sobrescribir trabajo ajeno. Crear una rama `ui/mission-control-draft` o una variante libre, sin force-push.
2. Inventariar evidencia, definir dos bocetos de composición mediante HTML/CSS o esquemas locales y elegir uno. Guardar una nota breve de diseño; avanzar a implementación, no quedarse en planificación.
3. Completar una sección vertical: portada → reproducción de una corrida → evento → resultado → fuente. Después añadir comparador, videoteca y preparación.
4. Ejecutar pruebas, inspeccionar capturas con herramientas visuales disponibles y corregir errores funcionales o de composición. Evitar usar solamente snapshots automáticos como criterio estético.
5. Preparar build portable y publicación. Si falla algo, priorizar integridad de datos y recorrido completo antes de efectos opcionales. P1/P2 nunca bloquean P0.
6. Entregar rama/commits o PR, comandos de desarrollo/build/pruebas, capturas, manifiesto de medios, informe de validación y estado de despliegue. No fusionar por la fuerza ni alterar resultados científicos para mejorar la demo.

Cerrar como **borrador local verificado** cuando AC01–AC11 estén demostrados; solo marcar **sitio publicado y verificado** al comprobar la URL. Si falta permiso, herramienta o recurso esencial, reportar intentos, evidencia disponible y bloqueo; no dar toda la Goal por completada. No activar nuevos experimentos largos solo para embellecer la interfaz.

## Referencias operativas

- Goals de Codex: https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex
- GitHub Pages y workflows: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Límites de Pages: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits

Las decisiones de diseño y los criterios AC son requisitos propuestos para este borrador, no normas oficiales de NASA. La documentación de plataforma se debe volver a consultar al implementar.
