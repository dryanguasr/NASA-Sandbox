# Preparación técnica y diseño de demos científicas interactivas

**Equipo:** David Yanguas, Jesús Flores, Jorge Fajardo, Daniel Cartagena y Diego Amaya.  
**Edición del documento:** 10 de noviembre de 2026.  
**Aplicación:** NASA Space Apps; guía reutilizable para otros retos y productos.  
**Estado:** recomendaciones y criterios propuestos. Las casillas no vienen certificadas como cumplidas.

## 1. La decisión estratégica

La preparación debería fortalecer tres capacidades: construir algo que funcione, demostrar por qué aporta y permitir que otra persona lo entienda sin depender continuamente de un desarrollador. El acabado visual debe facilitar esa comprensión.

La experiencia deseada para un jurado es: **«Entiendo el problema; puedo probar una decisión; veo su consecuencia; puedo comprobar de dónde sale el resultado».** Esa es la prioridad del manual. No se promete un resultado competitivo ni se asignan pesos oficiales inventados.

La guía de evaluación 2025 usa impacto, creatividad, validez, relevancia y presentación como orientación para un juicio global. También incluye usabilidad dentro de la validez. Es un antecedente útil para preparar evidencia, pero los formatos y condiciones aplicables se verifican en la guía vigente de 2026. [S2]

### Un requisito previo importante

La organización global indicó el 5 de noviembre de 2026 que se puede estudiar, investigar recursos y formar equipo antes del evento, pero que comenzar el proyecto antes del inicio oficial puede causar descalificación. [S1] El sandbox ya desarrollado no queda autorizado para la competencia por llamarse «prueba». Antes de reutilizarlo, describir honestamente su historial y pedir aclaración escrita al organizador competente. No borrar historial ni asumir que reescribir el código elimina la restricción.

Esta guía es material de estudio. Los ejercicios de interfaz previos deberían hacerse con problemas independientes del entregable. Los diseños finales, pantallas y código específicos se reservan para la ventana autorizada. La aprobación local puede no resolver por sí sola una condición de elegibilidad global: aclarar el alcance de la respuesta recibida.

## 2. Cómo usar la checklist

**P0:** condición esencial para una propuesta defendible y presentable. **P1:** mejora importante cuando la base está estable. **P2:** ampliación opcional.

**Antes:** estudio, acuerdos, revisión de reglas o ejercicios independientes. **Evento:** implementación y comprobación sobre el producto que se entregará. **Ambos:** practicar antes y volver a verificar sobre el entregable dentro de la ventana permitida.

Los responsables son una propuesta, no una evaluación de aptitudes. Jesús tiene el perfil de integración más probable según lo descrito, pero conviene comprobar su experiencia concreta en interfaces. Cada integrante debe tener un resultado propio verificable y una persona de respaldo. Marcar una casilla exige una evidencia o nota breve; estar «verificado» aquí no equivale a aprobación de NASA.

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


## 3. Manual de experiencia tipo videojuego

### 3.1 Diseñar desde lo que debe entender el usuario

El marco MDA distingue mecánicas, dinámicas y experiencia. [S5] Lo adaptaría a una demostración científica así:

| Pregunta | Aplicación a la demo |
|---|---|
| ¿Qué queremos que experimente? | Curiosidad, capacidad de decidir y comprensión de una consecuencia. |
| ¿Qué comportamiento lo produce? | Elegir entre alternativas y comparar sus resultados. |
| ¿Qué control concreto hace falta? | Un selector de estrategia, un objetivo elegible o una condición de escenario. |
| ¿Qué evidencia lo respalda? | Trayectoria, evento y medida calculados para esa misma ejecución. |

No todas las aplicaciones necesitan ser juegos. Un simulador, tablero o mapa puede aprovechar objetivos claros, decisiones, descubrimientos y retroalimentación sin puntuaciones artificiales, recompensas arbitrarias ni ficción excesiva.

### 3.2 El ciclo central de interacción

**Situación → objetivo → elección → consecuencia → comparación → siguiente decisión.**

