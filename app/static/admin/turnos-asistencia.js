// Administrador, pantalla Usuarios: catálogo de turnos, asignación de turno a cada operario y
// asistencia del día (validar o corregir las marcas). Alcance, Sección 5.1 "Turnos y asistencia".

let turnosDeLaEmpresa = [];

const NOMBRE_ESTADO_ASISTENCIA = {
    REGISTRADA: "Por validar",
    VALIDADA: "Validada",
    CORREGIDA: "Corregida",
    SIN_MARCA: "Sin marca",
};

function horaDeMomento(momento) {
    if (!momento) {
        return "—";
    }
    const fecha = new Date(momento);
    return `${String(fecha.getHours()).padStart(2, "0")}:${String(fecha.getMinutes()).padStart(2, "0")}`;
}

// ---------- Turnos ----------

function crearFilaTurno(turno) {
    const fila = crearElemento("li", "fila-turno");
    fila.append(
        crearElemento("span", "fila-nombre", turno.nombre),
        crearElemento("span", "fila-meta cifra",
            `${turno.hora_inicio} a ${turno.hora_fin} · descanso ${duracionTexto(turno.descanso_min)} · capacidad ${duracionTexto(turno.capacidad_min)}`),
    );
    return fila;
}

async function cargarTurnos() {
    turnosDeLaEmpresa = await pedirApi("/turnos");
    document.getElementById("lista-turnos").replaceChildren(...turnosDeLaEmpresa.map(crearFilaTurno));
    document.getElementById("turnos-vacio").hidden = turnosDeLaEmpresa.length > 0;
}

function validarTurno(datos) {
    if (!datos.nombre.trim() || !datos.hora_inicio || !datos.hora_fin) {
        return "Completa nombre, hora de inicio y hora de fin.";
    }
    return null;
}

function abrirAsignarTurno(operario) {
    const dialogo = document.getElementById("dialogo-asignar-turno");
    if (turnosDeLaEmpresa.length === 0) {
        mostrarAviso("Primero crea un turno en el panel Turnos.", "advertencia");
        return;
    }
    const selector = dialogo.querySelector('select[name="turno_id"]');
    selector.replaceChildren(...turnosDeLaEmpresa.map((turno) => {
        const opcion = crearElemento("option", "", `${turno.nombre} (${turno.hora_inicio} a ${turno.hora_fin})`);
        opcion.value = turno.id;
        return opcion;
    }));
    if (operario.turno) {
        selector.value = operario.turno.id;
    }
    dialogo.querySelector('input[name="operario_id"]').value = operario.id;
    const desde = dialogo.querySelector('input[name="desde"]');
    desde.value = fechaTexto(new Date());
    desde.min = desde.value;
    dialogo.querySelector("h2").textContent = `Turno de ${operario.nombre}`;
    dialogo.showModal();
    selector.focus();
}

// ---------- Asistencia de hoy ----------

function crearFilaAsistencia(asistencia) {
    const fila = crearElemento("li", "fila-asistencia");
    const textos = crearElemento("div");
    const turno = asistencia.turno ? `Turno ${asistencia.turno.hora_inicio} a ${asistencia.turno.hora_fin} · ` : "";
    textos.append(
        crearElemento("span", "fila-nombre", asistencia.operario),
        crearElemento("span", "fila-meta cifra",
            `${turno}Entrada ${horaDeMomento(asistencia.entrada)} · Salida ${horaDeMomento(asistencia.salida)}`),
    );
    const estado = crearElemento("span", `etiqueta asistencia-${asistencia.estado.toLowerCase()}`,
        NOMBRE_ESTADO_ASISTENCIA[asistencia.estado] || asistencia.estado);
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

// ---------- Conexión de los diálogos ----------

function configurarTurnosYAsistencia(recargar) {
    const dialogoTurno = document.getElementById("dialogo-turno");
    configurarDialogo([document.getElementById("nuevo-turno")], dialogoTurno);
    dialogoTurno.querySelector("form").addEventListener("submit", (evento) => {
        evento.preventDefault();
        enviarFormularioDialogo(dialogoTurno, validarTurno, async (datos) => {
            const turno = await enviarJson("/turnos", "POST", { ...datos, descanso_min: Number(datos.descanso_min || 0) });
            await cargarTurnos();
            return `Turno "${turno.nombre}" creado.`;
        });
    });

    const dialogoAsignar = document.getElementById("dialogo-asignar-turno");
    configurarDialogo([], dialogoAsignar);
    dialogoAsignar.querySelector("form").addEventListener("submit", (evento) => {
        evento.preventDefault();
        enviarFormularioDialogo(dialogoAsignar, () => null, async (datos) => {
            await enviarJson(`/usuarios/${encodeURIComponent(datos.operario_id)}/turno`, "PUT",
                { turno_id: datos.turno_id, desde: datos.desde });
            await recargar();
            return "Turno asignado.";
        });
    });

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
