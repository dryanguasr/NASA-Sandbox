# Checklist técnica de preparación — Space Apps

Documento de trabajo. P0: esencial; P1: importante; P2: opcional. Responsables propuestos. «Antes» significa estudio o ejercicios independientes, no adelantar el producto competitivo.

### 01 · Alcance y elegibilidad

- [ ] **A01 · P0 · Aclarar qué se puede reutilizar del sandbox**  
  Responsable propuesto: David. Momento: Antes.  
  Verificación: Respuesta escrita del organizador competente sobre trabajo previo; inventario de código, datos, recursos y fechas. No asumir que cambiar de repositorio o reescribirlo resuelve la restricción.  
  Evidencia/nota: ____________________

- [ ] **A02 · P0 · Definir usuario, decisión y resultado esperado**  
  Responsable propuesto: David. Momento: Antes.  
  Verificación: Una frase: «Ayudamos a [usuario] a decidir [acción] usando [datos] y evaluamos el resultado con [medida]». La formulación final se ajusta al reto y a las reglas.  
  Evidencia/nota: ____________________

- [ ] **A03 · P0 · Mapear requisitos del reto a evidencia visible**  
  Responsable propuesto: David. Momento: Evento.  
  Verificación: Cada requisito obligatorio tiene una pantalla, un resultado o una explicación comprobable. Separar requisitos, sugerencias y extras propios; no inventar ponderaciones oficiales.  
  Evidencia/nota: ____________________

- [ ] **A04 · P0 · Distinguir contribución propia, recursos y uso de IA**  
  Responsable propuesto: Daniel. Momento: Ambos.  
  Verificación: Inventario de fuentes, licencias, herramientas de IA y revisión humana. Verificar política vigente de declaración, imágenes, audio, branding y materiales previos.  
  Evidencia/nota: ____________________

- [ ] **A05 · P1 · Reconocer alternativas existentes y la diferencia propuesta**  
  Responsable propuesto: David. Momento: Antes.  
  Verificación: Tres capacidades ya resueltas por otras herramientas y una decisión que la propuesta pretende mejorar. No prometer novedad científica sin revisión específica.  
  Evidencia/nota: ____________________

### 02 · Datos y conocimiento

- [ ] **D01 · P0 · Documentar la procedencia de cada capa**  
  Responsable propuesto: Daniel. Momento: Ambos.  
  Verificación: Producto, misión, instrumento, fecha, unidades, proyección, escala nativa, NoData, condiciones de uso y checksum. Evidencia de que cada capa aporta a una decisión.  
  Evidencia/nota: ____________________

- [ ] **D02 · P0 · Repasar coordenadas, orientación y escalas**  
  Responsable propuesto: Daniel. Momento: Ambos.  
  Verificación: Ejercicio independiente con un punto conocido y distancias verificadas. Norte, ejes, latitud/longitud y datum consistentes. No aplicar una proyección terrestre a Marte sin justificación.  
  Evidencia/nota: ____________________

- [ ] **D03 · P0 · Diferenciar resolución, exactitud e incertidumbre**  
  Responsable propuesto: Daniel. Momento: Ambos.  
  Verificación: La leyenda distingue retícula de cálculo de resolución nativa. La incertidumbre del modelo tiene unidades y supuestos; NoData no se convierte en terreno seguro.  
  Evidencia/nota: ____________________

- [ ] **D04 · P0 · Comprobar que los datos satisfacen el reto**  
  Responsable propuesto: David. Momento: Evento.  
  Verificación: Si se exige integrar varias misiones, verificarlo realmente: CTX y HiRISE en el piloto pertenecen a MRO. No añadir una capa decorativa para aparentar integración.  
  Evidencia/nota: ____________________

- [ ] **D05 · P0 · Separar referencia del simulador y conocimiento del agente**  
  Responsable propuesto: Jesús. Momento: Evento.  
  Verificación: Una prueba verifica que el planificador no lee alturas, objetivos o estados ocultos. La vista de evaluación no modifica la información del agente.  
  Evidencia/nota: ____________________

