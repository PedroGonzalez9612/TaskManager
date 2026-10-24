// Mi perfil (alcance, Sección 5.1): los datos del usuario y el cambio de su contraseña. Es la misma
// página para los tres roles; se entra tocando el avatar de la barra superior.

const LONGITUD_MINIMA_CONTRASENA = 8;     // La misma del servidor (usuario_service.py).

function pintarDatos(usuario) {
    const filas = [["Nombre", usuario.nombre]];
    // Una sesión abierta antes de que se guardara el correo no lo trae: se ve al volver a entrar.
    if (usuario.correo) {
        filas.push(["Correo", usuario.correo]);
    }
    filas.push(["Rol", NOMBRE_ROL[usuario.rol] || usuario.rol]);
    if (usuario.empresa) {
        filas.push(["Empresa", usuario.empresa.nombre]);
    }
    document.getElementById("perfil-datos").replaceChildren(...filas.flatMap(([nombre, valor]) =>
        [crearElemento("dt", "", nombre), crearElemento("dd", "", valor)]));
}

// Se revisa antes de enviar para ayudar (Nielsen 5); el servidor vuelve a validar todo.
function leerFormulario() {
    const actual = document.getElementById("contrasena-actual").value;
    const nueva = document.getElementById("contrasena-nueva").value;
    const repetida = document.getElementById("contrasena-repetir").value;
    if (!actual) {
        throw new Error("Escribe tu contraseña actual.");
    }
    if (nueva.length < LONGITUD_MINIMA_CONTRASENA) {
        throw new Error(`La contraseña nueva debe tener al menos ${LONGITUD_MINIMA_CONTRASENA} caracteres.`);
    }
    if (nueva !== repetida) {
        throw new Error("Las dos contraseñas nuevas no coinciden.");
    }
    return { actual, nueva };
}

function configurarFormulario() {
    const formulario = document.getElementById("formulario-contrasena");
    const error = formulario.querySelector(".mensaje-formulario");
    const boton = formulario.querySelector("button[type=submit]");
    const campos = formulario.querySelectorAll("input[type=password]");

    document.getElementById("mostrar-contrasenas").addEventListener("change", (evento) => {
        for (const campo of campos) {
            campo.type = evento.target.checked ? "text" : "password";
        }
    });

    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        error.hidden = true;
        boton.disabled = true;
        try {
            await enviarJson("/auth/contrasena", "PUT", leerFormulario());
            formulario.reset();
            for (const campo of campos) {
                campo.type = "password";
            }
            mostrarAviso("Contraseña cambiada. La próxima vez entra con la nueva.");
        } catch (error_) {
            mostrarErrorFormulario(error, error_.message);
        } finally {
            boton.disabled = false;
        }
    });
}

iniciarPaginaProtegida(["SUPERADMIN", "ADMINISTRADOR", "OPERARIO"]).then((usuario) => {
    pintarDatos(usuario);
    configurarFormulario();
});