En una aplicación de exploración, la pregunta podría ser: «¿Priorizamos conocer el terreno pronto o terminar la misión en menos tiempo?». En una herramienta ambiental: «¿Qué zona conviene inspeccionar primero?». En una aplicación educativa: «¿Qué cambia al modificar esta condición?». La estructura funciona con temas diferentes.

Una decisión útil tiene al menos dos alternativas defendibles y una consecuencia visible. Pulsar «iniciar» y observar una animación puede ser una buena introducción, pero no reemplaza una exploración de decisiones.

### 3.3 Diseñar una demostración corta completa

Como objetivo de ensayo interno, preparar una secuencia de 90 segundos, adaptable al tiempo oficial:

| Intervalo propuesto | Qué ve y entiende el espectador |
|---|---|
| 0–15 s | Quién tiene el problema y qué debe decidir. |
| 15–30 s | Qué información existe y qué incertidumbre queda. |
| 30–55 s | Una elección del usuario y la respuesta del sistema. |
| 55–75 s | Un resultado comparado con una alternativa comprensible. |
| 75–90 s | El beneficio, el costo y el límite principal. |

Los 90 segundos son un criterio de preparación propio, no el límite oficial de Space Apps. Separar demo interactiva, presentación local y material de entrega global: pueden tener restricciones diferentes.

### 3.4 Tres vistas, tres necesidades

**Demo guiada.** Caso precargado, pocas acciones y hitos con explicación. Debe servir al presentador sin obligarlo a operar veinte controles.

**Exploración.** Cambios permitidos, comparación entre alternativas, pausa, reinicio y selección de entidades. El sistema mantiene consistencia entre entradas y resultados.

**Evidencia.** Fuentes, unidades, hipótesis, versión, semilla, métricas detalladas y archivos exportables. Lo avanzado se ofrece de forma accesible, sin llenar la primera pantalla. Esta separación aplica la revelación progresiva de información. [S3]

### 3.5 Arquitectura visual de una pantalla

Propuesta para una vista horizontal de computadora:

- Encabezado: objetivo de la misión, escenario y estado de ejecución.
- Área principal: mapa o visualización central; debe dominar la pantalla.
- Panel lateral: selección actual, decisión y explicación corta de sus consecuencias.
- Banda de resultados: hasta tres medidas principales con unidades y comparación.
- Línea de tiempo: hitos, reproducción, pausa y reinicio.
- Acceso secundario claro: fuentes, supuestos y reporte.

No es obligatorio usar este reparto para todos los productos. Lo importante es que el tamaño visual responda a la importancia de la información. Si el jurado debe leer una tabla extensa para entender por qué la aplicación existe, falta una síntesis.

### 3.6 Biblioteca de patrones útiles

| Patrón | Para qué sirve | Implementación mínima | Riesgo a evitar |
|---|---|---|---|
| Antes/después | Mostrar mejora del conocimiento o cambio de decisión. | Dos vistas sincronizadas con la misma escala y leyenda. | Cambiar escalas para exagerar diferencias. |
| Dos políticas | Mostrar una compensación entre objetivos. | Escenario común y dos resultados identificados. | Cambiar objetivos o presupuesto entre políticas. |
| «¿Por qué?» | Explicar asignaciones o recomendaciones. | Razón derivada de eventos, capacidades y costos. | Inventar razones mediante texto persuasivo. |
| Hitos | Saltar al descubrimiento o decisión relevante. | Marcadores en la línea temporal. | Ocultar eventos desfavorables. |
| Detalle a demanda | Mostrar rigor sin saturar. | Seleccionar entidad y abrir su ficha. | Convertir cada clic en un panel distinto sin salida. |
| Recuperar vista | Reducir errores de navegación. | Botón «Volver a la vista general». | Cámara 3D que se pierde o gira sola. |
| Resultado exportable | Permitir verificar y compartir. | PNG/CSV/JSON asociados al run_id. | Exportar datos de otra ejecución. |
| Estado vacío con salida | Resolver situaciones sin solución. | Motivo y acciones disponibles. | Pantalla en blanco o progreso infinito. |

