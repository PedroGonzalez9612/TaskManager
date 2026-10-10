// Piezas compartidas para mostrar actividades: señales de prioridad y estado, el diálogo de detalle
// y la configuración del calendario. Las usan las vistas del Operario y del Administrador.

const ICONO_PRIORIDAD = { URGENTE: "triangle-alert", ALTA: "chevron-up", MEDIA: "circle-alert", BAJA: "minus" };
const ICONO_ESTADO = {
    PENDIENTE: "circle", ASIGNADA: "circle", EN_EJECUCION: "play", PAUSADA: "pause", DEVUELTA: "circle-alert",
    COMPLETADA: "check", NO_REALIZADA: "minus", CANCELADA: "minus",
};
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
    return actividad.hora_programada ? `${fecha}, ${actividad.hora_programada}` : `${fecha}, horario flexible`;
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

// Un bloque nunca se dibuja más bajo que esto, aunque la ejecución real haya durado menos: por debajo
// no cabe ni una línea de texto ni se puede tocar. Solo cambia el dibujo; el tiempo registrado no.
const DURACION_MINIMA_BLOQUE_MIN = 20;

// Estados que se escriben dentro del bloque. Por iniciar y Sin asignar son lo normal y no llevan texto.
const ESTADOS_CON_TEXTO = new Set(["EN_EJECUCION", "PAUSADA", "DEVUELTA", "COMPLETADA", "NO_REALIZADA"]);

// Lo que ya terminó cambia el ícono de prioridad por el de su estado: la prioridad ya no importa.
const ICONO_ESTADO_FINAL = { COMPLETADA: "check", NO_REALIZADA: "minus" };

// Estado de la actividad para UN operario, según su propia ejecución (tablero del Administrador, donde
// cada columna es una persona). Los estados finales de la actividad valen para todos.
const ESTADO_SEGUN_EJECUCION = { EN_PROGRESO: "EN_EJECUCION", PAUSADA: "PAUSADA", FINALIZADA: "COMPLETADA" };

function estadoDelOperario(actividad, operario) {
    if (["NO_REALIZADA", "CANCELADA"].includes(actividad.estado)) {
        return actividad.estado;
    }
    return ESTADO_SEGUN_EJECUCION[operario.estado_ejecucion] || "ASIGNADA";
}

// Las canceladas no se dibujan en el horario: ya no son trabajo de nadie ni suman a la carga.
// Siguen en la vista Actividades del Administrador, con su motivo.
function actividadesDelHorario(actividades) {
    return actividades.filter((actividad) => actividad.estado !== "CANCELADA");
}

// Dónde va el bloque, según la programación dinámica del día (alcance, Sección 5.1): lo ejecutado ocupa
// sus horas reales; lo que está en curso o pausado va de su inicio real a su fin proyectado (ahora más lo
// que le falta del estimado); lo que no ha empezado, de su hora programada más el estimado. Las horas
// reales las pone el servidor; "ahora" solo sirve para dibujar la proyección. Devuelve null si la
// actividad es de horario flexible y no ha empezado: va en la fila "Flexible".
function horarioDelBloque(actividad, ejecucion) {
    const inicioReal = ejecucion?.fecha_inicio ? new Date(ejecucion.fecha_inicio) : null;
    if (inicioReal && ejecucion.fecha_fin) {
        return { inicio: inicioReal, fin: new Date(ejecucion.fecha_fin) };
    }
    const faltaMs = Math.max(0, actividad.tiempo_estimado_min - (ejecucion ? ejecucion.tiempo_real_min : 0)) * 60000;
    // Si empezó en un día anterior (se reprogramó), hoy se muestra solo lo que le falta, como pendiente.
    if (inicioReal && inicioReal >= fechaDesdeTexto(actividad.fecha_programada)) {
        return { inicio: inicioReal, fin: new Date(Date.now() + faltaMs) };
    }
    if (!actividad.hora_programada) {
        return null;
    }
    const inicio = fechaDesdeTexto(actividad.fecha_programada, actividad.hora_programada);
    return { inicio, fin: new Date(inicio.getTime() + faltaMs) };
}

// Clase según el alto del bloque, para mostrar solo lo que cabe sin cortar renglones a la mitad:
// corto (menos de 45 min), solo el título en una línea; medio (menos de 1 h), título y código en
// una línea cada uno; largo, título en dos líneas y código. Los cortes salen del alto de la franja
// (--alto-franja-horario, 2rem por cada 30 min) y del tamaño de letra de los bloques (13 px).
function claseDeAlto(minutos) {
    if (minutos < 45) {
        return "bloque-corto";
    }
    return minutos < 60 ? "bloque-medio" : "bloque-largo";
}