- [ ] **D06 · P1 · Ensayar lectura y recuperación de archivos de datos**  
  Responsable propuesto: Diego. Momento: Antes.  
  Verificación: Práctica con archivos pequeños: apertura, recorte, validación y error por recurso ausente; entender qué está cacheado y qué depende de una descarga.  
  Evidencia/nota: ____________________

### 03 · Algoritmos y evidencia

- [ ] **E01 · P0 · Elegir una medida principal y una comparación sencilla**  
  Responsable propuesto: David. Momento: Ambos.  
  Verificación: Definición operacional, unidad y sentido de mejora de cada medida. Comparar con una estrategia comprensible, manteniendo datos, objetivos y presupuesto equivalentes.  
  Evidencia/nota: ____________________

- [ ] **E02 · P0 · Verificar capacidades, precedencias y exclusión de tareas**  
  Responsable propuesto: Jesús. Momento: Evento.  
  Verificación: Un objetivo no se muestra antes de descubrirse, una muestra no se asigna antes de inspeccionarse, una tarea no se duplica y un agente no ejecuta dos trabajos incompatibles.  
  Evidencia/nota: ____________________

- [ ] **E03 · P0 · Resolver explícitamente la inviabilidad**  
  Responsable propuesto: Jesús. Momento: Evento.  
  Verificación: Sin ruta o sin agente capaz, la tarea queda pendiente/bloqueada y se explica el motivo. No inventar un resultado ni forzar una asignación inválida.  
  Evidencia/nota: ____________________

- [ ] **E04 · P1 · Examinar sensibilidad y resultados desfavorables**  
  Responsable propuesto: Daniel. Momento: Evento.  
  Verificación: Probar distintos objetivos, terrenos o condiciones relevantes; variar solo ruido no demuestra generalización. Registrar cuándo una política pierde y por qué.  
  Evidencia/nota: ____________________

- [ ] **E05 · P0 · Limitar las afirmaciones a lo realmente implementado**  
  Responsable propuesto: David. Momento: Evento.  
  Verificación: Separar observación real, observación simulada, supuesto y función futura. En el piloto actual no atribuir fotogrametría, batería, seguridad EVA ni Heterogeneous DisCoverage completo.  
  Evidencia/nota: ____________________

### 04 · Arquitectura e integración

- [ ] **I01 · P0 · Acordar un contrato entre motor y visualización**  
  Responsable propuesto: Jesús. Momento: Ambos.  
  Verificación: Esquema mínimo: run_id, escenario, política, semilla, t_sim, unidades, marco, agentes, tareas, eventos y métricas. Identificadores y orden temporal estables.  
  Evidencia/nota: ____________________

- [ ] **I02 · P0 · Invalidar los resultados cuando cambian las entradas**  
  Responsable propuesto: Jesús. Momento: Evento.  
  Verificación: Cambiar una condición marca el resultado como desactualizado hasta recalcular o cargar una ejecución compatible. Nunca mostrar una trayectoria vieja bajo parámetros nuevos.  
  Evidencia/nota: ____________________

- [ ] **I03 · P0 · Etiquetar ejecución nueva y reproducción guardada**  
  Responsable propuesto: Jesús. Momento: Evento.  
  Verificación: El usuario sabe si está calculando, reproduciendo una corrida o viendo material ilustrativo. La comparación identifica los dos escenarios y las dos políticas.  
  Evidencia/nota: ____________________

- [ ] **I04 · P0 · Ensayar arranque limpio y funcionamiento sin internet**  
  Responsable propuesto: Jesús. Momento: Ambos.  
  Verificación: Prueba en una segunda máquina o entorno limpio, con dependencias fijadas y recursos locales. No basar la demo en cachés del navegador, CDN, cuentas personales o llaves expuestas.  
  Evidencia/nota: ____________________

- [ ] **I05 · P1 · Exportar resultados desde una única fuente**  
  Responsable propuesto: Daniel. Momento: Evento.  
  Verificación: Pantalla, tabla descargada y resumen coinciden en valores, unidades y run_id. Exportar PNG/CSV/JSON según necesidad; evitar cifras copiadas manualmente.  
  Evidencia/nota: ____________________

