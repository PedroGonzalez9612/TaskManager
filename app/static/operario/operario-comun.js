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
// "alCambiar" recarga la vista después de iniciar o finalizar.
function abrirDetalleOperario(actividad, actividades, alCambiar) {
    const enCurso = actividadEnCurso(actividades);
    const acciones = [];
    let aviso = "";

    if (actividad.estado === "ASIGNADA") {
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
