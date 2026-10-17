// Lo que comparten las vistas del Operario: abrir el detalle de una actividad con las acciones
// que él puede hacer (iniciar, reanudar, pausar o finalizar), y las ventanas para pausar con un
// motivo y para finalizar con una observación (alcance, Secciones 5.1 y 6.1).

const MOTIVO_URGENTE = "Actividad urgente";

// Evidencia de la ejecución (alcance, Sección 5.1).
const MAXIMO_EVIDENCIAS = 5;
const TAMANO_MAXIMO_EVIDENCIA = 5 * 1024 * 1024;
const LADO_MAXIMO_FOTO = 1600;      // Píxeles del lado mayor: la foto se lee bien y pesa unos 300 KB.
const CALIDAD_FOTO = 0.8;

function actividadEnCurso(actividades) {
    return actividades.find((actividad) => actividad.estado === "EN_EJECUCION") || null;
}

// "actividades" es la lista completa del operario (para saber si ya tiene otra en curso) y
// "alCambiar" recarga la vista después de iniciar o finalizar. Con "soloLectura" (Hoy sin la entrada
// marcada o después de la salida) se ve la información, sin acciones.
function abrirDetalleOperario(actividad, actividades, alCambiar, { soloLectura = false } = {}) {
    const enCurso = actividadEnCurso(actividades);
    const acciones = [];
    let aviso = "";

    if (soloLectura) {
        if (["ASIGNADA", "PAUSADA"].includes(actividad.estado)) {
            aviso = "Para iniciarla o reanudarla, marca la entrada en Inicio.";
        }
    } else if (actividad.estado === "ASIGNADA") {
        // Una sola actividad en ejecución a la vez: el botón se desactiva y se explica por qué.
        const bloqueada = enCurso && enCurso.id !== actividad.id;
        if (bloqueada) {
            aviso = `Ya tienes una actividad en curso (${enCurso.codigo}). Páusala o finalízala antes de iniciar esta.`;
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
    } else if (actividad.estado === "PAUSADA") {
        // Quedó pausada (por ejemplo, al terminar la jornada): se retoma donde iba.
        const bloqueada = enCurso && enCurso.id !== actividad.id;
        if (bloqueada) {
            aviso = `Ya tienes una actividad en curso (${enCurso.codigo}). Páusala o finalízala antes de reanudar esta.`;
        }
        acciones.push({
            texto: "Reanudar actividad",
            desactivada: bloqueada,
            alHacer: async () => {
                await pedirApi(`/actividades/${actividad.id}/reanudar`, { method: "POST" });
                await alCambiar();
                mostrarAviso(`${actividad.codigo} reanudada.`);
            },
        });
    } else if (actividad.estado === "EN_EJECUCION") {
        // Una de hora fija no se pausa (alcance, Sección 5.1).
        if (!actividad.hora_programada) {
            acciones.push({ texto: "Pausar", clase: "boton-secundario", alHacer: () => abrirPausar(actividad, alCambiar) });
        }
        acciones.push({ texto: "Finalizar actividad", alHacer: () => abrirFinalizar(actividad, alCambiar) });
    }
    abrirDetalleActividad(actividad, { acciones, aviso, extra: crearRegistroEjecucion(actividad.ejecucion) });
}

// ---------- Ventanas para pausar y finalizar ----------

function textoActividad(actividad) {
    return `${actividad.titulo} (${actividad.codigo})`;
}

// Pausar: el motivo sale de la lista de la empresa; con "Otro" se escribe y queda en la lista.
async function abrirPausar(actividad, alCambiar) {
    let motivo;
    try {
        motivo = await crearSelectorMotivo("/catalogos/motivos-pausa", "pausa");
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        return;
    }
    abrirDialogoAccion({
        titulo: "Pausar actividad",
        subtitulo: textoActividad(actividad),
        campos: [...motivo.campos,
            crearElemento("p", "ayuda-campo", "El tiempo se detiene mientras esté en pausa. La retomas con \"Reanudar\".")],
        textoConfirmar: "Pausar",
        iconoConfirmar: "pause",
        alConfirmar: async () => {
            await enviarJson(`/actividades/${actividad.id}/pausar`, "POST", motivo.leer());
            await alCambiar();
            mostrarAviso(`${actividad.codigo} quedó en pausa.`);
        },
    });
}

// Reduce una foto en el celular antes de subirla, para no gastar datos. Devuelve un JPG.
async function reducirFoto(archivo) {
    let imagen;
    try {
        imagen = await createImageBitmap(archivo);
    } catch (error) {
        throw new Error(`No se pudo leer la foto "${archivo.name}". Usa una foto JPG o PNG.`);
    }
    const escala = Math.min(1, LADO_MAXIMO_FOTO / Math.max(imagen.width, imagen.height));
    const lienzo = document.createElement("canvas");
    lienzo.width = Math.round(imagen.width * escala);
    lienzo.height = Math.round(imagen.height * escala);
    lienzo.getContext("2d").drawImage(imagen, 0, 0, lienzo.width, lienzo.height);
    const reducida = await new Promise((resolver) => lienzo.toBlob(resolver, "image/jpeg", CALIDAD_FOTO));
    return { contenido: reducida, nombre: archivo.name.replace(/\.[^.]+$/, "") + ".jpg" };
}

async function subirEvidencia(actividad, archivo) {
    const { contenido, nombre } = archivo.type.startsWith("image/")
        ? await reducirFoto(archivo)
        : { contenido: archivo, nombre: archivo.name };
    if (contenido.size > TAMANO_MAXIMO_EVIDENCIA) {
        throw new Error(`"${archivo.name}" pesa más de 5 MB.`);
    }
    const datos = new FormData();
    datos.append("archivo", contenido, nombre);
    await pedirApi(`/actividades/${actividad.id}/evidencias`, { method: "POST", body: datos });
}

function crearSelectorArchivos(id, texto, aceptar, icono_) {
    const etiqueta = crearConIcono("label", "etiqueta-archivos", icono_, texto);
    etiqueta.htmlFor = id;
    const entrada = crearElemento("input");
    entrada.id = id;
    entrada.type = "file";
    entrada.accept = aceptar;
    entrada.multiple = true;
    return { etiqueta, entrada };
}

// Finalizar: la evidencia es opcional: una observación, fotos y adjuntos (PDF o imágenes).
// Primero se suben los archivos y después se finaliza, porque la evidencia se agrega con la
// actividad todavía en curso.
function abrirFinalizar(actividad, alCambiar) {
    const etiqueta = crearElemento("label", "", "Observación (opcional)");
    etiqueta.htmlFor = "finalizar-observacion";
    const observacion = crearElemento("textarea");
    observacion.id = "finalizar-observacion";
    observacion.rows = 3;
    observacion.maxLength = 500;

    const fotos = crearSelectorArchivos("finalizar-fotos", "Fotos (opcional)", "image/*", "camera");
    const adjuntos = crearSelectorArchivos("finalizar-adjuntos", "Adjuntos (opcional)", "application/pdf,image/*", "paperclip");
    const elegidos = crearElemento("ul", "evidencia-elegida");
    elegidos.setAttribute("aria-live", "polite");
    const archivos = () => [...fotos.entrada.files, ...adjuntos.entrada.files];
    const pintarElegidos = () => elegidos.replaceChildren(...archivos().map((archivo) =>
        crearConIcono("li", "", archivo.type.startsWith("image/") ? "camera" : "paperclip", archivo.name)));
    fotos.entrada.addEventListener("change", pintarElegidos);
    adjuntos.entrada.addEventListener("change", pintarElegidos);

    abrirDialogoAccion({
        titulo: "Finalizar actividad",
        subtitulo: textoActividad(actividad),
        campos: [etiqueta, observacion,
            crearElemento("p", "ayuda-campo", "Lo que hiciste, lo que encontraste o lo que quedó por hacer."),
            fotos.etiqueta, fotos.entrada, adjuntos.etiqueta, adjuntos.entrada, elegidos,
            crearElemento("p", "ayuda-campo", `Hasta ${MAXIMO_EVIDENCIAS} archivos: fotos o PDF de 5 MB como máximo. Las fotos se reducen antes de subirlas.`)],
        textoConfirmar: "Finalizar",
        iconoConfirmar: "check",
        alConfirmar: async () => {
            const lista = archivos();
            if (lista.length > MAXIMO_EVIDENCIAS) {
                throw new Error(`Elige como máximo ${MAXIMO_EVIDENCIAS} archivos.`);
            }
            for (const archivo of lista) {
                await subirEvidencia(actividad, archivo);
            }
            await enviarJson(`/actividades/${actividad.id}/finalizar`, "POST", { observacion: observacion.value });
            await alCambiar();
            mostrarAviso(lista.length ? `${actividad.codigo} finalizada, con ${lista.length} de evidencia.` : `${actividad.codigo} finalizada.`);
        },
    });
}

// ---------- La jornada: lo que comparten Inicio y Hoy (alcance, Secciones 5.1 y 6.1) ----------

const MOTIVO_FIN_JORNADA = "Fin de jornada";
const AVISO_TURNO_MIN = 15;     // Desde cuántos minutos antes se avisa el inicio y el fin del turno.
const MINUTO_MS = 60000;

// "inicio" antes de marcar la entrada, "dia" con la entrada marcada y "cierre" después de la salida.
// Una asistencia de otra jornada que quedó sin salida no cuenta: hoy se marca una entrada nueva.
function estadoDeJornada(programacion) {
    const { asistencia, fecha } = programacion;
    if (!asistencia || asistencia.jornada !== fecha) {
        return "inicio";
    }
    return asistencia.salida ? "cierre" : "dia";
}

function horaDeMomento(momento) {
    const fecha = new Date(momento);
    return `${String(fecha.getHours()).padStart(2, "0")}:${String(fecha.getMinutes()).padStart(2, "0")}`;
}

function minutosHasta(momento) {
    return Math.ceil((new Date(momento).getTime() - Date.now()) / MINUTO_MS);
}

// Una frase corta sobre el turno, debajo de la hora: no repite el horario, que va en la barra.
function textoEstadoTurno(programacion) {
    const { turno, asistencia } = programacion;
    if (estadoDeJornada(programacion) === "cierre") {
        return `Marcaste la salida a las ${horaDeMomento(asistencia.salida)}`;
    }
    if (!turno) {
        return "Sin turno asignado";
    }
    if (minutosHasta(turno.inicio) > 0) {
        return `Tu turno empieza a las ${turno.hora_inicio}`;
    }
    const faltan = minutosHasta(turno.fin);
    return faltan > 0 ? `En turno: faltan ${duracionTexto(faltan)}` : `Tu turno terminó a las ${turno.hora_fin}`;
}

// ---------- La cinta del día: el elemento firma de GestLab (dirección visual "Cinta del día") ----------
// Una sola cinta reúne el tiempo, la carga y lo que hay que hacer: el marco es el turno, cada
// actividad es un segmento con el color de su categoría en su hora, la aguja marca la hora actual y
// lo que no cabe sale del marco rayado en coral. Debajo, las mismas cifras en texto (la cinta no
// depende solo del color: alcance, Sección 6.3, regla 1).

function momentoMs(momento) {
    return new Date(momento).getTime();
}

// La ventana que dibuja la cinta: del inicio del turno (o de la primera actividad) hasta lo más
// tarde entre el fin del turno, la última actividad y la hora actual.
function ventanaDeLaCinta(programacion) {
    const { turno, tramos } = programacion;
    const ahora = Date.now();
    const inicios = tramos.map((tramo) => momentoMs(tramo.inicio));
    const fines = tramos.map((tramo) => momentoMs(tramo.fin));
    const desde = turno ? Math.min(momentoMs(turno.inicio), ...inicios) : Math.min(ahora, ...inicios);
    let hasta = Math.max(ahora, ...fines);
    if (turno) {
        const fin = momentoMs(turno.fin);
        hasta = Math.max(hasta, fin);
        // Si algo pasa del turno, el desborde ocupa al menos una cuarta parte: se ve y cabe su cifra.
        if (hasta > fin) {
            hasta = Math.max(hasta, desde + (fin - desde) / 0.75);
        }
    } else {
        hasta = Math.max(hasta, desde + 60 * MINUTO_MS);
    }
    return { desde, hasta };
}

function crearSegmentosDeLaCinta(programacion, posicion) {
    const porId = new Map(programacion.actividades.map((actividad) => [actividad.id, actividad]));
    return programacion.tramos.filter((tramo) => porId.has(tramo.actividad_id)).map((tramo) => {
        const actividad = porId.get(tramo.actividad_id);
        const tipo = { FINALIZADA: "hecho", EN_CURSO: "curso" }[tramo.tipo] || "pendiente";
        const clases = ["cinta-segmento", `cinta-${tipo}`, `bloque-cat-${String(actividad.categoria).toLowerCase()}`];
        if (actividad.prioridad === "URGENTE" && tipo === "pendiente") {
            clases.push("cinta-urgente");
        }
        const segmento = crearElemento("span", clases.join(" "));
        const inicio = posicion(momentoMs(tramo.inicio));
        segmento.style.left = `${inicio}%`;
        // Una actividad muy corta igual se ve: como mínimo un trazo.
        segmento.style.width = `max(3px, ${Math.max(0, posicion(momentoMs(tramo.fin)) - inicio)}%)`;
        return segmento;
    });
}

function crearCintaDelDia(programacion) {
    const { turno, resumen } = programacion;
    const { desde, hasta } = ventanaDeLaCinta(programacion);
    const posicion = (ms) => Math.min(100, Math.max(0, ((ms - desde) * 100) / (hasta - desde)));
    const finTurno = turno ? posicion(momentoMs(turno.fin)) : 100;

    const contenedor = crearElemento("section", "cinta-dia");
    contenedor.setAttribute("aria-label", "Tu jornada");

    const cabeza = crearElemento("div", "cinta-cabeza");
    const hora = crearElemento("p", "cinta-hora cifra-firma");
    const estado = crearElemento("p", "cinta-estado");
    cabeza.append(hora, estado);

    // La cinta es un dibujo: lo que dice está también en texto, debajo.
    const cinta = crearElemento("div", "cinta");
    cinta.setAttribute("aria-hidden", "true");
    const marco = crearElemento("span", "cinta-marco");
    marco.style.width = `${finTurno}%`;
    cinta.append(marco);
    if (turno && finTurno < 100) {
        const desborde = crearElemento("span", "cinta-desborde");
        desborde.style.left = `${finTurno}%`;
        cinta.append(desborde);
    }
    cinta.append(...crearSegmentosDeLaCinta(programacion, posicion));
    const aguja = crearElemento("span", "cinta-aguja");
    cinta.append(aguja);

    const escala = crearElemento("div", "cinta-escala cifra");
    escala.setAttribute("aria-hidden", "true");
    if (turno) {
        const inicioTurno = crearElemento("span", "cinta-escala-inicio", turno.hora_inicio);
        const finDelTurno = crearElemento("span", "cinta-escala-fin", turno.hora_fin);
        finDelTurno.style.left = `${finTurno}%`;
        escala.append(inicioTurno, finDelTurno);
        if (resumen.fuera_del_turno_min > 0) {
            const desborde = crearElemento("span", "cinta-escala-desborde", `+${duracionTexto(resumen.fuera_del_turno_min)}`);
            desborde.style.left = `${finTurno}%`;
            escala.append(desborde);
        }
    }

    // La carga en cifras: lo programado frente a lo que cabe, grande; el detalle, en la leyenda.
    const { trabajado_min: trabajado, pendiente_min: pendiente, capacidad_min: capacidad } = resumen;
    const exceso = Math.max(0, trabajado + pendiente - capacidad);
    const total = crearElemento("p", "cinta-total");
    total.append(crearElemento("strong", "cifra-firma", duracionTexto(trabajado + pendiente)),
        crearElemento("span", "", ` de ${duracionTexto(capacidad)} programadas`));
    const dato = (clase, nombre, minutos) => {
        const fila = crearElemento("li", clase);
        fila.append(crearElemento("span", "", nombre), crearElemento("strong", "cifra", duracionTexto(minutos)));
        return fila;
    };
    const leyenda = crearElemento("ul", "barra-leyenda");
    leyenda.append(
        dato("leyenda-trabajado", "Trabajado", trabajado),
        dato("leyenda-por-hacer", "Por hacer", pendiente),
        exceso ? dato("leyenda-exceso", "Se pasa", exceso) : dato("leyenda-libre", "Libre", capacidad - trabajado - pendiente),
    );

    contenedor.append(cabeza, cinta, escala, total, leyenda);
    if (exceso) {
        contenedor.append(crearConIcono("p", "barra-jornada-aviso", "triangle-alert",
            `Tu trabajo programado pasa ${duracionTexto(exceso)} de tu jornada. Infórmalo a tu administrador.`));
    }

    function actualizar() {
        hora.textContent = horaDeMomento(Date.now());
        estado.textContent = textoEstadoTurno(programacion);
        aguja.style.left = `${posicion(Date.now())}%`;
    }
    actualizar();
    return { elemento: contenedor, actualizar };
}

// Avisos del turno: la llegada tarde (alcance, Sección 5.1) y los 15 minutos antes del inicio y del
// fin. Devuelve [tipo, texto] o null.
function avisoDelTurno(programacion) {
    const { turno } = programacion;
    const estado = estadoDeJornada(programacion);
    if (!turno || estado === "cierre") {
        return null;
    }
    if (estado === "inicio" && programacion.retraso_entrada_min > 0) {
        return ["advertencia", `Tu turno empezó hace ${duracionTexto(programacion.retraso_entrada_min)} y no has marcado la entrada.`];
    }
    const faltan = minutosHasta(estado === "inicio" ? turno.inicio : turno.fin);
    if (faltan > 0 && faltan <= AVISO_TURNO_MIN) {
        return ["info", `${estado === "inicio" ? "Tu turno inicia en" : "Tu turno termina en"} ${duracionTexto(faltan)}.`];
    }
    return null;
}

function pintarAvisoDelTurno(elemento, programacion) {
    const aviso = avisoDelTurno(programacion);
    elemento.hidden = !aviso;
    if (aviso) {
        const [tipo, texto] = aviso;
        elemento.className = `aviso aviso-${tipo}`;
        elemento.replaceChildren(...crearConIcono("span", "", tipo === "info" ? "info" : "circle-alert", texto).childNodes);
    }
}

async function marcarAsistencia(boton, ruta, texto, alCambiar) {
    boton.disabled = true;
    try {
        await pedirApi(ruta, { method: "POST" });
        mostrarAviso(texto);
        await alCambiar();
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        boton.disabled = false;
    }
}

// Marcar salida (alcance, Sección 5.1): con una actividad en curso no se marca la salida; la de horario
// flexible se pausa con el motivo "Fin de jornada" y la de hora fija, que no se pausa, se finaliza.
// Todo en el mismo paso.
function abrirSalida(programacion, alCambiar) {
    const tramo = programacion.tramos.find((t) => t.tipo === "EN_CURSO");
    const enCurso = tramo ? programacion.actividades.find((a) => a.id === tramo.actividad_id) : null;
    const esFija = Boolean(enCurso?.hora_programada);

    const campos = [];
    if (enCurso) {
        campos.push(crearConIcono("p", "aviso aviso-advertencia aviso-bloque", "circle-alert", esFija
            ? `Tienes ${enCurso.codigo} en curso. Es de hora fija y no se pausa: se finaliza antes de marcar la salida.`
            : `Tienes ${enCurso.codigo} en curso. Se pausa con el motivo "${MOTIVO_FIN_JORNADA}" y la retomas en tu siguiente jornada.`));
    }
    campos.push(crearElemento("p", "portada-nota",
        "Después de marcar la salida no podrás iniciar ni reanudar actividades en esta jornada."));

    let textoConfirmar = "Marcar salida";
    if (enCurso) {
        textoConfirmar = esFija ? "Finalizar y marcar salida" : "Pausar y marcar salida";
    }
    abrirDialogoAccion({
        titulo: "Marcar salida",
        campos,
        textoConfirmar,
        iconoConfirmar: "log-out",
        alConfirmar: async () => {
            try {
                if (enCurso && esFija) {
                    await pedirApi(`/actividades/${enCurso.id}/finalizar`, { method: "POST" });
                } else if (enCurso) {
                    await enviarJson(`/actividades/${enCurso.id}/pausar`, "POST", { motivo: MOTIVO_FIN_JORNADA });
                }
                await pedirApi("/asistencia/salida", { method: "POST" });
            } catch (error) {
                alCambiar();    // Si alcanzó a pausar o finalizar, la pantalla debe mostrarlo.
                throw error;
            }
            await alCambiar();
            mostrarAviso("Salida registrada.");
        },
    });
}
