// Inicio de sesión: al entrar, cada rol va a su propia pantalla de inicio.

const formulario = document.getElementById("formulario-login");
const mensaje = document.getElementById("mensaje");

function mostrarError(texto) {
    mensaje.textContent = texto;
    mensaje.hidden = false;
}

formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const datos = datosFormulario(formulario);

    if (!datos.correo || !datos.contraseña) {
        mostrarError("Escribe tu correo y tu contraseña.");
        return;
    }

    const boton = formulario.querySelector("button");
    boton.disabled = true;
    boton.textContent = "Ingresando…";

    try {
        const usuario = await enviarJson("/auth/login", "POST", datos);
        window.location.href = INICIO_POR_ROL[usuario.rol];
    } catch (error) {
        mostrarError(error.message);
        boton.disabled = false;
        boton.textContent = "Ingresar";
    }
});

// Si ya hay una sesión abierta, no tiene sentido volver a pedir el login.
fetch("/auth/sesion").then(async (respuesta) => {
    if (respuesta.ok) {
        const usuario = await respuesta.json();
        window.location.href = INICIO_POR_ROL[usuario.rol];
    }
});