### 3.7 Hacer visible la causalidad

La unidad narrativa más valiosa es **dato → decisión → consecuencia**. Un ejemplo de mensaje, cuyo contenido tendría que proceder del sistema, es:

> Se observó el sector norte. El objetivo B quedó disponible para inspección. Rover 2 fue asignado porque cumple los requisitos y tiene menor costo estimado entre los rovers disponibles.

Mostrar solo «INSPECT:S2» conserva el identificador pero pierde la explicación. Conservar ambos: frase en la vista principal e identificador técnico en el detalle. La visibilidad del estado y la retroalimentación son principios de usabilidad, no adornos. [S4]

En una versión posterior, mostrar la tabla de candidatos con costo y restricciones. No llamar «óptimo» a un resultado si solo es óptimo para la asignación instantánea y no para toda la misión.

### 3.8 Usar la incertidumbre como parte de la experiencia

Separar al menos: sin información, información orbital aproximada y observación local. Un área observada puede seguir siendo incierta. La visualización no debe sugerir que ha pasado automáticamente a ser segura.

La referencia de evaluación se coloca en una vista claramente rotulada y aislada de los controles del planificador. Si se compara CTX con HiRISE, explicar qué es información inicial, qué es referencia reservada y qué obtiene realmente el sensor simulado. Una capa de incertidumbre necesita unidad, escala y definición, no solo una paleta atractiva.

### 3.9 Gramática visual propuesta

Usar pocos tamaños tipográficos y espaciados consistentes; una familia legible y fuente de sistema son suficientes. Evitar tipografía de ciencia ficción para párrafos y cifras.

Asignar formas diferentes a clases de agente y combinar forma, texto y color. Separar identidad —qué agente es— de estado —qué está haciendo—. No reutilizar el mismo significado visual para «rover», «éxito» y «zona segura».

Como referencia de accesibilidad web, WCAG indica contraste mínimo 4.5:1 para texto normal y 3:1 para texto grande, con sus excepciones. La información no debe depender exclusivamente del color. [S6, S7] Probar el diseño en proyección y a distancia: cumplir una razón de contraste no garantiza por sí solo legibilidad en la sala. [S8]

Objetivos internos sugeridos: texto principal de 18–22 px en modo presentación, controles grandes, foco visible, pocas cifras decimales y cifras con unidades. Los tamaños concretos se ajustan tras probar la pantalla real; no son requisitos de NASA.

Animar lo que cambió, permitir pausa y respetar reducción de movimiento. Evitar destellos, lluvia de partículas, audio obligatorio y desplazamientos de cámara que interrumpan la lectura. El aspecto oscuro puede servir en una pantalla, pero comprobar una alternativa de alto contraste para proyección.

### 3.10 Estados que deben diseñarse antes del acabado

Definir visualmente: listo, calculando, completo, sin solución, error, cancelado y resultado desactualizado. Cada estado responde «qué pasa» y «qué puedo hacer».

Si cambia una entrada, el resultado anterior queda marcado como desactualizado. Si se reinicia, no debe seguir apareciendo un callback tardío de otra ejecución. Si dos paneles comparan políticas, mostrar el mismo tiempo simulado o identificar expresamente que se están comparando estados finales.

Nunca mostrar controles que aparenten alterar el modelo y solo modifiquen la decoración. Un slider de batería no corresponde al piloto actual mientras la batería no esté modelada. Un selector de estrategia que carga una ejecución ya calculada debe decirlo.

## 4. Arquitectura técnica mínima

Separar tres capas: **cálculo → contrato de datos → presentación**. El motor resuelve el problema; la interfaz ayuda a entenderlo. Gazebo puede aportar reproducción o sensores, pero no debe bloquear necesariamente la apertura del resumen y de la evidencia.

El contrato podría incluir:

```text
run_id, schema_version, scenario_id, policy_id, seed
sources, assumptions, coordinate_frame, units
t_sim, agent_states, task_states, events, metrics
```

