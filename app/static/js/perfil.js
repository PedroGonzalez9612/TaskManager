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

// Un error que sabe en qué campo está, para marcarlo (alcance, Sección 6.3: borde rojo en el campo
// con el mensaje debajo).
class ErrorDeCampo extends Error {
    constructor(idCampo, mensaje) {
        super(mensaje);
        this.idCampo = idCampo;
    }
}

// Se revisa antes de enviar para ayudar (Nielsen 5); el servidor vuelve a validar todo.
function leerFormulario() {
    const actual = document.getElementById("contrasena-actual").value;
    const nueva = document.getElementById("contrasena-nueva").value;
    const repetida = document.getElementById("contrasena-repetir").value;
    if (!actual) {
        throw new ErrorDeCampo("contrasena-actual", "Escribe tu contraseña actual.");
    }
    if (nueva.length < LONGITUD_MINIMA_CONTRASENA) {
        throw new ErrorDeCampo("contrasena-nueva", `La contraseña nueva debe tener al menos ${LONGITUD_MINIMA_CONTRASENA} caracteres.`);
    }
    if (nueva !== repetida) {
        throw new ErrorDeCampo("contrasena-repetir", "Las dos contraseñas nuevas no coinciden.");
    }
    return { actual, nueva };
}

// El error del servidor también se ubica en su campo: la actual o la nueva.
function campoDelError(error) {
    if (error.idCampo) {
        return error.idCampo;
    }
    return /actual/i.test(error.message) ? "contrasena-actual" : "contrasena-nueva";
}

function marcarCampo(idCampo, idMensaje) {
    const campo = document.getElementById(idCampo);
    campo.setAttribute("aria-invalid", "true");
    const descripciones = (campo.getAttribute("aria-describedby") || "").split(" ").filter(Boolean);
    if (!descripciones.includes(idMensaje)) {
        campo.setAttribute("aria-describedby", [...descripciones, idMensaje].join(" "));
    }
    campo.focus();
}

function limpiarCampos(campos, idMensaje) {
    for (const campo of campos) {
        campo.removeAttribute("aria-invalid");
        const resto = (campo.getAttribute("aria-describedby") || "").split(" ").filter((id) => id && id !== idMensaje);
        if (resto.length) {
            campo.setAttribute("aria-describedby", resto.join(" "));
        } else {
            campo.removeAttribute("aria-describedby");
        }
    }
}

function configurarFormulario() {
    const formulario = document.getElementById("formulario-contrasena");
    const error = formulario.querySelector(".mensaje-formulario");
    const boton = formulario.querySelector("button[type=submit]");
    const campos = formulario.querySelectorAll("input[type=password]");
    error.id = "error-contrasena";
    // Al escribir de nuevo, la marca de error se quita.
    for (const campo of campos) {
        campo.addEventListener("input", () => limpiarCampos([campo], error.id));
    }

    document.getElementById("mostrar-contrasenas").addEventListener("change", (evento) => {
        for (const campo of campos) {
            campo.type = evento.target.checked ? "text" : "password";
        }
    });

    formulario.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        error.hidden = true;
        limpiarCampos(campos, error.id);
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
            marcarCampo(campoDelError(error_), error.id);
        } finally {
            boton.disabled = false;
        }
    });
}

iniciarPaginaProtegida(["SUPERADMIN", "ADMINISTRADOR", "OPERARIO"]).then((usuario) => {
    pintarDatos(usuario);
    configurarFormulario();
});
