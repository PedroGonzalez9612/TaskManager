# Casos de lógica por definir

Situaciones que el sistema todavía no contempla o que resuelve de una forma que conviene confirmar. Cada caso dice qué pasa hoy y qué se propone. Cuando se decida, la regla pasa al [alcance](alcance_proyecto.md) con su fila en la bitácora, y el caso sale de este documento.

Fecha de la revisión: 2026-10-10.

## Actividades de hora fija

| # | Caso | Qué pasa hoy | Propuesta |
|---|---|---|---|
| F1 | El operario intenta **iniciar una de hora fija antes de su hora** | Se puede iniciar en cualquier momento | Solo desde 15 minutos antes de su hora. Antes, el botón se desactiva y dice "Podrás iniciarla desde las 09:45". Los 15 minutos serían un dato configurable por empresa |
| F2 | La **inicia tarde** (por ejemplo, a las 10:40 si era a las 10:00) | Se permite y no queda registro del retraso | Se permite, y se guarda el retraso de inicio (40 min) como dato para un indicador de puntualidad |
| F3 | El Administrador programa **dos de hora fija que se cruzan** para el mismo operario | Se permite sin aviso | No se permite: "Carlos ya tiene una actividad de hora fija de 10:00 a 11:00" |
| F4 | Una de hora fija **termina después del fin del turno** del operario | Se permite sin aviso | Se permite (el turno no limita), con un aviso al asignar |
| F5 | Pasa algo grave **durante una de hora fija** (falla del equipo, accidente) y el operario necesita detenerla | No se puede pausar; solo finalizar | Permitir detenerla solo con un motivo de una lista corta (por ejemplo, "Emergencia" o "Falla del equipo"), y que quede marcada para el Administrador |
| F6 | El Administrador **cambia la hora** de una de hora fija que ya se inició | Se permite | No se permite mientras esté en curso o pausada |

## Ejecución

| # | Caso | Qué pasa hoy | Propuesta |
|---|---|---|---|
| E1 | El operario **inicia una actividad sin haber marcado entrada** | Se permite | Pedir la entrada primero: "Marca tu entrada para empezar". El turno no limita, pero la asistencia debe existir para atribuir bien el tiempo |
| E2 | Intenta **marcar la salida con una actividad en curso** | Se permite y la actividad sigue corriendo | No se permite hasta pausarla o finalizarla; la pantalla ofrece pausarla con el motivo "Fin de turno" en el mismo paso |
| E3 | **Inicia una actividad de un día futuro** | Se permite si la tiene asignada | Solo se ejecuta lo de la jornada vigente. Para adelantar trabajo, el Administrador le cambia la fecha |
| E4 | **Finaliza en segundos** una actividad estimada en horas (lo que pasó en la base de prueba: "Tomó 0 min") | Se acepta y daña la precisión de la estimación | Si el tiempo real es menor que el 10 % del estimado, pedir confirmación con una observación obligatoria |
| E5 | **Dos urgentes** llegan al mismo tiempo | Las dos se muestran; la primera queda arriba | Ordenarlas por hora de creación y avisar al Administrador cuando un operario tiene más de una urgente |

## Asignación y planeación

| # | Caso | Qué pasa hoy | Propuesta |
|---|---|---|---|
| A1 | Se **asigna una actividad a un operario que no tiene turno** ese día | Se permite sin aviso | Aviso al asignar: "Luisa no tiene turno el sábado" |
| A2 | Se **retira a un operario que tiene la actividad en curso** | Se permite y su ejecución se cierra | No se permite mientras esté en curso; primero debe pausarla |
| A3 | Se **edita el estimado o la fecha de una actividad en curso** | Se permite | El estimado sí (cambia el fin proyectado); la fecha no, mientras esté en curso |
| A4 | Una **reprogramación automática deja una jornada sobrecargada** | Solo se ve en la carga del día | Aviso al Administrador al abrir el tablero (ya está en el alcance; falta construirlo) |

## Asistencia

| # | Caso | Qué pasa hoy | Propuesta |
|---|---|---|---|
| S1 | El operario **no marca entrada** pasado el tiempo de tolerancia | No hay aviso | Aviso al Administrador con las actividades del día de ese operario, para reasignarlas (ya está en el alcance; falta construirlo) |
| S2 | El operario **vino pero no pudo marcar** (olvido, celular sin batería) | El Administrador no puede registrarle la asistencia; solo corregir una que ya existe | El Administrador puede registrar la asistencia de un operario "Sin marca", con hora de entrada, hora de salida y motivo; queda como Corregida |
| S3 | **Sale antes del fin del turno** | Se permite y no queda marcado | Se permite y se muestra como "Salida anticipada" para el Administrador y para los indicadores |
| S4 | Se **cambia el turno de un operario con la asistencia abierta** | Se permite; el turno nuevo rige desde la fecha indicada | Se mantiene así: la jornada abierta conserva su turno; el nuevo rige desde la fecha elegida, que ya no puede ser pasada |
