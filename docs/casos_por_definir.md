# Casos de lógica por definir

Situaciones que el sistema todavía no contempla o que resuelve de una forma que conviene confirmar. Cada caso dice qué pasa hoy y qué se propone. Cuando se decida, la regla pasa al [alcance](alcance_proyecto.md) con su fila en la bitácora, y el caso sale de este documento.

Fecha de la revisión: 2026-10-10.

## Actividades de hora fija

| # | Caso | Qué pasa hoy | Propuesta |
|---|---|---|---|
| F3 | El Administrador programa **dos de hora fija que se cruzan** para el mismo operario | Se permite sin aviso | No se permite: "Carlos ya tiene una actividad de hora fija de 10:00 a 11:00" |
| F4 | Una de hora fija **termina después del fin del turno** del operario | Se permite sin aviso | Se permite (el turno no limita), con un aviso al asignar |

## Ejecución

| # | Caso | Qué pasa hoy | Propuesta |
|---|---|---|---|
| E3 | **Inicia una actividad de un día futuro** | Se permite si la tiene asignada | Solo se ejecuta lo de la jornada vigente. Para adelantar trabajo, el Administrador le cambia la fecha |
| E4 | **Finaliza en segundos** una actividad estimada en horas (lo que pasó en la base de prueba: "Tomó 0 min") | Se acepta y daña la precisión de la estimación | Si el tiempo real es menor que el 10 % del estimado, pedir confirmación con una observación obligatoria |

## Asignación y planeación

| # | Caso | Qué pasa hoy | Propuesta |
|---|---|---|---|
| A1 | Se **asigna una actividad a un operario que no tiene turno** ese día | Se permite sin aviso | Aviso al asignar: "Luisa no tiene turno el sábado" |
| A2 | Se **retira a un operario que tiene la actividad en curso** | Se permite y su ejecución se cierra | No se permite mientras esté en curso; primero debe pausarla |
| A3 | Se **edita el estimado o la fecha de una actividad en curso** | Se permite | El estimado sí (cambia el fin proyectado); la fecha no, mientras esté en curso |
| A4 | Una **reprogramación automática deja una jornada sobrecargada** | Solo se ve en la carga del día | Aviso al Administrador al abrir el tablero (ya está en el alcance; falta construirlo) |

## Turnos

| # | Caso | Qué pasa hoy | Propuesta |
|---|---|---|---|
| T1 | El turno **no tiene días de descanso**: aplica todos los días | Los indicadores cuentan una jornada solo si el operario marcó asistencia o tenía actividades (alcance, Sección 5.2) | Darle al turno sus días de la semana (por ejemplo, de lunes a viernes). Así el tiempo programado, la llegada tarde y el aviso de ausencia sabrían qué días se trabaja |

## Asistencia

| # | Caso | Qué pasa hoy | Propuesta |
|---|---|---|---|
| S1 | El operario **no marca entrada** pasado el tiempo de tolerancia | No hay aviso | Aviso al Administrador con las actividades del día de ese operario, para reasignarlas (ya está en el alcance; falta construirlo) |
| S2 | El operario **vino pero no pudo marcar** (olvido, celular sin batería) | El Administrador no puede registrarle la asistencia; solo corregir una que ya existe | El Administrador puede registrar la asistencia de un operario "Sin marca", con hora de entrada, hora de salida y motivo; queda como Corregida |
| S4 | Se **cambia el turno de un operario con la asistencia abierta** | Se permite; el turno nuevo rige desde la fecha indicada | Se mantiene así: la jornada abierta conserva su turno; el nuevo rige desde la fecha elegida, que ya no puede ser pasada |
