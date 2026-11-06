# Pilotos de Jezero en lazo cerrado

Los cuatro pilotos ejecutan Gazebo Harmonic. Se usan mundos generados separados de los pilotos canónico y 2.5D. El controlador publica velocidades y toma decisiones a partir de sensores de la simulación. Los videos capturan cámaras de las ejecuciones.

| Capa | Procedencia y función |
|---|---|
| CTX | Mapa inicial orbital USGS/MRO, resolución nativa de 20 m. |
| HiRISE | DEM orbital USGS/MRO, postes nativos de 1 m. Genera el suelo de Gazebo y lo usa el evaluador. |
| Retícula del piloto | CTX y HiRISE alineados a 4 m en tres recortes de 128 × 128 m. La metadata conserva DOI, URLs, proyección, alturas y SHA-256. |
| Percepción | Imágenes RGB y profundidad de dos cámaras nadir co-localizadas, limitadas por el sensor de Gazebo. El ruido de altura es de 0,10 m por celda con semilla. La segmentación de colores detecta cajas ficticias. |
| Navegación | Rover diferencial con odometría de ruedas, IMU y corrección idealizada de posición cada 2 s con ruido de 0,035 m. Drones y humanos reciben velocidades cinemáticas y usan posición simulada conocida. |
| Evaluación | Poses observadas en Gazebo y DEM orbital de referencia, almacenados por separado de los datos que consume el planificador. |

## Reproducir

Requisitos en Ubuntu 24.04: Gazebo Harmonic, bindings de Gazebo Transport y mensajes 13/10 para el Python del sistema, NumPy, SciPy, Pillow, DejaVu Sans y FFmpeg. El entorno de requisitos de Jezero se usa para importación, auditoría y pruebas. La ejecución registrada usó WSL2 y renderizado Ogre2 por software.

    python3 scripts/generate_terrain.py --check
    python3 scripts/validate_scene.py
    python3 -m venv .venv-jezero
    .venv-jezero/bin/pip install -r pilots/jezero/requirements.txt
    .venv-jezero/bin/python -m pytest pilots/jezero/test_live_mission.py -q
    OPENBLAS_NUM_THREADS=1 /usr/bin/python3 pilots/jezero/run_live_pilots.py --jobs 5 --rate 18 --out generated/closed_loop/final
    .venv-jezero/bin/python pilots/jezero/live_report.py

Los recortes verificados se incluyen en `data/jezero_live/`. Para contrastar el recorte central con las fuentes de USGS, ejecutar el importador con `--side-m 128 --out generated/closed_loop/source_center`. Para contrastar este y oeste, repetir la importación con las coordenadas de los metadatos. El planificador recibe el mapa inicial y observaciones, mientras que el ejecutor carga la referencia para construir el mundo y evaluar los resultados.

Para ejecutar un piloto, añadir su número al comando de matriz. Para ejecutar un único caso:

    /usr/bin/python3 pilots/jezero/live_trial.py --pilot 1 --obstacle --video --out generated/closed_loop/single

Cada ensayo guarda sus estados, eventos, comandos, log de Gazebo y resultado. Los ensayos que agotan los 1.200 s simulados quedan como `timeout`. Las ejecuciones con discrepancias en la comprobación física quedan como `verification_failed`.

El protocolo de comunicación transporta observaciones, estados, asignaciones y confirmaciones. Las asignaciones llevan un token que cambia al reasignarlas. La caducidad local ordena velocidad cero y el coordinador descarta confirmaciones de tokens vencidos. Las interrupciones afectan al canal de misión, mientras que la navegación y el control continúan locales.

[Informe, resultados, videos y telemetría](../../evidence/jezero_live/report.md).

Para el reensayo del este con video y comprobación individual de los seis agentes:

    OPENBLAS_NUM_THREADS=1 /usr/bin/python3 pilots/jezero/live_trial.py --pilot 3 --zone east --layout 1 --seed 7 --policy information_hungarian --rate 18 --video --smoke --out generated/closed_loop/east-retry

El arranque verifica los suscriptores de velocidad y el desplazamiento de los drones. Los humanos giran hacia el siguiente punto antes de avanzar por el eje del visor. [Próximos casos de terreno no convexo y descubrimiento de tareas](NEXT_CASES.md).
