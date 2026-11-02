// Piezas compartidas para mostrar actividades: señales de prioridad y estado, el diálogo de detalle
// del Administrador, el registro de ejecución y la información por bloques. Las usan las vistas del
// Operario y del Administrador.

const ICONO_PRIORIDAD = { URGENTE: "triangle-alert", ALTA: "chevron-up", MEDIA: "circle-alert", BAJA: "minus" };
const ICONO_ESTADO = {
    PENDIENTE: "circle", ASIGNADA: "circle", EN_EJECUCION: "play", PAUSADA: "pause", DEVUELTA: "circle-alert",
    COMPLETADA: "check", NO_REALIZADA: "minus", CANCELADA: "minus",
};
const ICONO_CATEGORIA = {
    OPERACION: "briefcase",
    ATENCION: "message-circle",
    ADMINISTRATIVA: "file-text",
    REVISION: "search",
    TRASLADO: "truck",
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

// ---------- Estado y prioridad como texto (alcance, Sección 6.2: etiquetas solo para excepciones) ----------

const ICONO_ESTADO_TEXTO = {
    PENDIENTE: "circle", ASIGNADA: "circle", EN_EJECUCION: "circle", PAUSADA: "pause", DEVUELTA: "undo-2",
    COMPLETADA: "check", NO_REALIZADA: "minus", CANCELADA: "minus",
};

function crearEstadoComoTexto(estado, clase = "estado-texto") {
    return crearConIcono("span", `${clase} estado-op-${estado.toLowerCase()}`,
        ICONO_ESTADO_TEXTO[estado] || "circle", NOMBRE_ESTADO[estado] || estado);
}

function crearPrioridadComoTexto(prioridad) {
    return crearConIcono("span", `fila-prioridad prioridad-texto-${prioridad.toLowerCase()}`,
        ICONO_PRIORIDAD[prioridad], NOMBRE_PRIORIDAD[prioridad] || prioridad);
}

function textoRetraso(actividad) {
    const dias = actividad.dias_de_retraso;
    return dias === 1 ? "Retraso: 1 día" : `Retraso: ${dias} días`;
}

// Las únicas etiquetas: Urgente, Hora fija y Retraso. Una terminada ya no tiene excepciones que avisar.
function crearEtiquetasDeExcepcion(actividad, { conHora = false } = {}) {
    if (["COMPLETADA", "CANCELADA", "NO_REALIZADA"].includes(actividad.estado)) {
        return [];
    }
    const etiquetas = [];
    if (actividad.prioridad === "URGENTE") {
        etiquetas.push(crearSenalPrioridad("URGENTE"));
    }
    if (actividad.hora_programada) {
        etiquetas.push(crearConIcono("span", "etiqueta etiqueta-hora-fija", "lock",
            conHora ? `Hora fija ${actividad.hora_programada}` : "Hora fija"));
    }
    if (actividad.reprogramada) {
        etiquetas.push(crearConIcono("span", "etiqueta etiqueta-retraso", "clock", textoRetraso(actividad)));
    }
    return etiquetas;
}

// ---------- Orden y tiempos ----------

// Por fecha, luego por hora (las que no tienen hora van al final del día) y luego por prioridad.
function ordenarActividades(actividades) {
    return [...actividades].sort((a, b) =>
        a.fecha_programada.localeCompare(b.fecha_programada)
        || (a.hora_programada || "99:99").localeCompare(b.hora_programada || "99:99")
        || b.peso_prioridad - a.peso_prioridad);
}

function textoProgramada(actividad) {
    const fecha = fechaLarga(fechaDesdeTexto(actividad.fecha_programada));
    return actividad.hora_programada ? `${fecha}, ${actividad.hora_programada}` : `${fecha}, horario flexible`;
}

// ---------- Panel lateral del Administrador (alcance, Sección 6.2) ----------
// En computador va a la derecha y no tapa la lista ni el tablero; en celular ocupa toda la pantalla. Lo
// usan el detalle de una actividad y el de un proyecto. Uno a la vez: abrir otro reemplaza al anterior.
// "marca" es el texto pequeño de la barra (el código de la actividad); "volverA", el nombre de la
// pantalla de atrás (el botón para volver en celular); "alCerrar" avisa al cerrarse, para quitar la
// marca de la fila abierta.
let panelAbierto = null;
const MEDIA_CELULAR = "(max-width: 50em)";

function crearBarraDelPanel(panel, marca, enCelular, volverA) {
    const barra = crearElemento("div", "detalle-op-barra");
    const cerrar = crearElemento("button", "detalle-op-volver");
    cerrar.type = "button";
    cerrar.addEventListener("click", () => panel.close());
    const textoMarca = crearElemento("span", "codigo cifra texto-secundario", marca);
    if (enCelular) {
        cerrar.insertAdjacentHTML("afterbegin", icono("chevron-left"));
        cerrar.append(volverA);
        barra.append(cerrar, textoMarca);
    } else {
        cerrar.insertAdjacentHTML("afterbegin", icono("x"));
        cerrar.setAttribute("aria-label", "Cerrar el detalle");
        barra.append(textoMarca, cerrar);
    }
    return barra;
}

function crearAccionesDelPanel(panel, acciones, error) {
    const pie = crearElemento("div", "detalle-op-acciones");
    const fila = crearElemento("div", "detalle-op-acciones-fila");
    for (const accion of acciones) {
        const boton = crearElemento("button", accion.clase || "boton", accion.texto);
        boton.type = "button";
        boton.disabled = Boolean(accion.desactivada);
        boton.addEventListener("click", async () => {
            boton.disabled = true;
            try {
                await accion.alHacer();
                panel.close();
            } catch (error_) {
                mostrarErrorFormulario(error, error_.message);
                boton.disabled = false;
            }
        });
        fila.append(boton);
    }
    pie.append(fila);
    return pie;
}

function abrirPanelLateral({ marca = "", titulo, antesDelTitulo = [], contenido = [], acciones = [], volverA = "Volver", alCerrar = null }) {
    panelAbierto?.close();
    const enCelular = window.matchMedia(MEDIA_CELULAR).matches;
    const origen = document.activeElement;
    const panel = crearElemento("dialog", "dialogo panel-lateral");
    panel.setAttribute("aria-labelledby", "panel-lateral-titulo");

    const cuerpo = crearElemento("div", "detalle-op-cuerpo");
    const encabezado = crearElemento("h2", "detalle-op-titulo", titulo);
    encabezado.id = "panel-lateral-titulo";
    encabezado.tabIndex = -1;
    const error = crearElemento("p", "mensaje-formulario");
    error.setAttribute("role", "alert");
    error.hidden = true;
    cuerpo.append(...antesDelTitulo, encabezado, ...contenido, error);
    panel.append(crearBarraDelPanel(panel, marca, enCelular, volverA), cuerpo);
    if (acciones.length) {
        panel.append(crearAccionesDelPanel(panel, acciones, error));
    }

    // En computador el panel no es modal (no oscurece ni bloquea la lista), así que Escape se atiende aquí.
    const conEscape = (evento) => {
        if (evento.key === "Escape" && !document.querySelector("dialog[open]:not(.panel-lateral)")) {
            panel.close();
        }
    };
    panel.addEventListener("close", () => {
        document.removeEventListener("keydown", conEscape);
        panel.remove();
        if (panelAbierto === panel) {
            panelAbierto = null;
            document.body.classList.remove("con-panel-lateral");
        }
        alCerrar?.();
        if (origen?.isConnected && !panelAbierto) {
            origen.focus();
        }
    });
    document.body.append(panel);
    panelAbierto = panel;
    if (enCelular) {
        panel.showModal();
    } else {
        document.addEventListener("keydown", conEscape);
        document.body.classList.add("con-panel-lateral");
        panel.show();
    }
    encabezado.focus();
    return panel;
}

// ---------- Detalle de la actividad (Administrador; el del Operario está en operario-comun.js) ----------
// Mismo orden que el del Operario: estado y excepciones, nombre, datos, registro de cada operario e
// información; las acciones, fijas abajo.

function crearDatosDelPanel(actividad) {
    const datos = crearElemento("dl", "lista-datos");
    const filas = [
        ["Programada", textoProgramada(actividad)],
        ["Estimado", duracionTexto(actividad.tiempo_estimado_min)],
        ["Prioridad", crearPrioridadComoTexto(actividad.prioridad)],
        ["Asignada a", actividad.operarios.map((o) => o.nombre).join(", ") || "Nadie todavía"],
        ["Categoría", NOMBRE_CATEGORIA[actividad.categoria] || actividad.categoria],
        ["Ubicación", actividad.ubicacion],
        ["Proyecto", actividad.proyecto_nombre || "Actividad independiente"],
    ];
    for (const [nombre, valor] of filas) {
        const dd = crearElemento("dd");
        dd.append(valor);
        datos.append(crearElemento("dt", "", nombre), dd);
    }
    return datos;
}

function abrirDetalleActividad(actividad, { acciones = [], aviso = "", extra = [], volverA = "Volver", alCerrar = null } = {}) {
    const estado = crearElemento("div", "detalle-op-estado");
    estado.append(crearEstadoComoTexto(actividad.estado, "detalle-op-estado-texto"), ...crearEtiquetasDeExcepcion(actividad));
    const contenido = [];
    if (actividad.descripcion) {
        contenido.push(crearElemento("p", "detalle-op-descripcion", actividad.descripcion));
    }
    contenido.push(crearDatosDelPanel(actividad), ...extra, ...crearInformacion(actividad));
    if (aviso) {
        contenido.push(crearConIcono("p", "linea-info", "info", aviso));
    }
    return abrirPanelLateral({
        marca: actividad.codigo, titulo: actividad.titulo, antesDelTitulo: [estado], contenido, acciones, volverA, alCerrar,
    });
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
    // Retraso de inicio: una de hora fija que se inició después de su hora (alcance, Sección 5.1).
    if (ejecucion.retraso_inicio_min) {
        filas.push(["Retraso de inicio", duracionTexto(ejecucion.retraso_inicio_min)]);
    }
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
