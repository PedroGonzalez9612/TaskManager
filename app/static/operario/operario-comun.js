// Lo que comparten las vistas del Operario: abrir el detalle de una actividad con las acciones
// que él puede hacer (iniciar o finalizar).

function actividadEnCurso(actividades) {
    return actividades.find((actividad) => actividad.estado === "EN_EJECUCION") || null;
}

// "actividades" es la lista completa del operario (para saber si ya tiene otra en curso) y
// "alCambiar" recarga la vista después de iniciar o finalizar.
function abrirDetalleOperario(actividad, actividades, alCambiar) {
    const enCurso = actividadEnCurso(actividades);
    const acciones = [];
    let aviso = "";

    if (actividad.estado === "ASIGNADA") {
        // Una sola actividad en ejecución a la vez: el botón se desactiva y se explica por qué.
        const bloqueada = enCurso && enCurso.id !== actividad.id;
        if (bloqueada) {
            aviso = `Ya tienes una actividad en curso (${enCurso.codigo}). Finalízala para iniciar esta.`;
        }
        acciones.push({
            texto: "Iniciar actividad",
            desactivada: bloqueada,
            alHacer: async () => {
                await pedirApi(`/actividades/${actividad.id}/iniciar`, { method: "POST" });
                await alCambiar();
                mostrarAviso(`${actividad.codigo} iniciada.`);
            },
        });
    } else if (actividad.estado === "EN_EJECUCION") {
        acciones.push({
            texto: "Finalizar actividad",
            alHacer: async () => {
                await pedirApi(`/actividades/${actividad.id}/finalizar`, { method: "POST" });
                await alCambiar();
                mostrarAviso(`${actividad.codigo} finalizada.`);
            },
        });
    }
    abrirDetalleActividad(actividad, { acciones, aviso });
}
