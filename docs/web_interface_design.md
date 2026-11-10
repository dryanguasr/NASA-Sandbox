# Diseño del borrador Mission Control

## Decisión y alcance

El borrador ayuda a un visitante a entender cómo una observación habilita
una tarea y qué compromisos muestran dos estrategias registradas. La
secuencia es portada → misión reproducible → evento → resultado → fuente.
Es una interfaz de interpretación de resultados, sin motor nuevo.

Los dos bocetos locales están en [design-sketches.html](../web/design-sketches.html):

1. **Terreno protagonista**, elegido: propósito y dos acciones claras,
   mapa grande, detalle contextual y línea temporal. Funciona como entrada
   para una demostración y se apila con continuidad en móvil.
2. **Consola analítica**: tres indicadores arriba, controles persistentes
   a la izquierda, mapa y tabla de eventos. Adecuado para consulta experta,
   pero la densidad inicial compite con la explicación de la misión.

Las formas SVG de los bocetos son esquemas de composición rotulados, no
imágenes del terreno. La aplicación usa mapas y fotogramas de evidencia.

## Gramática visual

Fondo carbón/azul, arena/cobre para ambiente y acción principal, cian para
observación. La jerarquía distingue propósito, mapa, estado temporal y
detalle técnico. Humanos, rovers y drones tienen formas y etiquetas
distintas; el color nunca es su único identificador. No hay animación
decorativa, parpadeo, audio automático ni cámara que se desplace sola.

La reproducción avanza únicamente por una acción del usuario. El tiempo,
la velocidad y el estado son visibles; hay pausa, reinicio, hitos y
regreso a vista general. Se respetan movimiento reducido, foco visible,
teclado y disposición móvil. Los detalles numéricos se ofrecen a demanda.
Las inspecciones visuales finales se registran en el informe de validación.

## Fidelidad y relato

La demo usa siete hitos comprobables del registro 2.5D, unidos por una
ruta con avance controlado. Los 90 segundos orientan al presentador y no
constituyen una regla oficial. No se anticipa un objetivo ni el estado
final de una tarea. Los costos registrados se pueden consultar; los
candidatos ausentes no se reconstruyen retrospectivamente.

La videoteca destaca Belva como avance de Gazebo en lazo cerrado, con seis
regresos y un objetivo inaccesible. La reproducción multivista por poses
conserva la etiqueta cinemática. El piloto base usa suelo sintético.
Estas tres clases de evidencia no comparten automáticamente métricas.

La comparación mantiene escenario, objetivos y conexión ideal. Muestra
beneficio y costo de la política informativa: cobertura temprana más rápida,
mayor duración y recorrido aéreo. Proximidad tiene métricas finales;
su trayectoria ignorada por Git no se incorpora al build reproducible.

El manual y las checklist quedan como sección secundaria. Su avance vive
en el navegador, con exportación/importación y sin supuesta sincronización
de equipo. Se conserva la advertencia sobre trabajo previo: el borrador
del laboratorio no acredita elegibilidad competitiva ni aprobación NASA.

## Arquitectura

HTML, CSS y módulos JavaScript nativos, Canvas para el mapa y Node para
extraer/copiar recursos. Este alcance no necesita un framework ni backend.
No hay dependencias CDN, cuentas propias, analítica ni formularios.
Los textos de interfaz se centralizan para facilitar una traducción futura.

[Contrato versionado](../web/data-contract.md): los adaptadores de 2.5D,
reproducción cinemática y lazo cerrado preservan su origen. La exportación
lee blobs del commit científico fijado; los originales y cambios previos
del checkout permanecen intactos. Los JSON/CSV descargables y las cifras
de pantalla proceden de la misma evidencia. Los campos ausentes son `null`.

La cuadrícula visual reutilizada es 64 × 64 a 8 m; deriva de la retícula
de cálculo de 4 m. CTX sigue teniendo postes nativos de 20 m y HiRISE de
1 m. Los extremos métricos no se conservaron en el visor exportado:
la elevación de esta capa es normalizada, con escala común; no se inventa
una barra de alturas métricas. La incertidumbre condicional sí conserva
la escala de 0–3 m.

## Publicación y respaldo

Sites es el destino primario solicitado en este encargo. Su identidad se
conserva en `web/.openai/hosting.json`; el artefacto servido es `web/dist`.
Una creación de Site o un build no acreditan publicación: el informe final
debe identificar URL y resultado del despliegue o su bloqueo concreto.

GitHub Pages queda como alternativa preparada. El workflow
[pages.yml](../.github/workflows/pages.yml) construye y prueba en PR, y solo
despliega por `workflow_dispatch` con `deploy: true`. Respeta el entorno
protegido `github-pages`; no activa Pages, cambia audiencias ni publica
automáticamente al subir esta rama. Solo carga `web/dist`, nunca el repo.
Las rutas relativas y navegación hash permiten `/NASA-Sandbox/`.

Para la alternativa Pages, el administrador debe seleccionar **Settings →
Pages → Source: GitHub Actions**, permitir la rama en el entorno
`github-pages` y ejecutar el workflow manual con despliegue habilitado.
Solo después de un resultado satisfactorio se debe comprobar la URL que
devuelva `deploy-pages` en una sesión sin autenticación. Si el workflow
aún no aparece en la pestaña Actions, debe incorporarse mediante revisión
a la rama predeterminada, o ejecutarse por la API sobre una referencia
permitida. No se ha afirmado que estos pasos administrativos estén hechos.

Según la documentación consultada el 10 de noviembre de 2026, el sitio
publicado de Pages tiene un máximo de 1 GB; el workflow comprueba un
límite conservador de 1.000.000.000 bytes. El despliegue necesita
`pages: write`, `id-token: write` y el entorno de protección. [Límites de
Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits),
[workflow oficial](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

El mismo build conserva los tres videos seleccionados, posters, informes,
datos y preparación para servirlo localmente sin red. Un servidor HTTP
local es necesario para módulos y `fetch`; no se promete `file://`.
