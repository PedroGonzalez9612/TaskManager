// Asistencia del día (alcance, Sección 5.1): la presencia de cada operario y la revisión de sus marcas,
// que el Administrador valida o corrige. La usa la pestaña Asistencia de Hoy.

// La revisión de las marcas (alcance, Sección 5.1). Si la persona vino es otra cosa: su presencia.
const NOMBRE_REVISION = { REGISTRADA: "Por validar", VALIDADA: "Validada", CORREGIDA: "Corregida" };
const ICONO_REVISION = { REGISTRADA: "clock", VALIDADA: "check", CORREGIDA: "pencil" };

function horaDeMomento(momento) {
    if (!momento) {
        return "—";
    }
    const fecha = new Date(momento);
    return `${String(fecha.getHours()).padStart(2, "0")}:${String(fecha.getMinutes()).padStart(2, "0")}`;
}

function crearFilaAsistencia(asistencia) {
    const fila = crearElemento("li", "fila-asistencia");
    const textos = crearElemento("div");
    const meta = crearElemento("span", "fila-meta datos-linea cifra");
    if (asistencia.turno) {
        meta.append(crearElemento("span", "", `Turno ${asistencia.turno.hora_inicio} a ${asistencia.turno.hora_fin}`));
    }
    meta.append(
        crearElemento("span", "", `Entrada ${horaDeMomento(asistencia.entrada)}`),
        crearElemento("span", "", `Salida ${horaDeMomento(asistencia.salida)}`),
    );
    textos.append(crearElemento("span", "fila-nombre", asistencia.operario), meta);
    // La presencia (con la salida anticipada en su texto) y, si hay marcas, su revisión: texto con ícono.
    const { presencia } = asistencia;
    const estado = crearElemento("div", "asistencia-estados");
    estado.append(crearConIcono("span", `presencia ${TONO_PRESENCIA[presencia.estado] || ""}`,
        ICONO_PRESENCIA[presencia.estado], textoDePresencia(presencia, asistencia.turno)));
    if (asistencia.estado && asistencia.salida) {
        estado.append(crearConIcono("span", "texto-secundario", ICONO_REVISION[asistencia.estado],
            NOMBRE_REVISION[asistencia.estado]));
    }
    const acciones = crearElemento("div", "fila-acciones");
    if (asistencia.id && asistencia.salida && asistencia.estado === "REGISTRADA") {
        const validar = crearElemento("button", "boton-texto", "Validar");
        validar.type = "button";
        validar.addEventListener("click", () => validarAsistencia(validar, asistencia));
        acciones.append(validar);
    }
    if (asistencia.id) {
        const corregir = crearElemento("button", "boton-texto", "Corregir");
        corregir.type = "button";
        corregir.addEventListener("click", () => abrirCorregir(asistencia));
        acciones.append(corregir);
    }
    fila.append(textos, estado, acciones);
    return fila;
}

async function cargarAsistencia() {
    const asistencias = await pedirApi("/asistencias");
    document.getElementById("lista-asistencia").replaceChildren(...asistencias.map(crearFilaAsistencia));
    document.getElementById("asistencia-vacia").hidden = asistencias.length > 0;
}

async function validarAsistencia(boton, asistencia) {
    boton.disabled = true;
    try {
        await pedirApi(`/asistencias/${encodeURIComponent(asistencia.id)}/validar`, { method: "POST" });
        await cargarAsistencia();
        mostrarAviso(`Asistencia de ${asistencia.operario} validada.`);
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        boton.disabled = false;
    }
}

function abrirCorregir(asistencia) {
    const dialogo = document.getElementById("dialogo-corregir");
    dialogo.querySelector('input[name="asistencia_id"]').value = asistencia.id;
    dialogo.querySelector('input[name="entrada"]').value = asistencia.entrada ? horaDeMomento(asistencia.entrada) : "";
    dialogo.querySelector('input[name="salida"]').value = asistencia.salida ? horaDeMomento(asistencia.salida) : "";
    dialogo.querySelector("h2").textContent = `Corregir asistencia de ${asistencia.operario}`;
    dialogo.showModal();
    dialogo.querySelector('input[name="entrada"]').focus();
}

function validarCorreccion(datos) {
    if (!datos.entrada || !datos.motivo.trim()) {
        return "Indica la hora de entrada y el motivo de la corrección.";
    }
    return null;
}

// El diálogo de corrección está en la página; aquí se conecta su envío.
function configurarAsistencia() {
    const dialogoCorregir = document.getElementById("dialogo-corregir");
    configurarDialogo([], dialogoCorregir);
    dialogoCorregir.querySelector("form").addEventListener("submit", (evento) => {
        evento.preventDefault();
        enviarFormularioDialogo(dialogoCorregir, validarCorreccion, async (datos) => {
            await enviarJson(`/asistencias/${encodeURIComponent(datos.asistencia_id)}/corregir`, "POST",
                { entrada: datos.entrada, salida: datos.salida || null, motivo: datos.motivo });
            await cargarAsistencia();
            return "Asistencia corregida.";
        });
    });
}
