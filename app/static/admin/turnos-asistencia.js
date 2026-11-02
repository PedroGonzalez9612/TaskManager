// Administrador, pantalla Usuarios: catálogo de turnos y asignación de turno a cada operario
// (alcance, Sección 5.1 "Turnos y asistencia"). La asistencia del día está en asistencia.js (Hoy).

let turnosDeLaEmpresa = [];

// ---------- Turnos ----------

function crearFilaTurno(turno) {
    const fila = crearElemento("li", "fila-turno");
    fila.append(
        crearElemento("span", "fila-nombre", turno.nombre),
        crearElemento("span", "fila-meta cifra",
            `${turno.hora_inicio} a ${turno.hora_fin}, descanso de ${duracionTexto(turno.descanso_min)}, capacidad de ${duracionTexto(turno.capacidad_min)}`),
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

// ---------- Conexión de los diálogos ----------

function configurarTurnos(recargar) {
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
}
