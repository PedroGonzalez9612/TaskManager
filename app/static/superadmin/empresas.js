// Superadmin: lista de empresas; desde aquí registra nuevas o entra a cada una.

const BUSCADOR_DESDE = 6;   // Con pocas empresas el buscador sobra: aparece desde esta cantidad.

const lista = document.getElementById("lista-empresas");
const estadoVacio = document.getElementById("estado-vacio");
const sinResultados = document.getElementById("sin-resultados");
const buscar = document.getElementById("buscar");
const dialogo = document.getElementById("dialogo-empresa");
let empresas = [];

function crearFilaEmpresa(empresa) {
    const elemento = crearElemento("li");
    const fila = crearElemento("a", "fila-empresa");
    fila.href = `/static/superadmin/empresa.html?id=${encodeURIComponent(empresa.id)}`;

    const textos = crearElemento("span");
    const meta = crearElemento("span", "fila-meta");
    meta.append(crearElemento("span", "codigo", empresa.nit), ` · ${empresa.sector}`);
    textos.append(crearElemento("span", "fila-nombre", empresa.nombre), meta);

    const medidores = crearElemento("span", "medidores");
    medidores.append(...crearMedidoresEmpresa(empresa));

    fila.append(crearLogoCuadro(empresa), textos, medidores);
    fila.insertAdjacentHTML("beforeend", icono("chevron-right"));
    elemento.append(fila);
    return elemento;
}

function pintarResumen() {
    const sumar = (rol) => empresas.reduce((total, empresa) => total + (empresa.usuarios_actuales[rol] || 0), 0);
    const plural = (cantidad, uno, varios) => `${cantidad} ${cantidad === 1 ? uno : varios}`;
    document.getElementById("resumen").textContent = [
        plural(empresas.length, "empresa", "empresas"),
        plural(sumar("ADMINISTRADOR"), "administrador", "administradores"),
        plural(sumar("OPERARIO"), "operario", "operarios"),
    ].join(" · ");
}

function pintarLista() {
    const texto = buscar.value.trim().toLowerCase();
    const visibles = empresas.filter((empresa) =>
        empresa.nombre.toLowerCase().includes(texto) || empresa.nit.toLowerCase().includes(texto));

    estadoVacio.hidden = empresas.length > 0;
    sinResultados.hidden = empresas.length === 0 || visibles.length > 0;
    lista.hidden = visibles.length === 0;
    lista.replaceChildren(...visibles.map(crearFilaEmpresa));
}

async function cargarEmpresas() {
    try {
        empresas = await pedirApi("/empresas");
        empresas.sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
        document.getElementById("herramientas").hidden = empresas.length < BUSCADOR_DESDE;
        pintarResumen();
        pintarLista();
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

document.querySelector(".buscador").insertAdjacentHTML("afterbegin", icono("search"));
buscar.addEventListener("input", pintarLista);

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
