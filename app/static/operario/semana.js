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
        calendario.setOption("events", actividadesDelHorario(actividades).map((actividad) => actividadAEvento(actividad)));
    } catch (error) {
        mostrarAviso(`No se pudieron cargar las actividades: ${error.message}`, "advertencia");
    }
}

iniciarPaginaProtegida(["OPERARIO"]).then(() => {
    document.getElementById("controles").append(crearConmutadorColor());
    document.getElementById("leyenda").append(...crearLeyendas());

    calendario = EventCalendar.create(document.getElementById("calendario"), opcionesCalendario({
        // En celular una semana completa no cabe: se empieza por el día.
        view: PANTALLA_ANGOSTA ? "timeGridDay" : "timeGridWeek",
        // El orden visual (título, Hoy, anterior y siguiente, vistas) lo pone estilos.css.
        headerToolbar: { start: "title", center: "", end: "today prev,next timeGridDay,timeGridWeek,listWeek" },
        datesSet: (info) => {
            rango = info;
            setTimeout(cargar);     // El primer aviso llega antes de que "calendario" quede asignado.
        },
        eventClick: (info) => abrirDetalleOperario(info.event.extendedProps.actividad, actividades, cargar),
    }));
});