// Convierte una actividad en un evento del calendario. Con "operario" el bloque va en la columna de esa
// persona, con sus horas y su estado; sin él, con la ejecución y el estado que entrega la API.
function actividadAEvento(actividad, operario = null) {
    const ejecucion = operario
        ? (actividad.ejecuciones || []).find((propia) => propia.usuario_id === operario.id)
        : actividad.ejecucion;
    const estado = operario ? estadoDelOperario(actividad, operario) : actividad.estado;
    const horario = horarioDelBloque(actividad, ejecucion);

    let inicio = fechaDesdeTexto(actividad.fecha_programada);
    let fin = inicio;
    if (horario) {
        inicio = horario.inicio;
        fin = new Date(Math.max(horario.fin.getTime(), inicio.getTime() + DURACION_MINIMA_BLOQUE_MIN * 60000));
    }
    return {
        id: operario ? `${actividad.id}-${operario.id}` : actividad.id,
        start: inicio,
        end: fin,
        allDay: !horario,
        resourceIds: operario ? [operario.id] : [],
        title: actividad.titulo,
        classNames: [
            "bloque",
            horario ? claseDeAlto((fin - inicio) / 60000) : "bloque-flexible",
            `bloque-prioridad-${actividad.prioridad.toLowerCase()}`,
            `bloque-categoria-${String(actividad.categoria).toLowerCase()}`,
            `bloque-estado-${estado.toLowerCase()}`,
        ],
        extendedProps: { actividad, estado },
    };
}

// Contenido de cada bloque: ícono y título; debajo, el estado (si no es el normal), el código y el lugar.
// En la vista de lista va además la hora, porque el contenido propio reemplaza el de la biblioteca.
// Se arma con nodos (no con HTML de texto).
function contenidoBloque(info) {
    const { actividad, estado } = info.event.extendedProps;
    const textoEstado = ESTADOS_CON_TEXTO.has(estado) ? NOMBRE_ESTADO[estado] : "";

    const titulo = crearConIcono(
        "strong", "bloque-titulo", ICONO_ESTADO_FINAL[estado] || ICONO_PRIORIDAD[actividad.prioridad], actividad.titulo,
    );
    // En un bloque corto solo se ve el título: el resto queda en la descripción emergente.
    titulo.title = [textoEstado, actividad.titulo, actividad.codigo, actividad.ubicacion].filter(Boolean).join(" · ");

    const detalle = crearElemento("span", "bloque-detalle");
    if (textoEstado) {
        detalle.append(crearElemento("span", "bloque-estado", textoEstado), " · ");
    }
    detalle.append(crearElemento("span", "codigo", actividad.codigo), ` · ${actividad.ubicacion}`);

    const nodos = [titulo, detalle];
    if (info.view?.type.startsWith("list")) {
        nodos.unshift(crearElemento("span", "bloque-hora cifra", info.event.allDay ? "Flexible" : info.timeText));
    }
    return { domNodes: nodos };
}

// Alto de una franja de 30 minutos, en píxeles, a partir de la variable en rem de estilos.css. Así el
// horario crece con el tamaño de letra que el usuario tenga en su navegador.
function altoFranjaPx() {
    const estilos = getComputedStyle(document.documentElement);
    const rem = Number.parseFloat(estilos.getPropertyValue("--alto-franja-horario")) || 2;
    return Math.round(rem * Number.parseFloat(estilos.fontSize));
}

// Opciones comunes a todos los calendarios de la aplicación. Sin alto fijo: el horario crece con su
// contenido y se recorre con el desplazamiento de la página, sin una barra interna.
function opcionesCalendario(extra) {
    return {
        locale: "es-CO",
        firstDay: 1,
        nowIndicator: true,
        slotMinTime: "06:00",
        slotMaxTime: "20:00",
        flexibleSlotTimeLimits: true,       // Si una actividad cae fuera de 06:00-20:00, el rango se amplía.
        slotDuration: "00:30",
        slotHeight: altoFranjaPx(),
        allDayContent: "Flexible",
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
        cuerpo.append(crearElemento("h3", "detalle-subtitulo", "Descripción de la actividad"),
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
                } catch (error_) {
                    mostrarErrorFormulario(error, error_.message);
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
