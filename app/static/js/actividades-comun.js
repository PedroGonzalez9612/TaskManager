// Piezas compartidas para mostrar actividades: señales de prioridad y estado, el diálogo de detalle
// y la configuración del calendario. Las usan las vistas del Operario y del Administrador.

const ICONO_PRIORIDAD = { URGENTE: "triangle-alert", ALTA: "chevron-up", MEDIA: "circle-alert", BAJA: "minus" };
const ICONO_ESTADO = { PENDIENTE: "circle", ASIGNADA: "circle", EN_EJECUCION: "play", COMPLETADA: "check" };
const ICONO_CATEGORIA = {
    PRODUCCION: "factory",
    MANTENIMIENTO: "wrench",
    CALIDAD: "clipboard-check",
    LIMPIEZA: "sparkles",
    LOGISTICA: "truck",
};

// ---------- Señales: siempre color + ícono + texto (alcance, Sección 6.3, regla 1) ----------

function crearSenalPrioridad(prioridad) {
    return crearConIcono(
        "span", `etiqueta prioridad-${prioridad.toLowerCase()}`,
        ICONO_PRIORIDAD[prioridad], NOMBRE_PRIORIDAD[prioridad] || prioridad,
    );
}

function crearEtiquetaEstado(estado) {
    return crearConIcono(
        "span", `etiqueta estado-${estado.toLowerCase()}`,
        ICONO_ESTADO[estado], NOMBRE_ESTADO[estado] || estado,
    );
}

function crearEtiquetaCategoria(categoria) {
    return crearConIcono(
        "span", `etiqueta categoria categoria-${String(categoria).toLowerCase()}`,
        ICONO_CATEGORIA[categoria], NOMBRE_CATEGORIA[categoria] || categoria,
    );
}

// ---------- Orden y tiempos ----------

// Por fecha, luego por hora (las que no tienen hora van al final del día) y luego por prioridad.
function ordenarActividades(actividades) {
    return [...actividades].sort((a, b) =>
        a.fecha_programada.localeCompare(b.fecha_programada)
        || (a.hora_programada || "99:99").localeCompare(b.hora_programada || "99:99")
        || b.peso_prioridad - a.peso_prioridad);
}

// Tiempo transcurrido desde una fecha, como "01:07:42" (para el cronómetro).
function tiempoTranscurrido(desde) {
    const segundos = Math.max(0, Math.floor((Date.now() - new Date(desde).getTime()) / 1000));
    const partes = [Math.floor(segundos / 3600), Math.floor((segundos % 3600) / 60), segundos % 60];
    return partes.map((parte) => String(parte).padStart(2, "0")).join(":");
}

function textoProgramada(actividad) {
    const fecha = fechaLarga(fechaDesdeTexto(actividad.fecha_programada));
    return actividad.hora_programada ? `${fecha}, ${actividad.hora_programada}` : `${fecha}, sin hora fija`;
}

// ---------- Color de los bloques del calendario: por prioridad o por categoría ----------

const CLAVE_MODO_COLOR = "gestlab-color-bloques";

function modoColor() {
    return localStorage.getItem(CLAVE_MODO_COLOR) === "categoria" ? "categoria" : "prioridad";
}

function aplicarModoColor() {
    document.documentElement.dataset.colorBloques = modoColor();
}

// Control de dos opciones para elegir cómo se colorean los bloques. Recuerda la elección en el navegador.
function crearConmutadorColor() {
    const grupo = crearElemento("div", "conmutador");
    grupo.setAttribute("role", "group");
    grupo.setAttribute("aria-label", "Color de los bloques");
    grupo.append(crearElemento("span", "conmutador-titulo", "Color por"));

    for (const [modo, texto] of [["prioridad", "Prioridad"], ["categoria", "Categoría"]]) {
        const boton = crearElemento("button", "", texto);
        boton.type = "button";
        boton.setAttribute("aria-pressed", String(modoColor() === modo));
        boton.addEventListener("click", () => {
            localStorage.setItem(CLAVE_MODO_COLOR, modo);
            aplicarModoColor();
            for (const otro of grupo.querySelectorAll("button")) {
                otro.setAttribute("aria-pressed", String(otro === boton));
            }
        });
        grupo.append(boton);
    }
    return grupo;
}

// Leyendas de los dos modos de color. El CSS muestra solo la del modo activo.
function crearLeyendas() {
    const prioridades = crearElemento("div", "leyenda-grupo leyenda-prioridad");
    prioridades.append(...Object.keys(PESO_PRIORIDAD).map(crearSenalPrioridad));
    const categorias = crearElemento("div", "leyenda-grupo leyenda-categoria");
    categorias.append(...Object.keys(NOMBRE_CATEGORIA).map(crearEtiquetaCategoria));
    return [prioridades, categorias];
}

// ---------- Calendario (EventCalendar) ----------

// Convierte una actividad en un evento del calendario. Con hora ocupa su franja; sin hora va arriba,
// en la fila de "todo el día". "porOperario" la ubica en la columna de cada operario asignado.
function actividadAEvento(actividad, porOperario = false) {
    const inicio = fechaDesdeTexto(actividad.fecha_programada, actividad.hora_programada || "00:00");
    const fin = new Date(inicio.getTime() + (actividad.hora_programada ? actividad.tiempo_estimado_min : 0) * 60000);
    return {
        id: actividad.id,
        start: inicio,
        end: fin,
        allDay: !actividad.hora_programada,
        resourceIds: porOperario ? actividad.operarios.map((operario) => operario.id) : [],
        title: actividad.titulo,
        classNames: [
            "bloque",
            `bloque-prioridad-${actividad.prioridad.toLowerCase()}`,
            `bloque-categoria-${String(actividad.categoria).toLowerCase()}`,
            `bloque-estado-${actividad.estado.toLowerCase()}`,
        ],
        extendedProps: { actividad },
    };
}

