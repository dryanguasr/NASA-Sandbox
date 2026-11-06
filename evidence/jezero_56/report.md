# Jezero · terreno no convexo y tareas descubiertas

Los cinco escenarios se ejecutaron en Gazebo Harmonic. El video de cada piloto alterna sus variantes con el mapa cenital al centro y seis vistas laterales con cuadrícula de 4 m.

| Piloto y variante | Duración simulada (s) | Cobertura | Inspecciones / muestreos | Regresos |
|---|---:|---:|---:|---:|
| p5/bypass | 614.98 | 100.0% | 1 / 1 | 6 |
| p5/sealed | 157.33 | 100.0% | 0 / 0 | 6 |
| p6/hidden | 420.99 | 100.0% | 4 / 4 | 6 |
| p6/emergent | 382.22 | 100.0% | 4 / 4 | 6 |
| p6/oracle | 418.47 | 100.0% | 4 / 4 | 6 |

## Piloto 5 · cuenca con acceso parcial

El recorte occidental CTX/HiRISE de 128 × 128 m aporta relieve orbital real. Una barrera experimental añadida, que representa un escarpe infranqueable, garantiza la geometría no convexa del tránsito terrestre. La variante abierta deja un corredor al norte. La cerrada extiende la barrera hasta el borde. El dron observa ambos lados en las dos variantes.

Los agentes estiman la transitabilidad con alturas observadas, ocupación, pendiente, desnivel y margen. Los límites experimentales de pendiente son 18° para el rover y 22° para el humano. El planificador conserva la distinción entre un paso todavía sin observar y una desconexión incluso con paso optimista por terreno desconocido.

| Tarea | Agente | Distancia directa (m) | Ruta transitable (m) | Viaje y servicio (s) |
|---|---|---:|---:|---:|
| inspect:S1 | rover_2 | 74.6 | 163.3 | 204.6 |
| sample:S1 | human_2 | 77.0 | 166.8 | 179.0 |

Los cruces terrestres observados en la variante abierta quedaron al norte del extremo de la barrera (y = 22 m). El menor fue y = 29.96 m. En la variante cerrada se clasificó `inspect:S1` como inaccesible y se confirmaron cero cruces terrestres. La distancia directa es una referencia geométrica que atraviesa la barrera.

[Video del piloto 5](piloto_5.mp4).

## Piloto 6 · tareas descubiertas al explorar

Los objetivos son marcadores ficticios. Las variantes oculta y emergente comienzan con el tablero científico vacío. Las cámaras nadir de los drones y las cámaras terrestres simuladas de corto alcance reportan detecciones por pose, tiempo y color. Una observación terrestre requiere al menos 12 píxeles de color y profundidad dentro del alcance de 5,5 m. La confianza es un indicador del detector basado en píxeles y carece de calibración probabilística.

El alero simulado oculta S4 desde arriba. En la variante emergente Gazebo inserta S3 durante la ejecución. La variante oráculo entrega las posiciones al coordinador al inicio para comparar. Una detección abre la inspección y completarla habilita el muestreo. Las detecciones repetidas se consolidan por sitio. El explorador terrestre tiene prioridad en el corredor compartido, así que las inspecciones esperan a que termine su reconocimiento en las tres variantes.

| Variante | Sitio | Observador | Aparición (s) | Detección (s) | Detección a asignación (s) |
|---|---|---|---:|---:|---:|
| hidden | S1 | drone_1 | 0.00 | 8.08 | 78.31 |
| hidden | S2 | drone_2 | 0.00 | 14.12 | 111.41 |
| hidden | S3 | drone_1 | 0.00 | 36.08 | 21.49 |
| hidden | S4 | rover_1 | 0.00 | 27.06 | 30.51 |
| emergent | S1 | drone_1 | 0.00 | 2.65 | 83.79 |
| emergent | S2 | drone_2 | 0.00 | 10.64 | 46.81 |
| emergent | S3 | drone_1 | 24.59 | 31.19 | 79.92 |
| emergent | S4 | rover_1 | 0.00 | 27.19 | 30.26 |
| oracle | S1 | oracle | 0.00 | 0.00 | 86.11 |
| oracle | S2 | oracle | 0.00 | 0.00 | 126.97 |
| oracle | S3 | oracle | 0.00 | 0.00 | 57.41 |
| oracle | S4 | oracle | 0.00 | 0.00 | 57.41 |

La auditoría comprobó una única cadena de inspección y muestreo por sitio, ninguna asignación científica anterior a su detección en las variantes exploratorias y al menos un descubrimiento aéreo y uno terrestre en cada una. Estos ensayos usan enlace ideal y asignaciones con caducidad. La comparación con el oráculo corresponde a una semilla por variante.

[Video del piloto 6](piloto_6.mp4).

## Datos y reproducción

- CTX es el mapa inicial. HiRISE construye el suelo y queda en el simulador y el evaluador. Los resultados incluyen el SHA-256 de cada recorte.
- La barrera, el alero y los marcadores son geometría ficticia del escenario. Profundidad, RGB, navegación y posición observada proceden de Gazebo. Los humanos conservan su movimiento cinemático con orientación hacia el avance.
- En la calibración terrestre se descartaron detecciones adelantadas al acortar el alcance y endurecer el filtro de color. Tras un atasco del explorador, se reservó el corredor y se desplazó el estacionamiento del segundo rover. La variante emergente se repitió por separado tras un fallo de arranque de sensores. Los videos publicados corresponden a los ensayos que superaron la auditoría.

    OPENBLAS_NUM_THREADS=1 /usr/bin/python3 pilots/jezero/run_live_pilots.py 5 6 --jobs 3 --rate 7 --out generated/closed_loop/extensions
    /usr/bin/python3 pilots/jezero/extension_report.py

[Resultados por variante](results.json) · [Telemetría y logs](telemetry.tar.gz) · [Hashes de los videos](video_hashes.json).
