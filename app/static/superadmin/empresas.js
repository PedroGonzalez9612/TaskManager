// Superadmin: lista de empresas; desde aquí registra nuevas o entra a cada una.

const tabla = document.getElementById("tabla-empresas");
const estadoVacio = document.getElementById("estado-vacio");
const dialogo = document.getElementById("dialogo-empresa");

function crearCelda(texto) {
    const celda = document.createElement("td");
    celda.textContent = texto;
    return celda;
}

function crearFilaEmpresa(empresa) {
    const fila = document.createElement("tr");

    const nombre = document.createElement("td");
    const contenido = document.createElement("div");
    contenido.className = "celda-empresa";
    if (empresa.tiene_logo) {
        const logo = document.createElement("img");
        logo.className = "logo-miniatura";
        logo.src = urlLogo(empresa.id);
        logo.alt = "";
        contenido.append(logo);
    }
    const enlace = document.createElement("a");
    enlace.className = "enlace-fila";
    enlace.href = `/static/superadmin/empresa.html?id=${encodeURIComponent(empresa.id)}`;
    enlace.textContent = empresa.nombre;
    contenido.append(enlace);
    nombre.append(contenido);

    const actuales = empresa.usuarios_actuales;
    // textContent (no innerHTML) para que un texto con etiquetas no se ejecute como HTML.
    fila.append(
        nombre,
        crearCelda(empresa.nit),
        crearCelda(empresa.sector),
        crearCelda(textoCupo(actuales.ADMINISTRADOR || 0, empresa.limite_administradores)),
        crearCelda(textoCupo(actuales.OPERARIO || 0, empresa.limite_operarios)),
    );
    return fila;
}

async function cargarEmpresas() {
    try {
        const empresas = await pedirApi("/empresas");
        tabla.hidden = empresas.length === 0;
        estadoVacio.hidden = empresas.length > 0;
        tabla.querySelector("tbody").replaceChildren(...empresas.map(crearFilaEmpresa));
    } catch (error) {
        estadoVacio.hidden = false;
        estadoVacio.textContent = `No se pudieron cargar las empresas: ${error.message}`;
        estadoVacio.classList.add("mensaje-error");
    }
}

const campoLogo = configurarCampoLogo(dialogo, () => null);

function validarEmpresa(datos) {
    const textos = [datos.nombre, datos.nit, datos.sector, datos.direccion];
    if (textos.some((valor) => !valor.trim())) {
        return "Completa nombre, NIT, sector y dirección.";
    }
    for (const limite of [datos.limite_administradores, datos.limite_operarios]) {
        if (!Number.isInteger(Number(limite)) || Number(limite) < 1) {
            return "Los límites de usuarios deben ser números enteros mayores o iguales a 1.";
        }
    }
    return validarArchivoLogo(campoLogo.archivo());
}

configurarDialogo(document.querySelectorAll("[data-abrir-dialogo]"), dialogo);
dialogo.querySelector("form").addEventListener("submit", (evento) => {
    evento.preventDefault();
    enviarFormularioDialogo(dialogo, validarEmpresa, async (datos) => {
        const empresa = await enviarJson("/empresas", "POST", datos);
        let texto = `Empresa "${empresa.nombre}" registrada.`;

        // La empresa ya quedó creada; si el logo falla, se avisa sin perder lo demás.
        const archivo = campoLogo.archivo();
        if (archivo) {
            try {
                await subirLogo(empresa.id, archivo);
            } catch (error) {
                texto += ` El logo no se guardó (${error.message}); puedes subirlo desde la empresa.`;
            }
        }
        await cargarEmpresas();
        return texto;
    });
});

iniciarPaginaProtegida(["SUPERADMIN"]).then(cargarEmpresas);
