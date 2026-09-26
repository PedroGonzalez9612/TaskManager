// Tabla y formulario de usuarios de una empresa.
// Lo usan el Superadmin (dentro de una empresa) y el Administrador (en su propia empresa).

function crearFilaUsuario(usuario) {
    const fila = document.createElement("tr");

    const nombre = document.createElement("td");
    nombre.textContent = usuario.nombre;
    nombre.style.fontWeight = "600";

    const correo = document.createElement("td");
    correo.className = "texto-suave";
    correo.textContent = usuario.correo;

    const rol = document.createElement("td");
    const etiqueta = document.createElement("span");
    etiqueta.className = `etiqueta etiqueta-rol-${usuario.rol.toLowerCase()}`;
    etiqueta.textContent = NOMBRE_ROL[usuario.rol] || usuario.rol;
    rol.append(etiqueta);

    // textContent (no innerHTML) para que un texto con etiquetas no se ejecute como HTML.
    fila.append(nombre, correo, rol);
    return fila;
}

// Llena la tabla de usuarios o muestra el estado vacío si la empresa no tiene ninguno.
async function cargarUsuarios(empresaId, tabla, estadoVacio) {
    const cuerpo = tabla.querySelector("tbody");
    try {
        const usuarios = await pedirApi(`/usuarios?empresa_id=${encodeURIComponent(empresaId)}`);
        tabla.hidden = usuarios.length === 0;
        estadoVacio.hidden = usuarios.length > 0;
        cuerpo.replaceChildren(...usuarios.map(crearFilaUsuario));
    } catch (error) {
        tabla.hidden = true;
        estadoVacio.hidden = false;
        estadoVacio.textContent = `No se pudieron cargar los usuarios: ${error.message}`;
        estadoVacio.classList.add("mensaje-error");
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

// Conecta el diálogo de creación de usuario. "alCrear" recarga la tabla después de guardar.
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
