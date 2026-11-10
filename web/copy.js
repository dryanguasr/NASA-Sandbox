// UI vocabulary isolated from evidence and geometry for later localization.
export const copy = {
 agents:{human_1:'Humano 1',human_2:'Humano 2',rover_1:'Rover 1',rover_2:'Rover 2',drone_1:'Dron 1',drone_2:'Dron 2'},
 kinds:{survey:'Reconocimiento',inspect:'Inspección',sample:'Muestreo',return:'Regreso'},
 events:{initial_base_survey:'Reconocimiento previo de la base',assigned:'Asignación',completed:'Finalización',site_detected:'Objetivo descubierto',task_created:'Nueva tarea'},
 layers:{mean:'Estimación disponible en el registro. Relieve normalizado: oscuro = menor elevación, claro = mayor. La imagen usa la última instantánea conocida.',prior:'Mapa orbital inicial CTX, resolución nativa de 20 m. Relieve normalizado en la escala común del visor; el remuestreo no crea detalle nuevo.',sigma:'Incertidumbre condicional σ: oscuro = 0 m, cian claro = 3 m. No es precisión certificada ni garantía de seguridad.',reference:'EVALUACIÓN · Referencia HiRISE reservada. Esta vista no modifica el conocimiento del planificador. Relieve normalizado; no representa una observación disponible.'}
};