// Contenido de cada bloque: ícono de prioridad, título y código. Se arma con nodos (no con HTML de texto).
function contenidoBloque(info) {
    const actividad = info.event.extendedProps.actividad;
    const titulo = crearConIcono("strong", "bloque-titulo", ICONO_PRIORIDAD[actividad.prioridad], actividad.titulo);
    const detalle = crearElemento("span", "bloque-detalle cifra", actividad.codigo);
    detalle.append(crearElemento("span", "bloque-lugar", ` · ${actividad.ubicacion}`));
    return { domNodes: [titulo, detalle] };
}

// Opciones comunes a todos los calendarios de la aplicación.
function opcionesCalendario(extra) {
    return {
        locale: "es-CO",
        firstDay: 1,
        nowIndicator: true,
        slotMinTime: "06:00",
        slotMaxTime: "20:00",
        flexibleSlotTimeLimits: true,
        slotDuration: "00:30",
        scrollTime: "06:00",
        allDayContent: "Sin hora",
        // Horas en formato de 24 horas, como se escriben en los turnos de planta.
        slotLabelFormat: { hour: "2-digit", minute: "2-digit", hourCycle: "h23" },
        eventTimeFormat: { hour: "2-digit", minute: "2-digit", hourCycle: "h23" },
        eventContent: contenidoBloque,
        buttonText: {
            today: "Hoy",
            timeGridDay: "Día",
            timeGridWeek: "Semana",
            listWeek: "Lista",
            resourceTimeGridDay: "Día",
            resourceTimeGridWeek: "Semana",
        },
        noEventsContent: "No hay actividades programadas en estas fechas.",
        ...extra,
    };
}

// ---------- Diálogo de detalle de una actividad ----------

// Abre el detalle. "acciones" es una lista de { texto, clase, alHacer, desactivada }; alHacer puede ser
// asíncrona y, si falla, su mensaje se muestra dentro del diálogo. "aviso" es un texto de advertencia.
function abrirDetalleActividad(actividad, { acciones = [], aviso = "" } = {}) {
    const dialogo = crearElemento("dialog", "dialogo dialogo-detalle");

    const encabezado = crearElemento("div", "dialogo-encabezado");
    encabezado.append(crearElemento("span", "codigo cifra", actividad.codigo));
    const cerrar = crearElemento("button", "boton-cerrar", "×");
    cerrar.type = "button";
    cerrar.setAttribute("aria-label", "Cerrar");
    cerrar.addEventListener("click", () => dialogo.close());
    encabezado.append(cerrar);

    const cuerpo = crearElemento("div", "detalle-cuerpo");
    const senales = crearElemento("div", "senales");
    senales.append(
        crearSenalPrioridad(actividad.prioridad),
        crearEtiquetaEstado(actividad.estado),
        crearEtiquetaCategoria(actividad.categoria),
    );
    cuerpo.append(senales, crearElemento("h2", "detalle-titulo", actividad.titulo));

    const datos = crearElemento("dl", "detalle-datos");
    const filas = [
        ["Ubicación", actividad.ubicacion, false],
        ["Programada", textoProgramada(actividad), false],
        ["Estimado", duracionTexto(actividad.tiempo_estimado_min), true],
        ["Asignada a", actividad.operarios.map((o) => o.nombre).join(", ") || "Nadie todavía", false],
    ];
    for (const [nombre, valor, esCifra] of filas) {
        datos.append(crearElemento("dt", "", nombre), crearElemento("dd", esCifra ? "cifra" : "", valor));
    }
    cuerpo.append(datos);
    if (actividad.descripcion) {
        cuerpo.append(crearElemento("h3", "detalle-subtitulo", "Qué hay que hacer"),
            crearElemento("p", "detalle-descripcion", actividad.descripcion));
    }
    if (aviso) {
        cuerpo.append(crearConIcono("p", "aviso aviso-advertencia", "circle-alert", aviso));
    }

    const error = crearElemento("p", "mensaje-formulario");
    error.setAttribute("role", "alert");
    error.hidden = true;
    cuerpo.append(error);

    if (acciones.length) {
        const botones = crearElemento("div", "dialogo-acciones");
        for (const accion of acciones) {
            const boton = crearElemento("button", accion.clase || "boton", accion.texto);
            boton.type = "button";
            boton.disabled = Boolean(accion.desactivada);
            boton.addEventListener("click", async () => {
                boton.disabled = true;
                try {
                    await accion.alHacer();
                    dialogo.close();
                } catch (fallo) {
                    mostrarErrorFormulario(error, fallo.message);
                    boton.disabled = false;
                }
            });
            botones.append(boton);
        }
        cuerpo.append(botones);
    }

    dialogo.append(encabezado, cuerpo);
    dialogo.addEventListener("close", () => dialogo.remove());
    document.body.append(dialogo);
    dialogo.showModal();
    return dialogo;
}

aplicarModoColor();
