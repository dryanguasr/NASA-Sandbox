# Piloto 7 · Cráter Belva en Gazebo Harmonic

[Video con mapa cenital y seis vistas](belva.mp4) · [GIF](belva.gif) · [Métricas por ejecución](result.json) · [Telemetría y mundo SDF](telemetry.tar.gz)

## Resultado

Los drones descubrieron los dos marcadores al explorar. El rover 2 inspeccionó S1 y habilitó su muestreo por el astronauta 1. Los dos agentes llegaron por rodeos distintos. S2 se clasificó como inaccesible para los rovers tras terminar el reconocimiento aéreo, por lo que no se generó su tarea de muestreo. Los seis agentes confirmaron el regreso y recibieron velocidad cero al cerrar la misión.

| Tarea | Distancia directa | Ruta asignada | Celdas excluidas en la recta |
|---|---:|---:|---:|
| Inspección S1 · rover 2 | ≈72 m | ≈113 m | 15 |
| Muestreo S1 · astronauta 1 | ≈71 m | ≈91 m | 7 |

Las distancias de la tabla son horizontales. Las celdas excluidas se calcularon a posteriori con HiRISE y los límites de cada tipo de agente. El [resultado detallado](result.json) separa las distancias planificadas de las observadas y registra las marcas temporales de detección, asignación y finalización.

La ejecución corregida duró **453,77 s simulados**, alcanzó el 80 % de cobertura a los 28,29 s y terminó con el 100 %. El error de elevación frente al DEM HiRISE pasó de 3,79 m a 0,33 m RMSE. En los tramos con movimiento humano medible, el percentil 95 del ángulo entre la orientación y el avance fue de 0,21°.

El rover 2 se aproximó a S1 marcha atrás y quedó orientado a 7,39° respecto del este. Al recibir el regreso, salió en avance y progresó 7,77 m hacia el este en unos diez segundos. En todo el regreso, su separación máxima de la ruta asignada fue de 0,65 m, medida sobre poses registradas aproximadamente una vez por segundo. Cada regreso se verificó con un evento de finalización y su pose de Gazebo.

| Agente | Retorno confirmado (s simulados) | Distancia al punto de partida (m) |
|---|---:|---:|
| Rover 1 | 306,55 | 0,15 |
| Rover 2 | 452,52 | 0,88 |
| Astronauta 1 | 402,95 | 0,66 |
| Astronauta 2 | 308,60 | 0,25 |
| Dron 1 | 317,50 | 0,67 |
| Dron 2 | 326,13 | 0,68 |

## Relieve y datos

