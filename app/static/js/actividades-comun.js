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

// Las canceladas no se dibujan en el horario: ya no son trabajo de nadie ni suman a la carga.
// Siguen en la vista Actividades del Administrador, con su motivo.
function actividadesDelHorario(actividades) {
    return actividades.filter((actividad) => actividad.estado !== "CANCELADA");
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

// Los ratos que de verdad trabajó: del inicio al fin (o a ahora), sin las pausas.
function segmentosTrabajados(ejecucion) {
    const fin = ejecucion.fecha_fin ? new Date(ejecucion.fecha_fin) : new Date();
    const pausas = (ejecucion.pausas || [])
        .map((pausa) => [new Date(pausa.inicio), pausa.fin ? new Date(pausa.fin) : fin])
        .sort((a, b) => a[0] - b[0]);
    const segmentos = [];
    let desde = new Date(ejecucion.fecha_inicio);
    for (const [inicioPausa, finPausa] of pausas) {
        if (inicioPausa > desde) {
            segmentos.push([desde, inicioPausa]);
        }
        desde = new Date(Math.max(desde, finPausa));
    }
    if (fin > desde) {
        segmentos.push([desde, fin]);
    }
    return segmentos;
}

function crearEvento(actividad, estado, id, inicio, fin) {
    const todoElDia = !inicio;
    const desde = inicio || fechaDesdeTexto(actividad.fecha_programada);
    const hasta = todoElDia ? desde : new Date(Math.max(fin.getTime(), desde.getTime() + DURACION_MINIMA_BLOQUE_MIN * 60000));
    return {
        id,
        start: desde,
        end: hasta,
        allDay: todoElDia,
        title: actividad.titulo,
        classNames: [
            "bloque",
            todoElDia ? "bloque-flexible" : claseDeAlto((hasta - desde) / 60000),
            `bloque-prioridad-${actividad.prioridad.toLowerCase()}`,
            `bloque-categoria-${String(actividad.categoria).toLowerCase()}`,
            `bloque-estado-${estado.toLowerCase()}`,
        ],
        extendedProps: { actividad, estado },
    };
}

// Los eventos del calendario de una actividad del Operario. Lo trabajado ocupa sus horas reales y sin
// las pausas, así que una actividad que se pausó se ve en varios bloques, cada uno en su día. Lo que
// le falta va en su hora fija o, si es de horario flexible, en la fila "Flexible" de su día.
function actividadAEventos(actividad) {
    const ejecucion = actividad.ejecucion;
    const eventos = [];
    const segmentos = ejecucion?.fecha_inicio ? segmentosTrabajados(ejecucion) : [];
    segmentos.forEach(([inicio, fin], indice) => {
        const ultimo = indice === segmentos.length - 1;
        const enCurso = ultimo && ejecucion.estado === "EN_PROGRESO";
        // Lo que está en curso se dibuja hasta su fin proyectado: ahora más lo que le falta.
        const faltaMs = Math.max(0, actividad.tiempo_estimado_min - ejecucion.tiempo_real_min) * 60000;
        const hasta = enCurso ? new Date(Date.now() + faltaMs) : fin;
        let estado = "PAUSADA";
        if (ejecucion.estado === "FINALIZADA") {
            estado = "COMPLETADA";
        } else if (enCurso) {
            estado = "EN_EJECUCION";
        }
        eventos.push(crearEvento(actividad, estado, `${actividad.id}-${indice}`, inicio, hasta));
    });

    const terminada = ["COMPLETADA", "NO_REALIZADA"].includes(actividad.estado) || ejecucion?.estado === "FINALIZADA";
    const enCurso = ejecucion?.estado === "EN_PROGRESO";
    if (!terminada && !enCurso) {
        const falta = Math.max(0, actividad.tiempo_estimado_min - (ejecucion?.tiempo_real_min || 0)) * 60000;
        if (actividad.hora_programada && !ejecucion) {
            const inicio = fechaDesdeTexto(actividad.fecha_programada, actividad.hora_programada);
            eventos.push(crearEvento(actividad, actividad.estado, `${actividad.id}-pendiente`, inicio, new Date(inicio.getTime() + falta)));
        } else {
            eventos.push(crearEvento(actividad, actividad.estado, `${actividad.id}-pendiente`, null, null));
        }
    } else if (actividad.estado === "NO_REALIZADA" && !segmentos.length) {
        const inicio = actividad.hora_programada ? fechaDesdeTexto(actividad.fecha_programada, actividad.hora_programada) : null;
        eventos.push(crearEvento(actividad, actividad.estado, `${actividad.id}-pendiente`, inicio,
            inicio ? new Date(inicio.getTime() + actividad.tiempo_estimado_min * 60000) : null));
    }
    return eventos;
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
    titulo.title = [textoEstado, actividad.titulo, actividad.codigo, actividad.ubicacion].filter(Boolean).join(", ");

    const detalle = crearElemento("span", "bloque-detalle datos-linea");
    if (textoEstado) {
        detalle.append(crearElemento("span", "bloque-estado", textoEstado));
    }
    detalle.append(crearElemento("span", "codigo", actividad.codigo), crearElemento("span", "", actividad.ubicacion));

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
// "extra" son elementos que cada rol agrega al detalle (por ejemplo, el registro del Operario).
function abrirDetalleActividad(actividad, { acciones = [], aviso = "", extra = [] } = {}) {
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
        ["Proyecto", actividad.proyecto_nombre || "Actividad independiente", false],
    ];
    for (const [nombre, valor, esCifra] of filas) {
        datos.append(crearElemento("dt", "", nombre), crearElemento("dd", esCifra ? "cifra" : "", valor));
    }
    cuerpo.append(datos);
    if (actividad.descripcion) {
        cuerpo.append(crearElemento("h3", "detalle-subtitulo", "Descripción de la actividad"),
            crearElemento("p", "detalle-descripcion", actividad.descripcion));
    }
    cuerpo.append(...crearInformacion(actividad), ...extra);
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

// ---------- Motivos: lista de la empresa más "Otro" (alcance, Sección 5.1) ----------

const OPCION_OTRO = "Otro";

// Pide la lista de motivos y arma sus campos. Lo escrito en "Otro" queda en la lista de la empresa.
// Devuelve { campos, leer } o lanza el error de la consulta.
async function crearSelectorMotivo(rutaLista, idBase) {
    const motivos = await pedirApi(rutaLista);
    const etiqueta = crearElemento("label", "", "Motivo");
    etiqueta.htmlFor = `${idBase}-motivo`;
    const selector = crearElemento("select");
    selector.id = `${idBase}-motivo`;
    const vacia = crearElemento("option", "", "Elige el motivo");
    vacia.value = "";
    selector.append(vacia, ...motivos.map((motivo) => {
        const opcion = crearElemento("option", "", motivo);
        opcion.value = motivo;
        return opcion;
    }));

    const etiquetaOtro = crearElemento("label", "", "¿Cuál es el motivo?");
    etiquetaOtro.htmlFor = `${idBase}-otro`;
    const otro = crearElemento("input");
    otro.id = `${idBase}-otro`;
    otro.maxLength = 120;
    const mostrarOtro = () => {
        etiquetaOtro.hidden = otro.hidden = selector.value !== OPCION_OTRO;
    };
    selector.addEventListener("change", () => {
        mostrarOtro();
        if (!otro.hidden) {
            otro.focus();
        }
    });
    mostrarOtro();

    const leer = () => {
        if (!selector.value) {
            throw new Error("Elige el motivo.");
        }
        return { motivo: selector.value, detalle: otro.value };
    };
    return { campos: [etiqueta, selector, etiquetaOtro, otro], leer };
}

// ---------- Registro de la ejecución: la constancia de lo que hizo el operario ----------

// "14:05" si es de hoy; "13 oct, 14:05" si es de otro día.
function horaCorta(momento) {
    const fecha = new Date(momento);
    const hora = `${String(fecha.getHours()).padStart(2, "0")}:${String(fecha.getMinutes()).padStart(2, "0")}`;
    if (fechaTexto(fecha) === fechaTexto(new Date())) {
        return hora;
    }
    return `${fecha.toLocaleDateString("es-CO", { day: "numeric", month: "short" }).replace(".", "")}, ${hora}`;
}

function minutosEntre(inicio, fin) {
    return Math.max(0, Math.round((new Date(fin) - new Date(inicio)) / 60000));
}

// Su inicio, su tiempo trabajado, cada pausa con su motivo y la observación final. "titulo" es
// "Tu registro" para el Operario o el nombre de la persona para el Administrador.
function crearRegistroEjecucion(ejecucion, titulo = "Tu registro", textoObservacion = "Tu observación") {
    if (!ejecucion) {
        return [];
    }
    const datos = crearElemento("dl", "detalle-datos");
    const filas = [["Inicio", horaCorta(ejecucion.fecha_inicio)]];
    if (ejecucion.fecha_fin) {
        filas.push(["Fin", horaCorta(ejecucion.fecha_fin)]);
    }
    filas.push(["Tiempo trabajado", duracionTexto(ejecucion.tiempo_real_min)]);
    for (const [nombre, valor] of filas) {
        datos.append(crearElemento("dt", "", nombre), crearElemento("dd", "cifra", valor));
    }
    const nodos = [crearElemento("h3", "detalle-subtitulo", titulo), datos];

    const pausas = ejecucion.pausas || [];
    if (pausas.length) {
        const lista = crearElemento("ul", "lista-pausas");
        for (const pausa of pausas) {
            // Arriba las horas y cuánto duró; debajo, el motivo.
            // El fin lleva fecha solo si es de otro día que el inicio.
            let fin = "ahora";
            if (pausa.fin) {
                const mismoDia = fechaTexto(new Date(pausa.inicio)) === fechaTexto(new Date(pausa.fin));
                fin = mismoDia ? horaCorta(pausa.fin).split(", ").at(-1) : horaCorta(pausa.fin);
            }
            const duracion = duracionTexto(minutosEntre(pausa.inicio, pausa.fin || Date.now()));
            const textos = crearElemento("span", "lista-pausas-textos");
            textos.append(
                crearElemento("span", "cifra", `${horaCorta(pausa.inicio)} a ${fin} (${duracion})`),
                crearElemento("span", "texto-suave", pausa.motivo),
            );
            const fila = crearConIcono("li", "", "pause", "");
            fila.append(textos);
            lista.append(fila);
        }
        nodos.push(crearElemento("h3", "detalle-subtitulo", pausas.length === 1 ? "1 pausa" : `${pausas.length} pausas`), lista);
    }
    if (ejecucion.observacion) {
        nodos.push(crearElemento("h3", "detalle-subtitulo", textoObservacion),
            crearElemento("p", "detalle-descripcion", ejecucion.observacion));
    }
    nodos.push(...crearEvidencias(ejecucion));
    return nodos;
}

// Fotos en miniatura y documentos como enlaces; cada uno se abre aparte, en tamaño completo. Sirve
// para la evidencia del operario y para los adjuntos de la información de la actividad.
function crearArchivos(archivos, rutaBase) {
    const fotos = crearElemento("div", "evidencia-fotos");
    const documentos = crearElemento("ul", "evidencia-adjuntos");
    for (const archivo of archivos) {
        const enlace = crearElemento("a");
        enlace.href = `${rutaBase}/${archivo.id}`;
        enlace.target = "_blank";
        enlace.rel = "noopener";
        if (archivo.tipo === "FOTO") {
            const imagen = crearElemento("img");
            imagen.src = enlace.href;
            imagen.alt = `Foto: ${archivo.nombre}`;
            imagen.loading = "lazy";
            enlace.append(imagen);
            fotos.append(enlace);
        } else {
            enlace.append(...crearConIcono("span", "", "paperclip", archivo.nombre).childNodes);
            const fila = crearElemento("li");
            fila.append(enlace);
            documentos.append(fila);
        }
    }
    return [fotos, documentos].filter((grupo) => grupo.childElementCount);
}

function crearEvidencias(ejecucion) {
    const evidencias = ejecucion.evidencias || [];
    if (!evidencias.length) {
        return [];
    }
    const titulo = evidencias.length === 1 ? "1 archivo de evidencia" : `${evidencias.length} archivos de evidencia`;
    return [crearElemento("h3", "detalle-subtitulo", titulo),
        ...crearArchivos(evidencias, `/actividades/${ejecucion.actividad_id}/evidencias`)];
}

// ---------- Información de la actividad (alcance, Sección 5.1) ----------

// Los bloques en el orden en que se muestran. "sugerencias" es la lista de la empresa que los
// completa (GET /catalogos/informacion/<sugerencias>); los pasos se escriben uno por renglón.
const BLOQUES_INFORMACION = [
    { clave: "PASOS", campo: "pasos", nombre: "Pasos" },
    { clave: "HERRAMIENTAS", campo: "herramientas", nombre: "Herramientas y materiales", sugerencias: "herramientas",
        ejemplo: "Llave de 13 mm" },
    { clave: "EQUIPO", campo: "equipo", nombre: "Equipo", sugerencias: "equipo", ejemplo: "Selladora de la línea 2" },
    { clave: "PRECAUCIONES", campo: "precauciones", nombre: "Precauciones de seguridad", sugerencias: "precauciones",
        ejemplo: "Bloquear y etiquetar la máquina" },
    { clave: "CONTACTO", campo: "contacto", nombre: "Contacto", sugerencias: "contacto",
        ejemplo: "Jorge Ruiz, jefe de planta, ext. 204" },
    { clave: "ADJUNTOS", nombre: "Adjuntos" },
];
const NOMBRE_BLOQUE = Object.fromEntries(BLOQUES_INFORMACION.map((bloque) => [bloque.clave, bloque.nombre]));

// Lo que no está listo se dice con los nombres de los bloques: "Falta información: Contacto y Adjuntos".
function textoFaltaInformacion(actividad) {
    const nombres = (actividad.bloques_faltantes || []).map((clave) => NOMBRE_BLOQUE[clave].toLowerCase());
    const lista = nombres.length > 1 ? `${nombres.slice(0, -1).join(", ")} y ${nombres.at(-1)}` : nombres[0];
    return `Falta información: ${lista}.`;
}

function crearEtiquetaFaltaInformacion(actividad) {
    const etiqueta = crearConIcono("span", "etiqueta etiqueta-falta-informacion", "circle-alert", "Falta información");
    etiqueta.title = textoFaltaInformacion(actividad);
    return etiqueta;
}

// Los pasos en una lista numerada (son una secuencia); los demás bloques, en una lista simple.
function crearListaDeBloque(bloque, valores) {
    const lista = crearElemento(bloque.clave === "PASOS" ? "ol" : "ul",
        bloque.clave === "PRECAUCIONES" ? "lista-informacion lista-precauciones" : "lista-informacion");
    lista.append(...valores.map((valor) => (bloque.clave === "PRECAUCIONES"
        ? crearConIcono("li", "", "triangle-alert", valor)
        : crearElemento("li", "", valor))));
    return lista;
}

function crearInformacion(actividad) {
    const informacion = actividad.informacion || { bloques: [] };
    if (!informacion.bloques.length) {
        return [];
    }
    const nodos = [crearElemento("h3", "detalle-subtitulo detalle-subtitulo-seccion", "Para hacer el trabajo")];
    if (!actividad.lista_para_iniciar) {
        nodos.push(crearConIcono("p", "aviso aviso-advertencia", "circle-alert", textoFaltaInformacion(actividad)));
    }
    for (const bloque of BLOQUES_INFORMACION.filter((b) => informacion.bloques.includes(b.clave))) {
        const valores = bloque.campo ? informacion[bloque.campo] : informacion.adjuntos;
        nodos.push(crearElemento("h4", "detalle-bloque", bloque.nombre));
        if (!valores.length) {
            nodos.push(crearElemento("p", "texto-suave", "Sin completar."));
        } else if (bloque.campo) {
            nodos.push(crearListaDeBloque(bloque, valores));
        } else {
            nodos.push(...crearArchivos(valores, `/actividades/${actividad.id}/adjuntos`));
        }
    }
    return nodos;
}

// Para el Administrador: el registro de cada operario que ya inició la actividad.
function crearRegistrosDelEquipo(actividad) {
    const ejecuciones = actividad.ejecuciones || [];
    if (!ejecuciones.length) {
        return [crearElemento("h3", "detalle-subtitulo", "Registro de los operarios"),
            crearElemento("p", "texto-suave", "Ningún operario la ha iniciado todavía.")];
    }
    return ejecuciones.flatMap((ejecucion) =>
        crearRegistroEjecucion(ejecucion, `Registro de ${ejecucion.operario_nombre}`, "Observación"));
}

aplicarModoColor();
