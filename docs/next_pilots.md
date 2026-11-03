# Guía de pilotos para Codex

Cada piloto debe dejar logs, comandos, versiones y un resultado verificable.

## P0 — Integridad sin Gazebo

```bash
python3 scripts/generate_terrain.py --check
python3 scripts/validate_scene.py
```

Esperado: 2 humanos, 2 drones, 2 rovers; XML válido y terreno consistente.

## P1 — Arranque de Gazebo

```bash
bash scripts/run_gazebo.sh
```

Comprobar seis agentes, cráteres, hábitat, dos sitios de interés, cámaras
y ausencia de errores de recursos/plugins. Guardar captura y log.

## P2 — Movimiento de los seis agentes

```bash
bash scripts/smoke_commands.sh
```

Inspeccionar `/model/<id>/cmd_vel`, odometría y parada. Registrar
movimientos antes/después, penetraciones y colisiones; el control de humanos
y drones es abstracto.

## P3 — ROS 2 y percepción

```bash
bash scripts/run_ros_bridge.sh
```

Validar /clock, seis cmd_vel, seis odom y publicar cámaras al
descubrir sus tópicos Gazebo.

## P4 — Terreno científico y tareas

Importar DEM NASA con georreferenciación, añadir costos por agente,
restricciones y reasignación. Comparar expedición con y sin reconocimiento
robótico. Mantener el escenario sintético como caso de regresión.

Este sandbox es de preparación: revisar las condiciones de NASA Space
Apps antes de reutilizar código en la entrega de la hackatón.