El escenario cubre 128 × 128 m en Belva, con centro en **18.48380349° N, 77.38555753° E**. Se buscaron sectores de terreno con un trayecto directo que cruzara pendientes o saltos de cota por encima del límite terrestre, y con un rodeo dentro del recorte. El análisis de selección fue previo a la misión. [Ficha de Belva en el nomenclátor USGS/IAU](https://planetarynames.wr.usgs.gov/Feature/15872).

| Tipo | Uso |
|---|---|
| Datos orbitales reales | HiRISE de MRO (1 m nativo) aporta las cotas de la única malla de relieve, a 4 m y sin exageración vertical. CTX de MRO (20 m nativo) inicializa el mapa aproximado del planificador en la misma cuadrícula. |
| Observaciones y control simulados | Gazebo proporciona RGB y profundidad nadir para descubrir marcadores y actualizar cotas, además de odometría de ruedas y poses simuladas. Los rovers reciben comandos diferenciales. Los drones y astronautas reciben velocidades cinemáticas. Los astronautas giran hacia la dirección de avance. |
| Elementos ficticios de escenario | Dos marcadores visuales sin colisión. Están físicamente presentes desde el inicio, pero cada tarea de inspección nace al detectar su marcador. Una inspección completada habilita el muestreo correspondiente. El enlace es ideal. |
| Métricas derivadas | El error de mapa es relativo al DEM orbital. El acceso terrestre se estima mediante pendiente y salto de cota sobre celdas observadas, con límites de 18° para el rover y 22° para el astronauta. Son umbrales del experimento. |

[HiRISE DTM, Fergason et al., USGS](https://doi.org/10.5066/P9REJ9JN) · [CTX DTM, Fergason et al., USGS](https://doi.org/10.5066/P906QQT8) · [Metadatos y SHA-256](../../data/jezero_live/belva/metadata.json).

La proyección es equirectangular marciana local, con longitud este, latitud planetocéntrica, radio de 3.396.190 m y filas de norte a sur. El recorte exige cobertura conjunta completa. Las cotas siguen la referencia MOLA/DeltaGeoid de origen. El planificador recibe el mapa inicial CTX, observaciones simuladas y estados de navegación. El DEM HiRISE de referencia se usa en la geometría y en la evaluación.

El relieve abarca **32,78 m** (−2479,03 a −2446,25 m), con una pendiente máxima de **32,28°** sobre la cuadrícula de 4 m. Las matrices empaquetadas coinciden celda a celda con sus GeoTIFF. SHA-256 del recorte publicado:

```text
12a8118fcbcbb588a6453ce78d1e010fd323fa426d51a77f6c2316d2913d27f9
```

## Desvío del rover 2 y corrección

En el ensayo fallido, a los 301,83 s simulados el rover recibió una ruta cuyo primer tramo útil iba de (−18, 18) a (−14, 18), hacia el este y cuesta arriba. Estaba junto a S1 en (−17,59, 18,11), con rumbo −173°. La pendiente de la celda de S1 en el DEM es de 11,15°. El controlador solo permitía avance frontal, por lo que intentó girar casi media vuelta sobre la ladera antes de avanzar. Después de la primera alineación, el rumbo osciló entre ambos lados del este. A los 307,08 s la posición de navegación discrepaba 0,86 m de la pose observada, más que la tolerancia de 0,70 m para dar un punto por alcanzado. El rover terminó a 41,78 m de la ruta asignada y perdió 9,09 m de cota. [Telemetría del desvío](repeatability.tar.gz).

El ensayo anterior completó el regreso por ese mismo primer tramo. La secuencia del fallo indica que el giro en pendiente y el error de posición durante la maniobra desestabilizaron el seguimiento local. La ruta seguía apuntando hacia el este y la telemetría anterior no incluía fuerzas de contacto, así que no se puede aislar cuánto contribuyó el deslizamiento de cada rueda.

La primera corrección permitió avanzar o retroceder con la orientación más cercana y conservó esa elección hasta alcanzar el punto de paso. El rover superó la salida de S1, pero perdió seguimiento más adelante, cerca de (46, 14), con el punto (54, 10) aún pendiente. El ensayo se detuvo a los 589,29 s con cinco regresos y el rover a 6,85 m de la ruta asignada. [Telemetría de la corrección intermedia](bidirectional-only.tar.gz).

La segunda corrección mantuvo la marcha bidireccional y suavizó el seguimiento. Limitó el giro a 0,65 rad/s, aumentó gradualmente la velocidad longitudinal a medida que se alineaban las ruedas y redujo el paso de integración física de Gazebo de 10 a 2,5 ms en Belva. Se mantuvieron el modelo diferencial, la odometría y la parada por datos caducados. La telemetría nueva registra el punto activo y el sentido seleccionado. El recorte, los marcadores y el planificador A* son los mismos. Los cambios de seguimiento y paso físico se probaron juntos. [Configuración física de Gazebo](https://github.com/gazebosim/gz-sim/blob/main/tutorials/physics.md).

## Validaciones

- El primer intento se interrumpió a los 18,48 s simulados al dibujar la primera etiqueta descubierta. La capa visual llamaba a un método que no existía en el mapa. Se corrigió para usar la cota estimada de la celda.
- En el segundo intento se detectaron ambos objetivos, pero la ruta a S1 que permitía el filtro preliminar de pendiente quedaba cerrada al aplicar también el filtro de vecindad del planificador. Se detuvo a los 505,09 s simulados, con velocidades cero. El selector definitivo evalúa ambos filtros con margen de pendiente y espacio respecto del borde del recorte.
- El ensayo del desvío se detuvo a los 579,19 s simulados con velocidad cero para los seis agentes. Había completado el muestreo y cinco retornos.
- Pasaron las dos validaciones estáticas y 34 pruebas de regresión. Se cargó por separado el mundo canónico con `bash scripts/run_gazebo.sh`. En la validación inicial de Belva se ejecutó también la regresión 2.5D con `run_all.py`, cuyas seis comparaciones completaron cuatro muestras cada una.
- Entorno de ejecución: Ubuntu 24.04 en WSL2, Gazebo Sim 8.14.0 (Harmonic), Python 3.12.3 y FFmpeg 6.1.1. GPU del equipo: NVIDIA GeForce RTX 4050 Laptop, controlador 610.62.

## Reproducción

Usar Gazebo Harmonic, los bindings de Gazebo Transport de la [guía de ejecución](../../pilots/jezero/LIVE.md) y FFmpeg. Se incluye el recorte verificado para ejecutar sin descargar los mosaicos.

```bash
python3 scripts/generate_terrain.py --check
python3 scripts/validate_scene.py
OPENBLAS_NUM_THREADS=1 python3 pilots/jezero/live_trial.py --pilot 7 --zone belva \
  --seed 7 --policy information_hungarian --link ideal --smoke --video --rate 7 \
  --out generated/closed_loop/belva-run
python3 pilots/jezero/belva_report.py generated/closed_loop/belva-run evidence/jezero_belva
```

Para repetir la selección orbital, preparar la venv de la [guía Jezero](../../pilots/jezero/README.md), importar el recorte de búsqueda, ejecutar el selector y volver a importar el centro seleccionado.

```bash
.venv-jezero/bin/python pilots/jezero/import_data.py --lat 18.478 --lon 77.382 \
  --side-m 1200 --out generated/closed_loop/belva-search
.venv-jezero/bin/python pilots/jezero/select_belva.py generated/closed_loop/belva-search \
  generated/closed_loop/belva-selection.json
.venv-jezero/bin/python pilots/jezero/import_data.py --lat 18.483803488071192 \
  --lon 77.38555752781869 --side-m 128 --out generated/closed_loop/belva-source
```

El MP4 reúne cámaras del servidor Gazebo. El centro muestra las restricciones estimadas para el rover en rojo y las rutas de trabajo en naranja (rover) y verde (astronauta). Las seis cámaras laterales tienen seguimiento isométrico y cuadrícula fija de 4 m en el terreno. El GIF comprime la misma toma. Ambos archivos se decodificaron completos con FFmpeg.

## Comparativo de semillas

Se repitió el piloto corregido en Gazebo Harmonic con las semillas **7, 11, 19, 23 y 31**. La semilla cambia el ruido de las mediciones de elevación y de las correcciones de posición de los rovers. Se mantuvieron el mismo recorte HiRISE, los mismos marcadores y bases, el enlace ideal y el controlador corregido. Se ejecutó sin cámaras de grabación, con un límite de 1.200 s simulados por semilla y dos grupos de procesos en particiones independientes de Gazebo Transport. El video de la ejecución anterior sigue disponible arriba.

**Los seis agentes regresaron en 5 de 5 misiones.** Hubo **0 fallos y 0 agotamientos del límite**. Las cinco ejecuciones pasaron las seis pruebas individuales de movimiento, alcanzaron el 100 % de cobertura y enviaron velocidad cero a los seis agentes al finalizar.

| Semilla | Estado | Regresos verificados | Duración simulada (s) | Mayor error final a base (m) | Máximo desvío del rover en el regreso (m) |
|---|---|---:|---:|---:|---:|
| 7 | Completa | 6/6 | 450,71 | 0,76 | 0,48 |
| 11 | Completa | 6/6 | 450,72 | 0,79 | 0,42 |
| 19 | Completa | 6/6 | 464,45 | 0,68 | 0,48 |
| 23 | Completa | 6/6 | 450,94 | 0,87 | 0,45 |
| 31 | Completa | 6/6 | 421,87 | 0,84 | 0,45 |

En la semilla 19 el rover 2 salió de S1 con rumbo −175,65°, próximo al del fallo original. Completó el regreso con 146 muestras de telemetría en marcha atrás y una separación máxima de 0,48 m de la ruta asignada. Las otras cuatro semillas llegaron a S1 con el rover orientado hacia el este y regresaron en avance. En todas se inspeccionó y muestreó S1 y se declaró S2 inaccesible por tierra. El identificador `inspect:S2` queda en la lista de tareas no completadas con estado `inaccessible`.

La consistencia observada corresponde a estas cinco semillas, este terreno y esta configuración. La variación de semillas evalúa los ruidos simulados de percepción y posicionamiento. El orden temporal de los mensajes también depende de la ejecución concurrente. El informe conserva aparte los fallos de desarrollo anteriores.

Para verificar un regreso se exigió un evento de finalización con pose observada a 2 m o menos de la base individual y una pose final dentro de ese mismo radio. Se registró por separado el estado de la misión y el envío de velocidad cero. El desvío del rover que inspeccionó S1 se calculó a partir de poses muestreadas aproximadamente una vez por segundo respecto de su ruta de regreso asignada.

[Métricas por semilla y agente](seed-comparison.json) · [Telemetría, consola y validaciones](seed-telemetry.tar.gz).

```bash
export OPENBLAS_NUM_THREADS=1
out=generated/closed_loop/belva-seeds
mkdir -p "$out"
run_seed() {
  local seed="$1" code=0
  python3 pilots/jezero/live_trial.py --pilot 7 --zone belva --seed "$seed" \
    --policy information_hungarian --link ideal --smoke --rate 7 --max-time 1200 \
    --out "$out/seed-$seed" > "$out/seed-$seed.console.log" 2>&1 || code=$?
  printf '%s\n' "$code" > "$out/seed-$seed.exit"
}
run_seed 7 & p7=$!
run_seed 11 & p11=$!
wait "$p7" "$p11"
run_seed 19 & p19=$!
run_seed 23 & p23=$!
run_seed 31 & p31=$!
wait "$p19" "$p23" "$p31"
python3 pilots/jezero/belva_compare.py "$out" evidence/jezero_belva 7 11 19 23 31
```
