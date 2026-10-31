# Plan: el Administrador con el diseño v3

- **Fecha:** 31 de octubre de 2026
- **Qué es:** llevar las pantallas del Administrador al mismo diseño del Operario (las reglas están en el [plan del Operario v3](plan_rediseno_operario_v3.md)) y construir lo que falta.
- **Rama:** `feature/rediseno-admin-v3`, desde `feature/rediseno-operario-v3`.

## Regla del menú

Cada cosa vive en un solo lugar, según la pregunta que responde. Los submenús son pestañas arriba de la pantalla; en celular, la barra inferior muestra solo los cuatro menús. Mi perfil sigue en el avatar.

## Menús y submenús

**1. Equipo:** ¿cómo está mi gente hoy?
- **Tablero del turno** (lo primero): una fila por persona, qué hace ahora, su carga y quién está sobrecargado.
- **Asistencia:** quién vino hoy, entrada, salida y salida anticipada; validar y corregir.
- **Novedades:** quién no llegó (con sus actividades para reasignar) y quién detuvo una de hora fija por emergencia.

**2. Actividades:** ¿qué trabajo hay?
- **Actividades** (lo primero): lista con filtros (Por hacer, Sin asignar, En curso o pausadas, Terminadas, Todas), agrupada por día. Crear, editar, asignar y cancelar.
- **Proyectos:** lista con el avance en horas; el detalle muestra sus actividades.
- **Reportes:** los reportes de actividad por revisar; se convierten en actividad o se descartan.

**3. Indicadores:** ¿cómo nos fue? (por semana)
- **Empresa** (lo primero): cumplimiento de jornada, aprovechamiento, tiempo adicional y cumplimiento de actividades.
- **Por persona:** lo mismo por operario, con su asistencia, lo real frente a lo estimado y sus pausas.
- **Por categoría y proyecto:** el cumplimiento de actividades agrupado así.

**4. Administración:** ¿cómo está configurada mi empresa?
- **Usuarios** (lo primero): crear, desactivar, reactivar y cambiar el turno.
- **Turnos:** el catálogo de turnos y cuántas personas tiene cada uno.
- **Empresa:** los límites de usuarios.

## Lo que se decidió (31 de octubre de 2026)

1. Se rediseña lo que existe y se construye lo que falta.
2. Antes de construir cada pantalla se muestra un esquema para aprobarlo.
3. Prioridad y estado como texto con su ícono; solo Urgente, Hora fija y Retraso llevan etiqueta.
4. El detalle de una actividad se abre como panel lateral en computador y a pantalla completa en celular.
5. El menú de arriba (ya está en el alcance, Sección 6.2, y en el glosario).

## Los pasos

Un paso por menú. En cada uno: esquema, aprobación, construir, probar, commit.

1. **Actividades**, con el panel lateral del detalle (lo usan los demás menús).
2. **Administración.**
3. **Equipo**, con Novedades y el aviso cuando alguien no llegó (lleva servidor y pruebas).
4. **Indicadores.**
5. **Revisión final:** contraste, capturas, revisión de diseño y pruebas.
