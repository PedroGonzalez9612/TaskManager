// Lista y formulario de usuarios de una empresa.
// Lo usan el Superadmin (dentro de una empresa) y el Administrador (en su propia empresa).
// Necesita componentes.js.

function crearFilaUsuario(usuario) {
    const fila = crearElemento("li", "fila-usuario");
    const textos = crearElemento("div");
    textos.append(
        crearElemento("span", "fila-nombre", usuario.nombre),
        crearElemento("span", "fila-meta", usuario.correo),
    );
    fila.append(
        crearAvatarNeutro(usuario.nombre),
        textos,
        crearElemento("span", "rol", NOMBRE_ROL[usuario.rol] || usuario.rol),
    );
    return fila;
}

// Llena la lista de usuarios o muestra el estado vacío si la empresa no tiene ninguno.
// Devuelve los usuarios cargados.
async function cargarUsuarios(empresaId, lista, estadoVacio) {
    try {
        const usuarios = await pedirApi(`/usuarios?empresa_id=${encodeURIComponent(empresaId)}`);
        // Primero los administradores y, dentro de cada rol, por nombre.
        usuarios.sort((a, b) => a.rol.localeCompare(b.rol) || a.nombre.localeCompare(b.nombre, "es"));
        lista.hidden = usuarios.length === 0;
        estadoVacio.hidden = usuarios.length > 0;
        lista.replaceChildren(...usuarios.map(crearFilaUsuario));
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
