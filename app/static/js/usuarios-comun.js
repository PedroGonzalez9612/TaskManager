// Lista y formulario de usuarios de una empresa.
// Lo usan el Superadmin (dentro de una empresa) y el Administrador (en su propia empresa).
// Necesita componentes.js.

// Un usuario no se borra: se desactiva y se puede reactivar (alcance, Sección 4).
function abrirDesactivar(usuario, alCambiar) {
    abrirDialogoAccion({
        titulo: `Desactivar a ${usuario.nombre}`,
        campos: [crearElemento("p", "dialogo-actividad",
            "No podrá iniciar sesión ni recibir actividades ni turnos, y su cupo queda libre. "
            + "Su nombre y su historial se conservan, y puedes reactivar su usuario cuando quieras.")],
        textoConfirmar: "Desactivar",
        iconoConfirmar: "minus",
        alConfirmar: async () => {
            await pedirApi(`/usuarios/${encodeURIComponent(usuario.id)}/desactivar`, { method: "POST" });
            await alCambiar();
            mostrarAviso(`Se desactivó el usuario de ${usuario.nombre}.`);
        },
    });
}

async function reactivar(boton, usuario, alCambiar) {
    boton.disabled = true;
    try {
        await pedirApi(`/usuarios/${encodeURIComponent(usuario.id)}/reactivar`, { method: "POST" });
        await alCambiar();
        mostrarAviso(`Se reactivó el usuario de ${usuario.nombre}.`);
    } catch (error) {
        mostrarAviso(error.message, "advertencia");
        boton.disabled = false;
    }
}

// "alAsignarTurno" (opcional): si viene, los operarios muestran su turno y un botón para cambiarlo.
// "opciones.alCambiar" (opcional): si viene, cada fila ofrece desactivar o reactivar al usuario,
// menos al que está usando la pantalla ("opciones.usuarioActualId").
function crearFilaUsuario(usuario, alAsignarTurno = null, opciones = {}) {
    const activo = usuario.activo !== false;
    const fila = crearElemento("li", activo ? "fila-usuario" : "fila-usuario fila-desactivada");
    const textos = crearElemento("div");
    const nombre = crearElemento("span", "fila-nombre", usuario.nombre);
    if (!activo) {
        nombre.append(" ", crearConIcono("span", "etiqueta", "minus", "Desactivado"));
    }
    // El rol va con los datos de la persona; a la derecha quedan solo las acciones, en un renglón.
    const meta = crearElemento("span", "fila-meta datos-linea");
    meta.append(crearElemento("span", "", NOMBRE_ROL[usuario.rol] || usuario.rol), crearElemento("span", "", usuario.correo));
    textos.append(nombre, meta);
    const acciones = crearElemento("span", "fila-usuario-acciones");
    if (alAsignarTurno && usuario.rol === "OPERARIO" && activo) {
        const turno = usuario.turno;
        textos.append(crearElemento("span", "fila-meta cifra",
            turno ? `Turno ${turno.nombre}, ${turno.hora_inicio} a ${turno.hora_fin}` : "Sin turno asignado"));
        const boton = crearElemento("button", "boton-texto", turno ? "Cambiar turno" : "Asignar turno");
        boton.type = "button";
        boton.addEventListener("click", () => alAsignarTurno(usuario));
        acciones.append(boton);
    }
    if (opciones.alCambiar && usuario.id !== opciones.usuarioActualId) {
        const baja = crearElemento("button", activo ? "boton-texto peligro" : "boton-texto", activo ? "Desactivar" : "Reactivar");
        baja.type = "button";
        baja.addEventListener("click", () => (activo
            ? abrirDesactivar(usuario, opciones.alCambiar)
            : reactivar(baja, usuario, opciones.alCambiar)));
        acciones.append(baja);
    }
    fila.append(crearAvatarNeutro(usuario.nombre), textos, acciones);
    return fila;
}

// Llena la lista de usuarios o muestra el estado vacío si la empresa no tiene ninguno.
// Devuelve los usuarios cargados.
async function cargarUsuarios(empresaId, lista, estadoVacio, alAsignarTurno = null, opciones = {}) {
    try {
        const usuarios = await pedirApi(`/usuarios?empresa_id=${encodeURIComponent(empresaId)}`);
        // Primero los activos; después, los administradores y, dentro de cada rol, por nombre.
        const inactivo = (u) => (u.activo === false ? 1 : 0);
        usuarios.sort((a, b) => inactivo(a) - inactivo(b) || a.rol.localeCompare(b.rol)
            || a.nombre.localeCompare(b.nombre, "es"));
        lista.hidden = usuarios.length === 0;
        estadoVacio.hidden = usuarios.length > 0;
        lista.replaceChildren(...usuarios.map((u) => crearFilaUsuario(u, alAsignarTurno, opciones)));
        return usuarios;
    } catch (error) {
        lista.hidden = true;
        estadoVacio.hidden = false;
        estadoVacio.textContent = `No se pudieron cargar los usuarios: ${error.message}`;
        estadoVacio.classList.add("mensaje-error");
        return [];
    }
}

function validarUsuario(datos) {
    if (!datos.nombre.trim() || !datos.correo.trim() || !datos.contraseña) {
        return "Completa nombre, correo y contraseña.";
    }
    if (datos.contraseña.length < 8) {
        return "La contraseña debe tener al menos 8 caracteres.";
    }
    return null;
}

// Conecta el diálogo de creación de usuario. "alCrear" recarga la lista después de guardar.
function configurarCreacionUsuario(botonesAbrir, dialogo, empresaId, alCrear) {
    configurarDialogo(botonesAbrir, dialogo);
    dialogo.querySelector("form").addEventListener("submit", (evento) => {
        evento.preventDefault();
        enviarFormularioDialogo(dialogo, validarUsuario, async (datos) => {
            const usuario = await enviarJson("/usuarios", "POST", { ...datos, empresa_id: empresaId });
            await alCrear();
            return `${NOMBRE_ROL[usuario.rol]} "${usuario.nombre}" creado. Ya puede iniciar sesión.`;
        });
    });
}
