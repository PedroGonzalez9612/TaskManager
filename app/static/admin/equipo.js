// Vista "Equipo" del Administrador: el día de cada operario en columnas, con su carga de la jornada.
// Responde las tres preguntas del sistema: qué hay que hacer, quién lo hace y cuánto trabajo tiene.

const SIN_ASIGNAR = "sin-asignar";

let calendario = null;
let formulario = null;
let rango = null;
let actividades = [];
let operarios = [];
let requerimientos = [];
let cargas = {};        // id del operario -> { minutos, porcentaje, sobrecarga } del día visible

// Encabezado de cada columna: nombre del operario y su carga del día.
function etiquetaDeColumna(info) {
    const nombre = crearElemento("strong", "columna-nombre", info.resource.title);
    if (info.resource.id === SIN_ASIGNAR) {
        return { domNodes: [nombre] };
    }
    const jornada = cargas[info.resource.id] || { porcentaje: 0, sobrecarga: false };
    const carga = jornada.sobrecarga
        ? crearConIcono("span", "carga cifra carga-sobrecarga", "triangle-alert", `${jornada.porcentaje} %`)
        : crearElemento("span", "carga cifra", `${jornada.porcentaje} %`);
    carga.title = "Carga del día respecto a la jornada";
    return { domNodes: [nombre, carga] };
}

function columnas() {
    const lista = operarios.map((operario) => ({ id: operario.id, title: operario.nombre }));
    // Las actividades sin operario tienen su propia columna, para que no se pierdan de vista.
    if (actividades.some((actividad) => actividad.operarios.length === 0)) {
        lista.push({ id: SIN_ASIGNAR, title: "Sin asignar" });
    }
    return lista;
}

function pintarAvisoSobrecarga() {
    const aviso = document.getElementById("aviso-sobrecarga");
    const sobrecargados = operarios.filter((operario) => cargas[operario.id]?.sobrecarga);
    aviso.hidden = sobrecargados.length === 0;
    if (sobrecargados.length) {
        const detalle = sobrecargados.map((o) => `${o.nombre} (${cargas[o.id].porcentaje} %)`).join(", ");
        aviso.replaceChildren(crearConIcono("span", "", "triangle-alert",
            `Superan el 100 % de su jornada este día: ${detalle}.`));
    }
}

async function cargar() {
    if (!rango) {
        return;
    }
    const dia = fechaTexto(rango.start);
    try {
        const [lista, carga, listaRequerimientos] = await Promise.all([
            pedirApi(`/actividades?fecha_desde=${dia}&fecha_hasta=${dia}`),
            pedirApi(`/analisis/carga?desde=${dia}&hasta=${dia}`),
            pedirApi("/requerimientos"),
        ]);
        actividades = lista;
        requerimientos = listaRequerimientos;
        operarios = carga.operarios.map((operario) => ({ id: operario.id, nombre: operario.nombre }));
        cargas = Object.fromEntries(carga.operarios.map((operario) => [operario.id, operario.jornadas[0] || null]));

        calendario.setOption("resources", columnas());
        calendario.setOption("events", actividades.map((actividad) => {
            const evento = actividadAEvento(actividad, true);
            if (evento.resourceIds.length === 0) {
                evento.resourceIds = [SIN_ASIGNAR];
            }
            return evento;
        }));
        pintarAvisoSobrecarga();
    } catch (error) {
        mostrarAviso(`No se pudo cargar el equipo: ${error.message}`, "advertencia");
    }
}

iniciarPaginaProtegida(["ADMINISTRADOR"]).then(() => {
    document.getElementById("controles").append(crearConmutadorColor());
    document.getElementById("leyenda").append(...crearLeyendas());

    formulario = crearFormularioActividad({
        obtenerRequerimientos: () => requerimientos,
        obtenerOperarios: () => operarios,
        alGuardar: cargar,
    });

    calendario = EventCalendar.create(document.getElementById("calendario"), opcionesCalendario({
        view: "resourceTimeGridDay",
        headerToolbar: { start: "prev,next today", center: "title", end: "" },
        height: "40rem",
        resources: [],
        resourceLabelContent: etiquetaDeColumna,
        datesSet: (info) => {
            rango = info;
            setTimeout(cargar);     // El primer aviso llega antes de que "calendario" quede asignado.
        },
        eventClick: (info) => formulario.abrirEdicion(info.event.extendedProps.actividad),
        // Clic en un espacio libre: nueva actividad con esa fecha, esa hora y ese operario ya puestos.
        dateClick: (info) => formulario.abrirNueva({
            fecha_programada: fechaTexto(info.date),
            hora_programada: info.allDay ? "" : info.date.toTimeString().slice(0, 5),
            operario_ids: info.resource && info.resource.id !== SIN_ASIGNAR ? [info.resource.id] : [],
        }),
    }));

    document.getElementById("nueva-actividad").addEventListener("click", () =>
        formulario.abrirNueva({ fecha_programada: rango ? fechaTexto(rango.start) : fechaTexto(new Date()) }));
});
