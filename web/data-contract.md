# Contrato de evidencia web · versión 1

`node scripts/build_web_data.mjs` extrae blobs de Git del commit científico
`450fa0c57b4073e0d96060a2a28c5c50d6393dd9`. No ejecuta los pilotos ni modifica
la evidencia. El wrapper `python scripts/build_web_data.py` delega al mismo
script Node. Se usa la biblioteca estándar; no hay dependencia de NumPy,
Gazebo, red o archivos ignorados. El commit fijado debe existir en el clon
(`fetch-depth: 0` en CI). Una fuente ausente o incompatible detiene el build.

La elección del commit preserva las modificaciones previas del checkout:
no las consume, reemplaza ni atribuye a esta interfaz. La preparación del
10 de noviembre es una incorporación posterior que se empaqueta por separado.

## Archivos

| Archivo en `public/data/` | Contenido y uso |
|---|---|
| `mission.json` | Ejecución `jezero-information-7`, simulación 2.5D, reproducción auténtica de semilla 7. |
| `comparison.json` | Métricas finales de las políticas `information_hungarian` y `nearest_greedy`, semillas 7, 11 y 19. |
| `belva.json` | Resultado del video Belva y, separados, los cinco ensayos de consistencia. |
| `runs.json` | Catálogo que distingue trayectoria, métricas sin trayectoria, video y resumen. |
| `manifest.json` | Ruta, bytes, SHA-256, commit consultado, último commit que modificó cada fuente, escenario, tipo y disponibilidad. |
| `source/` | JSON/CSV/JSONL originales descargables, byte por byte desde Git. |

El registro de video y de informes legibles pertenece al manifiesto de medios,
sin mezclar sus conclusiones con las métricas 2.5D. Los `null` indican ausencia,
no cero ni resultado negativo.

## Tiempo, mapa y entidades

`mission.json` conserva los campos del payload del visor existente:

- `n: 64`, `side: 512`, `trajectory`: 387 estados registrados cada 5 s, desde
  0 hasta 1930 s. Cada estado tiene `time_s`, `positions` y `tasks`; las
  posiciones son `[x_m, y_m, z_m, yaw_rad]`. Los seis IDs son `human_1`,
  `human_2`, `rover_1`, `rover_2`, `drone_1`, `drone_2`.
- `frames`: 98 estados de mapa, cobertura y muestreos, normalmente cada
  20 s, más el estado final. Mostrar el último registro con `time_s <= t`
  y señalar su tiempo. No presentar interpolación visual como medición.
- `prior`, `reference`, `mean[frame]`: base64 de `uint16` little-endian,
  4096 celdas, escala común normalizada 0–65535 del visor original. El visor
  no conservó los extremos métricos: `elevation_min_m` y `elevation_max_m`
  son `null`. No rotular sus valores como alturas en metros. La vista de
  referencia pertenece exclusivamente a evaluación y comienza desactivada.
- `sigma[frame]`: base64 de `uint8`, escala 0–255 equivalente a 0–3 m de
  incertidumbre condicional del simulador. No acredita precisión NASA ni
  seguridad del terreno. La cuadrícula de visualización toma una celda de
  cada dos: 64 × 64, espaciado 8 m; la retícula de cálculo es 128 × 128 a
  4 m. La resolución nativa de CTX sigue siendo 20 m y la de HiRISE 1 m.
- `sites`: marcadores ficticios con `xy_m`, `detected_s`, `detected_by`.
  Filtrar siempre `detected_s <= t`; el listado completo es referencia del
  registro, nunca conocimiento anticipado en la pantalla. `seen_sites`
  solo corresponde al instante muestreado de cada frame.
- `events`: eventos originales sin reordenación, con tiempos, agente,
  tarea y, cuando fue registrado, `score_s`. No hay tabla de candidatos;
  no afirmar que el asignado tenía el menor costo respecto a alternativas.
- `tasks`: estado final original; reconstruir estado temporal mediante
  `created_s`, eventos `assigned/completed` y dependencias. Nunca mostrar
  `state: done` ni `assigned_to` final antes de sus eventos respectivos.
- `milestones`: siete hitos con `event_index` y tiempo comprobable:
  0, 40, 85, 525, 920, 1335 y 1930 s. Sus textos son una explicación de los
  eventos guardados, no nuevas observaciones.

Marco local equirectangular marciano, norte arriba, filas de norte a sur,
centro 18,45° N / 77,45° E, radio esférico 3 396 190 m. Las unidades,
procedencia, hipótesis y resolución están también en `metadata`.

## Separación de adaptadores y comparación

`buildMission()` conserva exclusivamente la simulación 2.5D. `buildBelva()`
exporta ejecución Gazebo en lazo cerrado con `trajectory: null`; no fabrica
posiciones desde imágenes. El registro `jezero-gazebo-replay` solo describe
reproducción cinemática por poses; no hereda validación de lazo cerrado.

La comparación utiliza un mismo terreno y distribución de objetivos, tres
semillas de ruido por política y comunicación global ideal. La cobertura
del 80 % llega a 320 s frente a 440 s, pero la duración total es 1930 s
frente a 1660 s y el recorrido aéreo 5270,5461 m frente a 4364,0619 m.
Todos los valores proceden de `benchmark_summary.json`. La selección de
proximidad abre métricas finales, pues su trayectoria no está versionada.

El resultado Belva de 453,77 s corresponde al video conservado. Sus cinco
repeticiones posteriores no son ese mismo video; aunque las cinco verifican
6/6 regresos, conservan duraciones propias. El objetivo S2 es inaccesible,
no una muestra completada. Humanos y drones siguen siendo cinemáticos.

## Validación

`node --test web/tests/data.test.mjs` comprueba identidad con los blobs
originales, orden temporal, detección no anticipada, precedencia de tareas,
hitos reales, comparación numérica, separación de corridas Belva, rechazo
de datos incompatibles y determinismo de bytes/SHA-256 del exportador.
