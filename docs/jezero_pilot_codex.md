# Instrucciones de continuación: piloto Jezero

Trabaja en `dryanguasr/NASA-Sandbox`. Lee `AGENTS.md`, `pilots/jezero/README.md` y el reporte de resultados. No modifiques el mundo canónico ni las evidencias del piloto 0.

1. Actualiza el repositorio y verifica el SHA-256 del recorte mediante `mission.load_data`. Ejecuta `python pilots/jezero/run_all.py` dentro del entorno con los requisitos del módulo. Conserva los datos reales y no los reemplaces por datos sintéticos si falla la red.
2. Audita el reporte, los eventos y el visor. Comprueba los seis agentes, las cuatro inspecciones, cuatro muestreos y seis regresos. Revisa especialmente que `sample` se habilite después de `inspect` y que el planificador no lea directamente la referencia HiRISE.
3. Carga `generated/jezero/jezero_mission.sdf` con los recursos locales y ejecuta `replay_gazebo.py` en la misma partición de transporte. Graba evidencia de visualización. Esta etapa es reproducción cinemática, no control cerrado: no alteres esa etiqueta.
4. Antes de extender el algoritmo, valida orientación, escala horizontal, alturas, normales, posición sobre el suelo y ausencia de archivos externos faltantes. Compara algunos puntos con los GeoTIFF generados por el importador.
5. Para un siguiente piloto de control cerrado, implementa un adaptador de observaciones y movimiento de Gazebo. No pases alturas globales de referencia al planificador. La referencia solo pertenece al entorno/sensor/evaluador; las salidas públicas deben respetar huella y ruido. Mantén comunicación global instantánea, sin alcance ni pérdidas.
6. Al terminar, registra comandos, versiones, pruebas efectivamente ejecutadas, fallos y límites. No atribuyas a fotogrametría o navegación física un resultado producido por el sensor ideal o por `set_pose_vector`.

No interpretes el resultado favorable de cobertura como superioridad global: la comparación inicial favorece a la política informativa en cobertura temprana, pero a proximidad en duración total. Verifica ambas medidas.