- [ ] **I06 · P0 · Definir dueño de integración y trabajo paralelo seguro**  
  Responsable propuesto: Jesús. Momento: Ambos.  
  Verificación: Responsables de módulos, interfaces y rama de integración acordados. Cambios grandes aislados y revisados; no varios agentes editando simultáneamente los mismos archivos.  
  Evidencia/nota: ____________________

### 05 · Experiencia interactiva

- [ ] **U01 · P0 · Escribir un guion de interacción con una decisión central**  
  Responsable propuesto: Jorge. Momento: Antes.  
  Verificación: En un ejercicio ajeno al entregable: objetivo → elección → consecuencia → comparación. El usuario puede explicar qué cambió por su acción.  
  Evidencia/nota: ____________________

- [ ] **U02 · P0 · Diseñar una primera pantalla que explique el propósito**  
  Responsable propuesto: Jorge. Momento: Evento.  
  Verificación: La pantalla responde qué problema se resuelve, para quién y qué acción ejecutar. Hay un caso precargado y un botón principal, no una pantalla vacía con veinte parámetros.  
  Evidencia/nota: ____________________

- [ ] **U03 · P0 · Hacer visible la causalidad de las decisiones**  
  Responsable propuesto: Jorge. Momento: Evento.  
  Verificación: Una selección permite inspeccionar dato nuevo, regla o criterio activado, tarea creada, agente elegido y efecto. Las razones se derivan de eventos y costos del algoritmo.  
  Evidencia/nota: ____________________

- [ ] **U04 · P1 · Separar demo guiada, exploración y evidencia**  
  Responsable propuesto: Jorge. Momento: Evento.  
  Verificación: La vista inicial es sencilla; el usuario puede explorar y acceder a supuestos/fuentes sin perderse. La explicación avanzada está a un nivel de distancia, no mezclada con todo.  
  Evidencia/nota: ____________________

- [ ] **U05 · P0 · Proporcionar pausa, reinicio y recuperación de cámara**  
  Responsable propuesto: Jorge. Momento: Evento.  
  Verificación: Se puede volver al caso inicial y recuperar el encuadre en una acción. Reiniciar cancela cálculos y limpia selección, tiempo, eventos, métricas y animaciones de la ejecución anterior.  
  Evidencia/nota: ____________________

- [ ] **U06 · P1 · Convertir eventos técnicos en mensajes comprensibles**  
  Responsable propuesto: Diego. Momento: Evento.  
  Verificación: Traducir etiquetas internas a frases como «Rover 2 inspecciona el objetivo B». Ofrecer identificadores técnicos y datos completos en el detalle para conservar trazabilidad.  
  Evidencia/nota: ____________________

### 06 · Diseño visual y accesibilidad

- [ ] **V01 · P0 · Definir una gramática visual estable**  
  Responsable propuesto: Jorge. Momento: Antes.  
  Verificación: En ejercicios genéricos: tipografía, espaciado, botones, leyenda, símbolos y estados consistentes. Colores de agente y colores de estado no se confunden.  
  Evidencia/nota: ____________________

- [ ] **V02 · P0 · Comprobar lectura y contraste en condiciones de presentación**  
  Responsable propuesto: Diego. Momento: Evento.  
  Verificación: Probar a 1366×768 y 1920×1080, zoom 125–150 % y proyección o vista alejada. Contraste de texto conforme al criterio aplicado; ninguna alerta depende solo del color.  
  Evidencia/nota: ____________________

- [ ] **V03 · P0 · Probar teclado, foco y alternativas al movimiento**  
  Responsable propuesto: Diego. Momento: Evento.  
  Verificación: Controles alcanzables con teclado, foco visible, información que no dependa solo de hover o audio, pausa y reducción de movimiento. Evitar destellos y cámara involuntaria.  
  Evidencia/nota: ____________________

- [ ] **V04 · P1 · Usar animación solo cuando explique un cambio**  
  Responsable propuesto: Jorge. Momento: Evento.  
  Verificación: Cada transición tiene propósito: mostrar observación, creación de tarea, reasignación o comparación. Velocidad de reproducción y tiempo simulado siempre identificables.  
  Evidencia/nota: ____________________

