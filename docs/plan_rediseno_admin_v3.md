# Plan: el Administrador con el diseño v3

- **Fecha:** 31 de octubre de 2026 (menú revisado el 2 de noviembre)
- **Qué es:** llevar las pantallas del Administrador al mismo diseño del Operario (las reglas están en el [plan del Operario v3](plan_rediseno_operario_v3.md)) y construir lo que falta.
- **Rama:** `feature/rediseno-admin-v3`, desde `feature/rediseno-operario-v3`.

## Quién es el Administrador

Quien organiza el trabajo de su empresa: decide qué se hace, quién lo hace y cuándo, y vigila que la carga sea justa. No ejecuta actividades. Su trabajo, según cuándo lo hace:

1. **Configurar** (una vez y cuando algo cambia): usuarios, turnos y límites.
2. **Planear** (a diario o semanal): crear, asignar y programar actividades; proyectos.
3. **Vigilar el turno** (varias veces al día): quién no llegó, quién está sobrecargado, lo que no tiene dueño, lo detenido por emergencia, los reportes.
4. **Cerrar el día:** validar o corregir la asistencia.
5. **Revisar resultados** (semanal): indicadores y evidencia.

## Menú

Ordenado por lo que más usa. Cada cosa vive en un solo lugar. Los submenús son pestañas arriba de la pantalla; en celular, la barra inferior muestra los cuatro menús. Mi perfil sigue en el avatar.

**1. Hoy** (la pantalla de entrada; el menú muestra cuántos pendientes hay): ¿qué necesita mi atención ahora y cómo va mi gente?
- **Pendientes** (lo primero): solo lo que pide una decisión suya, y se resuelve ahí. Quién no llegó, con sus actividades para reasignar; las de hora fija detenidas por emergencia; las de hoy sin asignar o devueltas; los reportes por revisar; las personas sobrecargadas.
- **Personas:** una fila por persona que trabaja hoy (cómo va, qué hace ahora, su carga), con filtros "Necesitan atención", "Con espacio" y "Todas". Al abrirla, su día en línea de tiempo; desde ahí se reasigna su trabajo.
- **Asistencia:** entrada, salida, llegada tarde y salida anticipada; validar y corregir.

**2. Planeación:** ¿qué trabajo hay y cómo lo reparto?
- **Actividades** (lo primero): todas, de cualquier día, con filtros y agrupadas por día. Crear, editar, asignar y cancelar.
- **Carga de la semana:** personas por días, con las horas asignadas frente a la capacidad; lo que se pasa, en rojo.
- **Proyectos:** su avance en horas y sus actividades.

**3. Indicadores** (por semana): ¿cómo nos fue?
- **Empresa** (lo primero), **Por persona** y **Por actividad** (categoría y proyecto, y qué tan bien se estima).

**4. Administración:** ¿cómo está configurada mi empresa?
- **Usuarios** (lo primero), **Turnos** y **Empresa** (límites de usuarios).

El tablero por horas deja de ser la pantalla principal: lo reemplazan la lista de Personas (con el día de cada una al abrirla) y la Carga de la semana. Las áreas o grupos de personas quedan para después.

## Lo que se decidió

1. Se rediseña lo que existe y se construye lo que falta, incluido el aviso de posible ausencia.
2. Antes de construir cada pantalla se muestra un esquema para aprobarlo.
3. Prioridad y estado como texto con su ícono; solo Urgente, Hora fija y Retraso llevan etiqueta.
4. El detalle de una actividad se abre como panel lateral en computador y a pantalla completa en celular.
5. El menú de arriba (alcance, Sección 6.2, y glosario; bitácora del 2 de noviembre).

## Los pasos

Un paso por menú. En cada uno: esquema, aprobación, construir, probar, commit.

1. **Hoy**, con el aviso de ausencia (lleva servidor y pruebas) y el panel lateral del detalle.
2. **Planeación.**
3. **Administración.**
4. **Indicadores.**
5. **Revisión final:** contraste, capturas, revisión de diseño y pruebas.
