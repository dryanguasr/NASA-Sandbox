# Piloto Jezero — resultados ejecutados

## Alcance y procedencia

Terreno orbital **real**: recorte de 512 × 512 m centrado en 18.45° N, 77.45° E. MRO/CTX (20 m de información nativa) inicializa el mapa; MRO/HiRISE (postes nativos de 1 m, remuestreados a 4.0 m) actúa como referencia oculta del simulador. Hay 128 × 128 celdas de cálculo.

La misión, los objetivos y los sensores son **hipotéticos**. El simulador revela alturas mediante huellas de observación y ruido controlado; no reconstruye geometría a partir de cámaras. El error se mide respecto al DEM de referencia, no respecto a mediciones de campo. No se ejecutó Gazebo para producir estas métricas.

- Motor: 2.5D mission-level simulation; NOT a Gazebo dynamics run.
- Comunicación: global, instantánea y sin pérdidas.
- Semilla principal: 7.
- SHA-256 de datos: `18d20b39a680d93addc3c3151bb3f19a5f41fc8f9a170396d4094694bbd76d6b`.
- Versiones de ejecución: `{"python": "3.11.18", "numpy": "2.2.6"}`.

## Resultado principal

| Medida | Resultado |
|---|---:|
| Misión completada y seis regresos | True |
| Tiempo simulado total | 1930 s |
| Cobertura por observación local | 100.00 % |
| Error inicial CTX frente a HiRISE | 1.5009 m RMSE |
| Error final del mapa estimado | 0.5256 m RMSE |
| Objetivos ficticios descubiertos | 4 |
| Inspecciones de rovers | 4 |
| Muestreos humanos | 4 |
| Pasos terrestres registrados en celdas no observadas | 0 |

El chequeo de celdas y pendientes NO certifica seguridad física: no modela boulders subpíxel, suelo, contactos ni colisiones entre agentes.

## Trabajo por agente

| Agente | Distancia de la simulación (m) | Tareas terminadas |
|---|---:|---|
| human_1 | 861.2 | sample:S2, sample:S3, return:human_1 |
| human_2 | 650.4 | sample:S1, sample:S4, return:human_2 |
| rover_1 | 828.3 | inspect:S3, return:rover_1 |
| rover_2 | 968.4 | inspect:S2, inspect:S1, inspect:S4, return:rover_2 |
| drone_1 | 2474.3 | survey:3:0, survey:2:1, survey:1:0, survey:0:1, survey:1:2, survey:3:2, survey:5:4, survey:5:5, survey:5:3, survey:4:2, survey:4:1, survey:3:1, survey:0:0, survey:1:3, return:drone_1 |
| drone_2 | 2796.3 | survey:5:2, survey:4:3, survey:3:4, survey:2:3, survey:1:4, survey:0:3, survey:0:5, survey:2:5, survey:4:5, survey:4:4, survey:5:0, survey:4:0, survey:2:0, survey:0:2, survey:2:4, return:drone_2 |


## Comparación pareada

Mismo terreno y objetivos; solo cambia el ruido del sensor entre semillas. No demuestra generalización.

| Política | Ejecuciones completas | Duración media (s) | Tiempo al 80 % (s) | Distancia aérea total (m) |
|---|---:|---:|---:|---:|
| information_hungarian | 3/3 | 1930.0 | 320.0 | 5270.5 |
| nearest_greedy | 3/3 | 1660.0 | 440.0 | 4364.1 |

La política informativa favorece conocer el terreno temprano, pero no necesariamente minimiza la duración total de la misión. Conservar ambos objetivos para la siguiente iteración.

## Cómo se generan las tareas

Los sectores de reconocimiento se proponen a partir del déficit de información del mapa inicial. Solo los sensores pueden revelar objetivos ficticios al entrar en su huella. Una detección crea `inspect`; completar esa tarea con un rover crea `sample`; solo entonces se puede asignar a un humano. La asignación húngara minimiza el costo definido sobre tareas actualmente factibles, con bonificación informativa para reconocimiento. No optimiza globalmente toda la misión ni reproduce íntegramente DisCoverage. Las tareas ya iniciadas se mantienen para evitar oscilaciones.

## Evidencia reproducible

- `viewer.html`: visor autónomo, sin servicios externos, con capas, reproducción y tareas.
- `events.jsonl`, `tasks.json`, `trajectory.jsonl`: trazabilidad temporal.
- `metrics.csv`, `summary.json`, `belief_final.npz`, `belief_frames.npz`: resultados numéricos.
- `benchmark.csv`, `benchmark_summary.json`: comparación con proximidad.
- `generated/jezero/`: exportación de terreno y seis agentes para **reproducción cinemática** en Gazebo; no es validación de control cerrado.

## Límites que deben conservarse

CTX y HiRISE pertenecen a **una sola misión**, MRO. Interpolar CTX a 4 m no crea detalles reales nuevos. La incertidumbre del mapa es un supuesto condicional del modelo y no la precisión oficial de esos productos. No hay límites de comunicación, baterías, soporte vital, biomecánica, aerodinámica, SLAM o reconstrucción fotogramétrica. Los dos humanos son agentes independientes de una misión ficticia; no se certifica ningún protocolo de EVA.

## Fuentes

Fergason et al. (2020), USGS, *Mars 2020 Terrain Relative Navigation HiRISE DTM Mosaic*. DOI: https://doi.org/10.5066/P9REJ9JN

Fergason et al. (2020), USGS, *Mars 2020 Terrain Relative Navigation CTX DTM Mosaic*. DOI: https://doi.org/10.5066/P906QQT8

Catálogos originales: https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/index.html y https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/CTX/index.html
