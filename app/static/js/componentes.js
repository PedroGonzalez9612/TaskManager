// Componentes visuales pequeños que se repiten en varias pantallas.
// Necesita api.js, vendor/lucide/iconos.js y layout.js.

// Cuadro con el logo de una empresa. Si no tiene logo, muestra la inicial de su nombre en gris.
function crearLogoCuadro(empresa, grande = false) {
    const cuadro = crearElemento("span", grande ? "logo-cuadro logo-cuadro-grande" : "logo-cuadro");
    if (empresa.tiene_logo) {
        const imagen = crearElemento("img");
        imagen.src = urlLogo(empresa.id);
        imagen.alt = "";
        cuadro.append(imagen);
    } else {
        cuadro.classList.add("sin-logo");
        cuadro.textContent = empresa.nombre.charAt(0).toUpperCase();
        cuadro.setAttribute("aria-hidden", "true");
    }
    return cuadro;
}

function crearAvatarNeutro(nombre) {
    const avatar = crearElemento("span", "avatar-neutro", nombre.charAt(0).toUpperCase());
    avatar.setAttribute("aria-hidden", "true");
    return avatar;
}

// Medidor de un límite: "Operarios  3 de 10" con una barra. Si no hay límite, solo la cantidad.
// Cuando el límite se alcanza lo dice con ícono y texto, no solo con el color de la barra.
function crearMedidor(nombre, actuales, limite, grande = false) {
    const lleno = limite != null && actuales >= limite;
    const medidor = crearElemento("div", "medidor");
    if (grande) {
        medidor.classList.add("medidor-grande");
    }

    const texto = crearElemento("div", "medidor-texto");
    texto.append(
        crearElemento("span", "medidor-nombre", nombre),
        crearElemento("span", "cifra", limite == null ? String(actuales) : `${actuales} de ${limite}`),
    );
    medidor.append(texto);

    if (limite == null) {
        medidor.append(crearElemento("span", "medidor-sin-limite", "Sin límite"));
    } else {
        const barra = crearElemento("div", "medidor-barra");
        const relleno = crearElemento("div", "medidor-relleno");
        relleno.style.width = `${Math.min(100, Math.round(actuales * 100 / limite))}%`;
        barra.append(relleno);
        medidor.append(barra);
    }
    if (lleno && grande) {
        medidor.append(crearConIcono("p", "medidor-nota", "circle-alert", "Límite alcanzado"));
    }
    return medidor;
}

// Los dos medidores de una empresa (administradores y operarios).
function crearMedidoresEmpresa(empresa, grande = false) {
    const actuales = empresa.usuarios_actuales;
    return [
        crearMedidor("Administradores", actuales.ADMINISTRADOR || 0, empresa.limite_administradores, grande),
        crearMedidor("Operarios", actuales.OPERARIO || 0, empresa.limite_operarios, grande),
    ];
}