- [ ] **V05 · P2 · Añadir 3D o sonido solo después de superar los criterios esenciales**  
  Responsable propuesto: Jorge. Momento: Evento.  
  Verificación: El mapa y los resultados siguen disponibles si falla WebGL. Audio opcional y silenciable; 3D sin añadir una interacción más difícil que la decisión científica.  
  Evidencia/nota: ____________________

### 07 · Pruebas de producto

- [ ] **T01 · P0 · Hacer una prueba con personas ajenas al equipo**  
  Responsable propuesto: Diego. Momento: Ambos.  
  Verificación: Dos o tres personas ejecutan un ejercicio sin recibir instrucciones paso a paso. Anotar dónde se detienen y qué entendieron; no interpretarlo como validación estadística.  
  Evidencia/nota: ____________________

- [ ] **T02 · P0 · Ensayar fallos y acciones rápidas**  
  Responsable propuesto: Diego. Momento: Evento.  
  Verificación: Doble clic, cambio de escenario durante cálculo, reinicio, error de carga, resultado vacío y pérdida de red. La interfaz conserva coherencia y ofrece una salida.  
  Evidencia/nota: ____________________

- [ ] **T03 · P1 · Automatizar recorridos y regresión visual**  
  Responsable propuesto: Jesús. Momento: Evento.  
  Verificación: Pruebas sobre controles y resultados; capturas en estados fijos, misma semilla, entorno y reloj. Revisar referencias antes de aceptar diferencias de imagen.  
  Evidencia/nota: ____________________

- [ ] **T04 · P1 · Medir carga y respuesta en el portátil de presentación**  
  Responsable propuesto: Jesús. Momento: Evento.  
  Verificación: Presupuesto interno propuesto: primera vista útil <5 s en arranque local limpio, confirmación visual inmediata y comparación/replay fluido. Si tarda más, estado de progreso y cancelación.  
  Evidencia/nota: ____________________

### 08 · Comunicación y entrega

- [ ] **C01 · P0 · Mostrar beneficio, costo y límites juntos**  
  Responsable propuesto: David. Momento: Evento.  
  Verificación: Una comparación visible y trazable: qué mejora, qué empeora y bajo qué hipótesis. No esconder la política básica si gana en una medida.  
  Evidencia/nota: ____________________

- [ ] **C02 · P0 · Probar enlaces y entregables desde una sesión ajena**  
  Responsable propuesto: Diego. Momento: Evento.  
  Verificación: Sin autenticación inesperada ni permisos privados. Comprobar reglas vigentes de idioma, formato, duración, referencias y declaración de IA.  
  Evidencia/nota: ____________________

- [ ] **C03 · P0 · Ensayar defensa y relevo del presentador**  
  Responsable propuesto: David. Momento: Evento.  
  Verificación: Cualquiera puede explicar usuario, datos, contribución, comparación y límites. Preparar ruta breve y ampliada; duración final subordinada al formato autorizado.  
  Evidencia/nota: ____________________

- [ ] **C04 · P1 · Congelar una versión presentable y disponer de respaldo**  
  Responsable propuesto: Jesús. Momento: Evento.  
  Verificación: Release/commit identificable, copia local, resultado guardado y video de respaldo claramente rotulado. Ensayar transición al respaldo sin fingir ejecución nueva.  
  Evidencia/nota: ____________________

- [ ] **C05 · P2 · Mantener un listado de extras que no entran en la primera versión**  
  Responsable propuesto: David. Momento: Antes.  
  Verificación: Excluir por defecto cuentas, multijugador, motor físico nuevo, editor universal, chat ornamental y efectos que no cambien una decisión. Reintroducir solo con criterio de aceptación y responsable.  
  Evidencia/nota: ____________________


Las fuentes y el desarrollo de cada criterio están en el manual. La regla de trabajo previo está explicada por la organización en https://github.com/nasa/spaceapps/discussions/1813 .
