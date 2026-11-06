# Jezero en lazo cerrado

Los ensayos se ejecutan en Gazebo Harmonic con renderizado Ogre2 por software. El archivo de telemetría incluye los logs de arranque, pruebas, versiones y GPU cuando están disponibles.

| Tipo de dato | Uso |
|---|---|
| Real · CTX USGS/MRO | Mapa inicial aproximado. Información nativa de 20 m remuestreada a 4 m. |
| Real · HiRISE USGS/MRO | Geometría y colisión de Gazebo, y referencia del evaluador. Postes nativos de 1 m remuestreados a 4 m. El planificador usa CTX y mediciones locales. |
| Simulado · percepción | Profundidad y RGB de Gazebo con alcance, huella y oclusión. Las alturas reciben ruido por celda y semilla. |
| Simulado · navegación | Rover con odometría de ruedas e IMU y corrección local idealizada cada 2 s a partir de la pose simulada con ruido de 0,035 m. Drones y humanos reciben comandos cinemáticos y usan pose simulada conocida. |
| Ficticio · escenario | Objetivos representados por marcadores de color, obstáculo y condiciones de comunicación. |
| Derivado · evaluación | Cobertura, distancia, llegada y error frente al DEM orbital. Las poses observadas por el evaluador se registran separadas de la navegación. |

La calibración con ruedas e IMU acumuló error. También se observó pérdida de tracción con dos apoyos pasivos. La versión final del rover usa dos ruedas motrices, un apoyo pasivo trasero y correcciones locales idealizadas. La marcha humana y el vuelo siguen siendo aproximaciones cinemáticas.

## Resultados

| Piloto | Casos previstos | Completos y verificados | Otros estados | Video |
|---|---:|---:|---|---|
| 1 | 3 | 3 | — | [Video](videos/piloto_1.mp4) |
| 2 | 1 | 1 | — | [Video](videos/piloto_2.mp4) |
| 3 | 24 | 23 | timeout × 1 | [Video](videos/piloto_3.mp4) |
| 4 | 8 | 8 | — | [Video](videos/piloto_4.mp4) |

### Casos sin completar

- `p3/east-1-7-information_hungarian` · timeout. Tareas pendientes: survey:-46:18.

Este caso se repitió por separado con verificación del canal de velocidad y giro de los humanos hacia su avance. La tabla anterior conserva la matriz original. [Diagnóstico, resultado y video del reensayo](east_retry.md).

### Percepción y misión nominal

- **clear** · complete. error de llegada 0.59 m.
- **obstacle** · complete. error de llegada 0.71 m, distancia del centro del rover al borde del obstáculo 9.44 m, latencia de replanteo 0.41 s, contactos 0.
- **odom-outage** · complete. error de llegada 0.56 m, distancia del centro del rover al borde del obstáculo 9.44 m, latencia de replanteo 0.13 s, deriva durante pérdida de odometría 0.09 m, contactos 0.
- **Misión nominal** · complete. Detecciones 4/4, inspecciones 4/4, muestreos 4/4, regresos 6/6.

### Comparación de terrenos

| Zona | Política | Completas | Llegaron al 80 % | Mediana t80 (s) | Duración mediana de éxitos (s) | Cobertura final mediana (%) |
|---|---|---:|---:|---:|---:|---:|
| center | information_hungarian | 4/4 | 4 | 35.64 | 383.07 | 100.00 |
| center | nearest_greedy | 4/4 | 4 | 47.01 | 366.14 | 100.00 |
| east | information_hungarian | 3/4 | 4 | 41.62 | 386.75 | 100.00 |
| east | nearest_greedy | 4/4 | 4 | 54.58 | 376.59 | 100.00 |
| west | information_hungarian | 4/4 | 4 | 39.42 | 469.14 | 100.00 |
| west | nearest_greedy | 4/4 | 4 | 49.05 | 433.09 | 100.00 |

Mediana de proximidad menos política informativa en pares medibles. Tiempo hasta el 80 %: **10.77 s** (12 pares). Duración total: **-31.22 s** (11 pares completos).

### Comunicaciones

| Modo | Completas | Reasignaciones a otro agente | Confirmaciones rechazadas | Recuperación mediana (s) | Duración mediana de éxitos (s) |
|---|---:|---:|---:|---:|---:|
| ideal | 2/2 | 0 | 0 | — | 389.22 |
| delay | 2/2 | 0 | 58 | — | 470.17 |
| loss | 2/2 | 0 | 6 | — | 389.99 |
| cut | 2/2 | 0 | 0 | 0.25 | 417.08 |

Una reasignación puede repetir trabajo parcial. La telemetría distingue reasignaciones, confirmaciones rechazadas y tareas duplicadas aceptadas. La latencia de recuperación se mide desde el fin del corte hasta el primer estado recibido.

### Procedencia de los recortes

| Zona | Centro lat/lon (°) | Pendiente media / máxima (°) | GeoTIFF verificados |
|---|---|---|---:|
| center | 18.45000, 77.45000 | 2.85 / 13.14 | 2 |
| east | 18.45000, 77.46000 | 1.44 / 6.01 | 2 |
| west | 18.45000, 77.44000 | 4.85 / 15.39 | 2 |

Cada zona tiene 128 × 128 m a 4 m por celda. Los centros ejecutados están separados más que el ancho de cada recorte. La auditoría conserva hashes y la comprobación de escala, orientación, cotas y normales.

[Reproducción](../../pilots/jezero/LIVE.md) · [CSV por ensayo](trials.csv) · [Matriz completa](matrix.json) · [Auditoría de terreno](terrain_audit.json) · [Telemetría y logs](telemetry.tar.gz).
