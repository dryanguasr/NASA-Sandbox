# Piloto Jezero: mapas orbitales, tareas emergentes y seis agentes

Este módulo importa **datos reales USGS/MRO**, ejecuta una misión 2.5D reproducible y exporta una reproducción para Gazebo. Conserva intactos el mundo canónico y las evidencias del piloto 0.

## Ejecutar

Desde la raíz del repositorio:

```bash
python3 -m venv .venv-jezero
source .venv-jezero/bin/activate
python -m pip install -r pilots/jezero/requirements.txt
python pilots/jezero/run_all.py
```

El recorte guardado en `data/jezero/terrain.npz` permite repetir sin descargar los mosaicos. Si falta, se importa mediante peticiones parciales HTTP, no se sustituye por terreno sintético. Para repetir la importación explícitamente:

```bash
python pilots/jezero/run_all.py --refresh-data
```

Abrir `evidence/jezero/viewer.html` en el navegador; funciona sin conexión y no necesita servidor. Resultados en `evidence/jezero/report.md`. GitHub Actions ofrece el paquete de evidencia como artefacto descargable (retención de 30 días). El recorte, metadatos y resultados principales también se conservan en Git.

## Qué datos se utilizan

Recorte de **512 × 512 m**, centro **18.45° N, 77.45° E**, Jezero. Proyección métrica local equirectangular sobre la esfera marciana de radio 3 396 190 m; norte arriba. No se utiliza WGS84 terrestre.

| Capa | Fuente | Papel |
|---|---|---|
| Mapa inicial | CTX, mosaico USGS, postes de 20 m | Relieve aproximado disponible al planificador |
| Referencia del simulador | HiRISE, mosaico USGS, postes nativos de 1 m | Referencia reservada para observación simulada y evaluación |
| Retícula de cálculo | Ambas capas alineadas a 4 m | 128 × 128 celdas; interpolar CTX **no** crea detalle de 4 m |

Productos: HiRISE DOI `10.5066/P9REJ9JN`; CTX DOI `10.5066/P906QQT8`. URLs, ventana leída, proyecciones, resolución, versiones y SHA-256 en `data/jezero/metadata.json`. Se exigen datos comunes válidos; la misión no rellena zonas sin datos silenciosamente.

**Ambos instrumentos pertenecen a MRO.** Este laboratorio no pretende cumplir todavía todos los requisitos de un reto que solicite varias misiones. Los modelos orbitales tienen incertidumbre propia; HiRISE no es una verdad física perfecta.

## Misión y asignación

Los drones realizan reconocimiento sobre sectores con información insuficiente. Al observar una ubicación de interés ficticia, se genera una tarea `inspect` para un rover. Su terminación habilita `sample` para un humano. Finalmente, cada agente recibe una tarea individual de regreso.

El asignador húngaro usa tiempo estimado de desplazamiento y servicio; para reconocimiento incorpora una bonificación por reducción esperada de incertidumbre. Las rutas terrestres usan A* con ocho vecinos, sin cortar esquinas, solo sobre celdas localmente observadas y compatibles con el umbral de pendiente. La información se comparte de manera **global, instantánea y sin pérdidas**.

Se conserva una política `nearest_greedy` para comparación. Hay compromiso de tarea para evitar reasignación continua. El algoritmo está **inspirado** en exploración heterogénea; no es una implementación completa de DisCoverage ni una solución óptima de toda la misión.

## Qué está simulado

Los cuatro sitios científicos están **inyectados** en `scenario.json`; no son minerales u objetos detectados en imágenes reales. El planificador no recibe su ubicación hasta que la observación los revela. Los sensores devuelven alturas de la referencia dentro de una huella ideal, con ruido supuesto y localización perfecta; no hay reconstrucción a partir de RGB, SLAM ni oclusión por relieve.

El estimador solo actualiza el área observada. Una observación repetida del mismo nivel no reduce artificialmente la varianza. Un sensor de mejor calidad reemplaza el nivel previo para no tratar mediciones correlacionadas como independientes. La sigma es **condicional al simulador**, no precisión certificada por NASA. Se supone un pequeño reconocimiento previo del hábitat, documentado en la configuración.

Los humanos tienen tareas propias, igual que los dos rovers y drones. Sus velocidades, sensores y umbrales son parámetros hipotéticos. No hay energía, soporte vital, restricciones de conectividad, dinámica de vuelo, biomecánica, mecánica del suelo ni prevención de colisiones entre agentes. Los dos humanos no constituyen un protocolo de EVA validado.

## Gazebo: reproducción, no ejecución de control cerrado

`export_gazebo.py` crea `generated/jezero/jezero_mission.sdf` y modelos portátiles. Utiliza el DEM real, normales OBJ explícitas y los seis nombres del piloto 0. En esta variante los agentes son **estáticos y movidos por poses**: se representa la misión calculada, sin afirmar validación dinámica.

Terminal 1, con Gazebo Harmonic:

```bash
export GZ_PARTITION=jezero_mission
export GZ_SIM_RESOURCE_PATH="$PWD/generated/jezero/models:${GZ_SIM_RESOURCE_PATH:-}"
gz sim -r generated/jezero/jezero_mission.sdf
```

Terminal 2, con los bindings de Gazebo instalados en el Python del sistema:

```bash
export GZ_PARTITION=jezero_mission
/usr/bin/python3 pilots/jezero/replay_gazebo.py --speed 40
```

Requiere `python3-gz-transport13` y `python3-gz-msgs10`. La API empleada está documentada en https://gazebosim.org/api/transport/13/python.html y el servicio `set_pose_vector` en https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1UserCommands.html . Esta integración no se marca como ejecutada hasta disponer de evidencia de Gazebo.

## Ampliaciones posteriores

Primero validar en el equipo local el mundo real y la reproducción. Después sustituir la huella ideal por sensores de Gazebo y cerrar el bucle de movimiento/percepción; mantener separados simulador, estimador y asignador. Añadir terrenos/objetivos alternativos, datos con huecos explícitos y ensayos de mapa desconocido frente a prior orbital. Solo después introducir métricas de energía, riesgo operacional y restricciones de comunicación.

Las reglas de reutilización de material previo y atribución de la competencia deben revisarse antes de copiar este laboratorio al entregable competitivo.
