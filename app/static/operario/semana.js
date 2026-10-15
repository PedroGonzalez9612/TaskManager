// Vista "Semana" del Operario: sus actividades en un horario por día, por semana o en lista.

const PANTALLA_ANGOSTA = window.matchMedia("(max-width: 50em)").matches;

let calendario = null;
let actividades = [];
let rango = null;

async function cargar() {
    if (!rango) {
        return;
    }
    const desde = fechaTexto(rango.start);
    const hasta = fechaTexto(sumarDias(rango.end, -1));    // "end" es el día siguiente al último visible.
    try {
        actividades = await pedirApi(`/actividades?fecha_desde=${desde}&fecha_hasta=${hasta}`);
        calendario.setOption("events", actividadesDelHorario(actividades).flatMap(actividadAEventos));
    } catch (error) {
        mostrarAviso(`No se pudieron cargar las actividades: ${error.message}`, "advertencia");
    }
}

// El horario va de una hora antes a una hora después del turno; si algo cae fuera, se amplía solo.
// Un turno que cruza la medianoche se ve completo, de 00:00 a 24:00.
async function rangoDelTurno() {
    try {
        const { turno } = await pedirApi("/programacion-del-dia");
        if (!turno) {
            return {};
        }
        const [hi] = turno.hora_inicio.split(":").map(Number);
        const [hf, mf] = turno.hora_fin.split(":").map(Number);
        if (hf * 60 + mf <= hi * 60) {
            return { slotMinTime: "00:00", slotMaxTime: "24:00" };
        }
        const desde = Math.max(0, hi - 1);
        const hasta = Math.min(24, hf + (mf ? 2 : 1));
        return { slotMinTime: `${String(desde).padStart(2, "0")}:00`, slotMaxTime: `${String(hasta).padStart(2, "0")}:00` };
    } catch {
        // Sin el turno, el horario usa su rango de siempre (de 06:00 a 20:00, ampliable).
        return {};
    }
}

iniciarPaginaProtegida(["OPERARIO"]).then(async () => {
    document.getElementById("controles").append(crearConmutadorColor());
    document.getElementById("leyenda").append(...crearLeyendas());
    // En computador la leyenda se ve abierta; en celular queda plegada para dejar ver el horario.
    document.getElementById("opciones-horario").open = !PANTALLA_ANGOSTA;
    const horasDelTurno = await rangoDelTurno();

    calendario = EventCalendar.create(document.getElementById("calendario"), opcionesCalendario({
        // En celular una semana completa no cabe: se empieza por el día.
        view: PANTALLA_ANGOSTA ? "timeGridDay" : "timeGridWeek",
        ...horasDelTurno,
        // El orden visual (título, Hoy, anterior y siguiente, vistas) lo pone estilos.css.
        headerToolbar: { start: "title", center: "", end: "today prev,next timeGridDay,timeGridWeek,listWeek" },
        datesSet: (info) => {
            rango = info;
            setTimeout(cargar);     // El primer aviso llega antes de que "calendario" quede asignado.
        },
        eventClick: (info) => abrirDetalleOperario(info.event.extendedProps.actividad, actividades, cargar),
    }));
});
