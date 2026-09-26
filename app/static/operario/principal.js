// Pantalla principal del Operario: lista de sus actividades ordenada por prioridad.

async function cargarActividades(usuarioId) {
    const asignaciones = await pedirApi(`/asignaciones?usuario_id=${encodeURIComponent(usuarioId)}`);
    const actividades = await Promise.all(
        asignaciones.map((asignacion) => pedirApi(`/actividades/${asignacion.actividad_id}`))
    );

    return actividades
        .filter((actividad) => actividad.estado !== "COMPLETADA")
        .sort((a, b) => (PESO_PRIORIDAD[b.prioridad] || 0) - (PESO_PRIORIDAD[a.prioridad] || 0));
}

function crearTarjeta(actividad) {
    const prioridad = actividad.prioridad || "BAJA";

    const elemento = document.createElement("li");
    const enlace = document.createElement("a");
    enlace.className = `tarjeta-actividad prioridad-${prioridad.toLowerCase()}`;
    enlace.href = `/static/operario/actividad.html?id=${encodeURIComponent(actividad.id)}`;

    const etiqueta = document.createElement("span");
    etiqueta.className = "etiqueta";
    etiqueta.textContent = NOMBRE_PRIORIDAD[prioridad] || prioridad;

    const estado = document.createElement("span");
    estado.className = "estado";
    estado.textContent = NOMBRE_ESTADO[actividad.estado] || actividad.estado;

    const titulo = document.createElement("h2");
    titulo.textContent = actividad.titulo;

    const descripcion = document.createElement("p");
    descripcion.textContent = actividad.descripcion;

    // Se usa textContent (no innerHTML) para que un texto con etiquetas no se ejecute como HTML.
    enlace.append(etiqueta, estado, titulo, descripcion);
    elemento.append(enlace);
    return elemento;
}

function mostrarAvisoUrgente(actividades) {
    const aviso = document.getElementById("aviso-urgente");
    const urgentes = actividades.filter((actividad) => actividad.prioridad === "URGENTE");

    if (urgentes.length === 0) {
        aviso.hidden = true;
        return;
    }
    aviso.textContent = urgentes.length === 1
        ? `Tienes una actividad urgente: "${urgentes[0].titulo}". Pausa la actual para atenderla.`
        : `Tienes ${urgentes.length} actividades urgentes. Pausa la actual para atenderlas.`;
    aviso.hidden = false;
}

async function iniciarPantalla() {
    const mensaje = document.getElementById("mensaje");
    const lista = document.getElementById("lista-actividades");
    const usuario = await iniciarPaginaProtegida(["OPERARIO"]);

    try {
        const actividades = await cargarActividades(usuario.id);
        mostrarAvisoUrgente(actividades);

        if (actividades.length === 0) {
            mensaje.textContent = "No tienes actividades pendientes.";
            return;
        }
        mensaje.hidden = true;
        lista.replaceChildren(...actividades.map(crearTarjeta));
    } catch (error) {
        mensaje.textContent = `No se pudieron cargar las actividades: ${error.message}`;
        mensaje.classList.add("mensaje-error");
    }
}

iniciarPantalla();
