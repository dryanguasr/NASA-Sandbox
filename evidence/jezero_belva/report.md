# Piloto 7 · Cráter Belva en Gazebo Harmonic

[Video con mapa cenital y seis vistas](belva.mp4) · [GIF](belva.gif) · [Métricas por ejecución](result.json) · [Telemetría y mundo SDF](telemetry.tar.gz)

## Resultado

Los drones descubrieron los dos marcadores al explorar. El rover 2 inspeccionó S1 y habilitó su muestreo por el astronauta 1. Los dos agentes llegaron por rodeos distintos. S2 se clasificó como inaccesible para los rovers tras terminar el reconocimiento aéreo, por lo que no se generó su tarea de muestreo. Los seis agentes confirmaron el regreso y recibieron velocidad cero al cerrar la misión.

| Tarea | Distancia directa | Ruta asignada | Celdas excluidas en la recta |
|---|---:|---:|---:|
| Inspección S1 · rover 2 | ≈72 m | ≈113 m | 15 |
| Muestreo S1 · astronauta 1 | ≈71 m | ≈91 m | 7 |

Las distancias de la tabla son horizontales. Las celdas excluidas se calcularon a posteriori con HiRISE y los límites de cada tipo de agente. El [resultado detallado](result.json) separa las distancias planificadas de las observadas y registra las marcas temporales de detección, asignación y finalización.

La ejecución publicada duró **457,05 s simulados**, alcanzó el 80 % de cobertura a los 28,55 s y terminó con el 100 %. El error de elevación frente al DEM HiRISE pasó de 3,79 m a 0,34 m RMSE. La mayor distancia final al punto de partida fue de 0,74 m. En los tramos con movimiento humano medible, el percentil 95 del ángulo entre la orientación y el avance fue de 0,19°.

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

## Diagnóstico y validaciones

- El primer intento se interrumpió a los 18,48 s simulados al dibujar la primera etiqueta descubierta. La capa visual llamaba a un método que no existía en el mapa. Se corrigió para usar la cota estimada de la celda.
- En el segundo intento se detectaron ambos objetivos, pero la ruta a S1 que permitía el filtro preliminar de pendiente quedaba cerrada al aplicar también el filtro de vecindad del planificador. Se detuvo a los 505,09 s simulados, con velocidades cero. El selector definitivo evalúa ambos filtros con margen de pendiente y espacio respecto del borde del recorte.
- Una repetición para depurar la superposición visual volvió a completar el muestreo y cinco retornos. El rover 2 derivó ladera abajo durante el regreso y se detuvo el ensayo a los 579,19 s simulados con velocidad cero para los seis. El retorno por esa ladera sigue siendo sensible a la dinámica del rover. Se publica la primera ejecución completa. [Telemetría de la repetición](repeatability.tar.gz).
- Pasaron las dos validaciones estáticas y 31 pruebas. Se cargó el mundo canónico por separado con `bash scripts/run_gazebo.sh`. La regresión 2.5D se ejecutó por separado con `run_all.py`; sus seis comparaciones completaron cuatro muestras cada una.
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

El MP4 reúne cámaras del servidor Gazebo. El centro muestra las restricciones estimadas para el rover en rojo y las rutas de trabajo en naranja (rover) y verde (astronauta). En la grabación publicada, la línea de ruta incluye un segmento visual que une la pose actual con el primer punto asignado. Las seis cámaras laterales tienen seguimiento isométrico y cuadrícula fija de 4 m en el terreno. El GIF comprime la misma toma. Ambos archivos se decodificaron completos con FFmpeg.