Distinguir tres modos: cálculo nuevo, reproducción verificable y material ilustrativo. No usar un video o una trayectoria guardada como si reflejara una decisión recién calculada.

Una ejecución nueva requiere invalidar salidas anteriores, mostrar progreso, gestionar cancelación y asociar todos los resultados al mismo identificador. Una reproducción solo necesita navegar un registro inmutable; sigue siendo interactiva si permite inspección y comparación honesta.

### Elección de herramientas

**Primera opción para el equipo:** extender habilidades web, sin cambiar el motor de misión por razones estéticas. HTML/CSS/JavaScript y Canvas/SVG bastan para mapas, controles, trazas y resultados. Elegir React u otro framework solo si alguien puede mantenerlo cómodamente.

**Three.js:** opción para un terreno 3D puntual cuando aporte comprensión. Su documentación incluye instalación con npm y desarrollo mediante servidor local. Empaquetar recursos; no dar por hecho que una aplicación modular funcionará con doble clic o sin CDN. [S10]

**Godot:** buena posibilidad cuando la interacción de juego sea el producto central y haya experiencia real en el equipo. La exportación web tiene requisitos de WebAssembly/WebGL 2, restricciones por lenguaje y condiciones adicionales al usar multihilo. Comprobar el despliegue antes de comprometerse con el motor. [S11]

No escoger una herramienta por una captura espectacular. El criterio de selección es producir una decisión, una consecuencia y una comparación verificables con el menor riesgo de integración.

## 5. Ejercicios previos de interfaz, separados del entregable

### Ejercicio A — Decisión y consecuencia

Problema independiente: tres vehículos reparten paquetes en un plano ficticio. Diseñar una pantalla que permita cambiar una prioridad y comparar resultados de dos casos de práctica. La observación clave es si una persona ajena explica el cambio sin recibir una clase.

### Ejercicio B — Explicación del algoritmo

Usar un pequeño conjunto de resultados ya calculados. Permitir seleccionar una asignación y ver candidato elegido, alternativas, costo y motivo de incompatibilidad. Todo texto debe salir de datos explícitos, no de explicaciones inventadas.

### Ejercicio C — Robustez de la experiencia

Cargar un archivo con datos faltantes, reiniciar durante una animación, cambiar el tamaño de ventana y quitar internet. El objetivo es aprender a diseñar estados coherentes y recuperar el control. Una práctica de interfaz puede revelar más riesgos de producto que añadir otro simulador.

### Ejercicio D — Narración y exportación

A partir de una misma ejecución de práctica, generar una tarjeta de resultados, una tabla y una captura. Comprobar que las tres representaciones cuentan la misma historia. Ensayar explicaciones breves y ampliadas, sin tomar ese material como el entregable competitivo.

Los ejercicios generan aprendizaje y criterios. Su eventual reutilización material depende de las reglas y de la respuesta sobre trabajo previo.

## 6. Aplicación al piloto Jezero ya existente

La versión adjunta de `Jezero_visor_mision.html` ya contiene mapa, cuatro capas, reproducción, velocidad, trayectorias, agentes, objetivos y eventos. El trabajo de diseño pendiente más valioso no sería añadir más paneles: sería conectar esos elementos con una decisión del usuario.

### Experiencia candidata para estudiar

1. Explicar la misión en una frase.
2. Elegir entre conocer pronto el terreno o completar antes las tareas, sin prometer una nueva política si no se ha implementado.
3. Comparar las dos políticas disponibles sobre el mismo escenario.
4. Saltar al primer descubrimiento y mostrar la cadena de tareas.
5. Mostrar resultado favorable y costo asociado.
6. Abrir la evidencia y los límites.

El reporte adjunto aporta una compensación real dentro de ese experimento: la política informativa llegó al 80 % de cobertura en 320 s frente a 440 s de proximidad, pero terminó la misión en 1930 s frente a 1660 s. Ese contraste es una historia de decisión útil. Son simulaciones sobre el mismo terreno y objetivos; tres semillas de ruido no prueban generalización.

