# Procedencia y fidelidad

El terreno es **sintético**: dos cráteres, crestas y pequeñas variaciones
deterministas. `scripts/generate_terrain.py` produce una malla OBJ y una
tabla CSV desde la misma fórmula, 31×31 puntos en [-45,45] m, paso 3 m.

Las coordenadas son locales `LOCAL_ENU_SYNTHETIC`. No hay proyección
planetaria, DEM/DTM NASA, radiación, suelo granular, meteorología o rutas
seguras verificadas. Los sitios científicos son marcadores ficticios.
Los drones emplean velocidades impuestas, sin dinámica de rotores; los
humanos no tienen biomecánica.

Para datos reales, un piloto posterior debe:

1. Elegir región y DEM MRO/HiRISE, MOLA u otra fuente apropiada.
2. Registrar identificador, URL, datum, proyección, escala, resolución,
   no-data y condiciones de uso.
3. Transformar a un marco local y generar OBJ + CSV desde el mismo raster.
4. Verificar orientación, unidades, alturas, poses, incertidumbres y
   alineación con imágenes/capas científicas.

Fuentes por explorar:
[NASA PDS](https://pds.nasa.gov/),
[HiRISE](https://hirise.lpl.arizona.edu/) y
[PDS Geosciences](https://pds-geosciences.wustl.edu/).

No atribuir a NASA el terreno procedimental entregado.
