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

// ---------- Horario: lo que comparte el tablero de Equipo ----------

// Las canceladas no se dibujan en el horario: ya no son trabajo de nadie ni suman a la carga.
// Siguen en la vista Actividades del Administrador, con su motivo.
function actividadesDelHorario(actividades) {
    return actividades.filter((actividad) => actividad.estado !== "CANCELADA");
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

// ---------- Detalle de la actividad (Administrador; el del Operario está en operario-comun.js) ----------

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