Pendientes metodológicos que la interfaz debe respetar: CTX y HiRISE proceden de MRO; sensores y objetivos son hipotéticos; no hay batería ni conectividad limitada; no hay reconstrucción por cámaras. La propuesta no requiere introducir ahora comunicaciones degradadas, porque se acordó conexión global ideal.

## 7. Responsabilidades sugeridas

| Persona | Responsabilidad propuesta | Entregable de preparación | Límite de alcance |
|---|---|---|---|
| David | Problema, rigor, prioridades y explicación | Criterios de éxito, afirmaciones permitidas y preguntas de defensa. | Evitar convertirse en aprobador de cada detalle de interfaz. |
| Jesús | Integración, contrato de datos y despliegue | Ejercicio que conecte datos y pantalla; plan de ejecución y pruebas. | Confirmar experiencia de frontend antes de asignarle toda la UI. |
| Jorge | Interacción y visualización | Patrón de decisión/consecuencia y gramática visual. | Una mecánica central y un efecto visual útil antes de cualquier 3D extra. |
| Daniel | Datos, medidas y comparación | Diccionario de datos, métricas y ensayo comparativo independiente. | Congelar una línea base antes de añadir un método más complejo. |
| Diego | Pruebas, eventos comprensibles y evidencia | Registro de usabilidad y componente acotado de eventos/exportación. | Tener una contribución funcional propia y apoyo de Jesús; no quedar solo con tareas auxiliares. |

Parejas útiles: Jesús–Jorge para integrar interacción y motor; Daniel–Diego para revisar trazabilidad y pruebas. David revisa las decisiones de alcance y las afirmaciones, no cada color o animación.

## 8. Prueba de aceptación de la experiencia

Como umbrales internos de entrenamiento, no oficiales:

- En 15 s una persona identifica a quién sirve y para qué.
- En 30 s encuentra la acción principal.
- En 90 s explica una consecuencia y una diferencia entre alternativas.
- Puede reiniciar y volver a la vista general sin ayuda.
- Puede localizar una fuente y reconocer una limitación.
- La demo se abre sin depender del terminal de un desarrollador.

Probar con dos o tres personas ajenas al desarrollo y preguntar: «¿Qué intentabas hacer?», «¿Qué esperabas al pulsar?», «¿Qué cambió?», «¿Qué no te queda claro?». Observar antes de explicar. Esto es detección cualitativa de problemas, no un estudio de usuarios representativo.

Automatizar después los recorridos que ya tienen sentido. Playwright puede comparar capturas con referencias, pero el render depende de navegador, sistema y configuración; fijar esos factores y el tiempo de simulación. [S9] Las capturas detectan cambios visuales; las pruebas de datos detectan incoherencias numéricas.

## 9. Reglas de recorte de alcance

Toda función debe tener un usuario, una decisión que mejora, un responsable y una prueba de aceptación. Si falta uno, pasa a la lista de extras.

Poner por delante: propósito claro, datos trazables, flujo completo, comparación honesta, estados de error, reinicio y exportación. Después: explicación avanzada, atajos temporales, modo presentación y pulido de transiciones. Al final: 3D adicional, audio o personalización.

No introducir por defecto cuentas, autenticación, chat, multijugador, nuevos motores físicos ni edición libre de escenarios. Un chatbot sería justificable solo con una necesidad y pruebas concretas; no por la expectativa de que «usar IA» haga más competitivo el producto.

Durante el evento, reservar un tramo explícito para congelar funciones, verificar y ensayar. La fracción concreta depende del horario; como punto de partida de planificación usar el último cuarto del tiempo útil. Es una propuesta del equipo, no una regla del evento.

## 10. Lecturas dirigidas

**NASA Eyes:** explorar una experiencia de datos científicos interactivos y anotar cómo orienta, selecciona y explica, sin intentar reproducir toda su escala. [S12]

**MDA:** identificar experiencia deseada y traducirla a una mecánica observable. [S5]

