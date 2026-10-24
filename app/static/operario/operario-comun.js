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
    } else if (actividad.prioridad === "URGENTE" && enCurso && enCurso.id !== actividad.id
        && ["ASIGNADA", "PAUSADA"].includes(actividad.estado)) {
        // Urgente con otra en curso (alcance, Sección 5.1): una de horario flexible se pausa y la
        // urgente empieza en el mismo paso; una de hora fija no se interrumpe.
        if (enCurso.hora_programada) {
            aviso = `${enCurso.codigo} es de hora fija y no se interrumpe. Atiende la urgente al finalizarla.`;
        } else {
            acciones.push({
                texto: "Pausar y atender",
                alHacer: () => atenderUrgente(actividad, enCurso, alCambiar),
            });
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

// Pausa lo que está en curso con el motivo "Actividad urgente" e inicia (o reanuda) la urgente.
// Son dos pasos en el servidor: si el segundo falla, lo primero ya quedó en pausa y se recarga.
async function atenderUrgente(urgente, enCurso, alCambiar) {
    try {
        await enviarJson(`/actividades/${enCurso.id}/pausar`, "POST", { motivo: MOTIVO_URGENTE });
        const accion = urgente.estado === "PAUSADA" ? "reanudar" : "iniciar";
        await pedirApi(`/actividades/${urgente.id}/${accion}`, { method: "POST" });
    } catch (error) {
        alCambiar();
        throw error;
    }
    await alCambiar();
    mostrarAviso(`${enCurso.codigo} quedó en pausa. ${urgente.codigo} en curso.`);
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
