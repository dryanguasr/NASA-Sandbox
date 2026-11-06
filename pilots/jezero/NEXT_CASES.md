# Próximos casos de Jezero

[Ejecución, comparación y videos de los dos casos](../../evidence/jezero_56/report.md).

La referencia metodológica es la tesis de David Reinerio Yanguas Rojas (2018), que combina exploración de espacios no convexos, heterogeneidad de los agentes y asignación de tareas por eventos. Los siguientes casos trasladan esas ideas a Jezero con el planificador y los sensores del repositorio. [Registro institucional de la tesis](https://repositorio.unal.edu.co/handle/unal/68687).

## Piloto 5 — Cuenca con acceso terrestre parcial

- Seleccionar un recorte HiRISE con una pared de cráter, valle o escarpe. Conservar CTX como mapa inicial y usar HiRISE para construir el terreno y evaluar la travesía. Validar que el DEM tiene cobertura y resolución suficientes para resolver el paso y el borde. Registrar recorte, fuente, resolución y SHA-256.
- Construir una máscara distinta para rover y humano con pendiente, desnivel local y margen de seguridad, a partir del mapa estimado. Usar los umbrales como parámetros del experimento. La topografía de referencia queda en el simulador y en el evaluador.
- Preparar dos condiciones de acceso. En una, el segmento directo entre base y objetivo atraviesa terreno prohibido, pero hay un corredor rodeando la cuenca. En la otra, el objetivo queda en una componente terrestre desconectada y sigue siendo observable desde el aire. Si cerrar el corredor exige una barrera añadida, etiquetarla como elemento ficticio.
- Comparar rutas por distancia euclidiana y por tiempo de viaje sobre el mapa transitable, conservando los mismos controladores y límites. El dron puede observar ambos lados. Los agentes terrestres rodean la cuenca cuando existe un camino y dejan la tarea pendiente por inaccesibilidad cuando el mapa observado confirma que no hay paso. Mantener «acceso desconocido» como estado distinto mientras falten observaciones.
- Medir longitud del rodeo, tiempo de llegada, incursiones en celdas prohibidas y errores al clasificar accesibilidad. La aceptación requiere un rodeo verificado en el primer caso y que ningún rover ni humano cruce la barrera del segundo.

## Piloto 6 — Tareas que aparecen al explorar

- Iniciar con el mapa CTX y el tablero de ciencia vacío. Los agentes reciben tareas de exploración en fronteras del mapa estimado. Solo el simulador conoce los marcadores ficticios. Los drones llevan RGB y profundidad; añadir cámaras de corto alcance a rover y humano para permitir descubrimientos propios, incluso bajo un borde que oculte el marcador a la ruta aérea.
- Separar dos condiciones con igual terreno y objetivos. En la primera, todos los marcadores ya existen en el mundo, ocultos al coordinador hasta que un sensor los observe. En la segunda, activar uno o más marcadores durante la misión mediante un evento del entorno, sin publicar su ubicación. Distinguir el instante de aparición en el mundo del instante de detección.
- Publicar cada observación con pose, instante, clase y confianza. Consolidar observaciones repetidas en un mismo sitio. Una detección abre una inspección, una inspección confirmada habilita un muestreo y un cambio de accesibilidad puede bloquear o reabrir una tarea. Reasignar por evento cuando un agente disponible pueda llegar en menos tiempo o cuando venza la asignación vigente.
- Comparar con una variante que conozca los objetivos desde el inicio como referencia de desempeño. Medir tiempo de aparición a detección, detección a asignación, porcentaje de sitios atendidos, duplicados, reasignaciones y cobertura. La aceptación requiere un descubrimiento aéreo y uno terrestre, ninguna asignación científica anterior a su detección y una única cadena de tareas por sitio.