**Revelación progresiva y estado del sistema:** decidir qué mostrar al principio y cómo comunicar cálculo, resultado y error. [S3, S4]

**Accesibilidad y pruebas:** revisar contraste, redundancia de color y capturas automatizadas. [S6–S9]

El objetivo de lectura es obtener una decisión de diseño y un criterio de prueba por recurso, no acumular tutoriales.

## 11. Plantilla de una página para cualquier producto

```text
Nombre provisional:
Usuario y situación:
Decisión que necesita tomar:
Dato que cambia esa decisión:
Lo que hará al abrir la aplicación:
Alternativas que podrá comparar:
Consecuencia visible:
Métrica principal y unidad:
Comparación sencilla:
Supuesto y límite más importantes:
Fuente y uso permitido:
Modo: cálculo nuevo / reproducción / ilustración:
Responsable de integración:
Prueba con persona ajena:
Plan de recuperación:
```

**Criterio final:** la experiencia es convincente cuando permite comprender y verificar una decisión, incluso sin el video editado y sin que el profesor traduzca cada pantalla.

## Fuentes y notas

Las secciones de diseño, los tiempos de ensayo y la asignación de responsabilidades son propuestas propias para este equipo. Las normas aplicables se consultan en su versión vigente; las guías históricas están identificadas como tales.

**[S1] Organización global Space Apps, respuesta del 5 de noviembre de 2026.** Preparación permitida, restricción de trabajo previo y riesgo de descalificación.  
https://github.com/nasa/spaceapps/discussions/1813

**[S2] Space Apps, Judging Instructional Guidance 2025.** Antecedente de criterios y requisitos. No reemplaza las bases de 2026.  
https://spaceapps-v2-staging.s3.amazonaws.com/media/documents/Final_Space_Apps_2025_Judging_Guidelines_for_web.pdf

**[S3] Nielsen Norman Group, Progressive Disclosure.** Separar acciones frecuentes de detalle avanzado.  
https://www.nngroup.com/articles/progressive-disclosure/

**[S4] Nielsen Norman Group, Visibility of System Status.** Mostrar estado y consecuencias de las acciones.  
https://www.nngroup.com/articles/visibility-system-status/

**[S5] Hunicke, LeBlanc y Zubek (2004), MDA.** Marco de mecánicas, dinámicas y experiencia; adaptación propia a demos científicas.  
https://aaai.org/papers/ws04-04-001-mda-a-formal-approach-to-game-design-and-game-research/

**[S6] W3C, WCAG 2.2: contraste mínimo.** Texto normal 4.5:1 y texto grande 3:1, con las excepciones del criterio.  
https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html

**[S7] W3C, WCAG 2.2: uso del color.** El color no debe ser el único canal para comunicar significado.  
https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html

**[S8] Microsoft, Xbox Accessibility Guideline 102.** Contraste y condiciones de visualización en interfaces de juegos.  
https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/102

**[S9] Playwright, Visual comparisons.** Comparación de capturas y necesidad de entornos consistentes.  
https://playwright.dev/docs/test-snapshots

**[S10] Three.js, Installation.** Dependencias, build y servidor local para aplicaciones web.  
https://threejs.org/manual/pages/installation.html

**[S11] Godot, Exporting for the Web.** WebAssembly/WebGL 2 y requisitos de exportación, incluidos multihilo y C#.  
https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html

**[S12] NASA Science, Eyes.** Referencia de visualización científica interactiva.  
https://science.nasa.gov/eyes/

**[S13] HackAthlone 2026, reproducción del reto Martian Map.** Referencia de trabajo: mapa integrado, exploración humana y varias misiones; contrastar con enunciado central vigente.  
https://hackathlone.com/challenges/interplanetary-survival-guide-martian-map

**Antecedentes del equipo consultados:** `Jezero_visor_mision.html`, versión adjunta en esta conversación, y `Jezero_reporte_resultados.md`, secciones «Alcance y procedencia», «Comparación pareada» y «Límites». Los resultados citados describen ese piloto, no una nueva ejecución ni el estado actual completo del repositorio.
