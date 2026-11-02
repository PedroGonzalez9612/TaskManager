// Gráficas de la interfaz con Chart.js (alcance, Sección 7). Necesita vendor/chartjs/chart.umd.min.js.
// Reglas de todas: los colores salen de :root (--grafica-1 a --grafica-3, validados para daltonismo);
// barras de 24 px como máximo con la punta redondeada, líneas de 2 px y puntos de 8 px con una forma
// distinta por serie; leyenda si hay dos o más series; y siempre la tabla con los mismos datos
// ("Ver los datos"), porque el color nunca es el único canal ni la única forma de leer el dato.

const FORMAS_DE_PUNTO = ["circle", "rect", "triangle"];
const graficasActivas = new Map();      // Una gráfica por lienzo: al repintar se destruye la anterior.

function variableCss(nombre) {
    return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}

function coloresDeGraficas() {
    return [variableCss("--grafica-1"), variableCss("--grafica-2"), variableCss("--grafica-3")];
}

// Una tabla con los mismos datos de la gráfica, plegada bajo "Ver los datos".
function crearTablaDeDatos(etiquetas, series, formato) {
    const detalles = crearElemento("details", "grafica-datos");
    detalles.append(crearElemento("summary", "", "Ver los datos"));
    const tabla = crearElemento("table", "tabla");
    const encabezado = crearElemento("tr");
    encabezado.append(crearElemento("th", "", ""), ...series.map((serie) => {
        const celda = crearElemento("th", "", serie.nombre);
        celda.scope = "col";
        return celda;
    }));
    const cuerpo = crearElemento("tbody");
    etiquetas.forEach((etiqueta, indice) => {
        const fila = crearElemento("tr");
        const nombre = crearElemento("th", "", etiqueta);
        nombre.scope = "row";
        fila.append(nombre, ...series.map((serie) => crearElemento("td", "cifra", formato(serie.valores[indice]))));
        cuerpo.append(fila);
    });
    const cabeza = crearElemento("thead");
    cabeza.append(encabezado);
    tabla.append(cabeza, cuerpo);
    detalles.append(tabla);
    return detalles;
}

// Ejes en números redondos (guía de visualización): para minutos, marcas cada 1, 2, 5, 10... horas.
function pasoEnHoras(maximoMin) {
    const horas = maximoMin / 60;
    const paso = [1, 2, 5, 10, 20, 50, 100].find((candidato) => horas / candidato <= 6) || 200;
    return paso * 60;
}

const ejeEnHoras = (series) => ({
    paso: pasoEnHoras(Math.max(60, ...series.flatMap((serie) => serie.valores.map((v) => v || 0)))),
    formatoEje: (valor) => `${Math.round(valor / 60)} h`,
});

const ejeEnCantidades = { paso: 1, formatoEje: (valor) => String(valor) };

// Pinta una gráfica dentro de "contenedor" y devuelve su figura.
// eje (opcional): { paso, formatoEje } para marcas redondas; sin él, Chart.js elige y se usa "formato".
// tipo: "linea" o "barras". horizontal: barras acostadas (para nombres largos).
// series: [{ nombre, valores }]. formato(valor) da el texto de una cifra (tabla y tooltip).
// descripcion: lo que la gráfica dice, para el lector de pantalla (el lienzo es una imagen).
function pintarGrafica(contenedor, { id, titulo, descripcion, tipo, etiquetas, series, formato, horizontal = false, maximo = null, eje = null }) {
    graficasActivas.get(id)?.destroy();
    const figura = crearElemento("figure", "grafica");
    figura.append(crearElemento("figcaption", "grafica-titulo", titulo));
    const marco = crearElemento("div", horizontal ? "grafica-lienzo grafica-horizontal" : "grafica-lienzo");
    if (horizontal) {
        marco.style.height = `${Math.max(8, etiquetas.length * (1.25 + 1.25 * series.length) + 4)}rem`;
    }
    const lienzo = crearElemento("canvas");
    lienzo.id = id;
    lienzo.setAttribute("role", "img");
    lienzo.setAttribute("aria-label", descripcion);
    marco.append(lienzo);
    figura.append(marco, crearTablaDeDatos(etiquetas, series, formato));
    contenedor.replaceChildren(figura);

    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
    const colores = coloresDeGraficas();
    const texto = variableCss("--texto-secundario");
    const rejilla = variableCss("--borde");
    const superficie = variableCss("--superficie");
    const conjuntos = series.map((serie, indice) => (tipo === "linea"
        ? {
            label: serie.nombre, data: serie.valores, borderColor: colores[indice], backgroundColor: colores[indice],
            borderWidth: 2, pointRadius: 4, pointHoverRadius: 6, pointStyle: FORMAS_DE_PUNTO[indice],
            pointBorderColor: superficie, pointBorderWidth: 2, spanGaps: false, tension: 0,
        }
        : {
            label: serie.nombre, data: serie.valores, backgroundColor: colores[indice],
            maxBarThickness: 24, borderRadius: 4, borderSkipped: "start",
        }));
    const ejeValores = {
        beginAtZero: true, max: maximo ?? undefined,
        grid: { color: rejilla, lineWidth: 1, drawTicks: false }, border: { display: false },
        ticks: { color: texto, padding: 8, stepSize: eje?.paso, precision: 0, callback: (valor) => (eje?.formatoEje || formato)(valor) },
    };
    const ejeEtiquetas = { grid: { display: false }, border: { color: rejilla }, ticks: { color: texto, maxRotation: 0, autoSkip: true } };
    const grafica = new Chart(lienzo, {
        type: tipo === "linea" ? "line" : "bar",
        data: { labels: etiquetas, datasets: conjuntos },
        options: {
            indexAxis: horizontal ? "y" : "x",
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            // La ventanita toma la fila o la columna bajo el puntero: en las barras acostadas, por la
            // altura (eje y); si no, Chart.js busca por x y muestra siempre la misma fila.
            interaction: { mode: "index", intersect: false, axis: horizontal ? "y" : "x" },
            scales: horizontal ? { x: ejeValores, y: ejeEtiquetas } : { x: ejeEtiquetas, y: ejeValores },
            plugins: {
                legend: {
                    display: series.length > 1, position: "top", align: "start",
                    labels: { color: texto, usePointStyle: true, boxWidth: 8, boxHeight: 8, padding: 16 },
                },
                tooltip: {
                    callbacks: { label: (contexto) => `${contexto.dataset.label}: ${formato(contexto.parsed[horizontal ? "x" : "y"])}` },
                },
            },
        },
    });
    graficasActivas.set(id, grafica);
    return figura;
}

// Si no hay nada que graficar, una frase en lugar de una gráfica vacía.
function pintarSinDatos(contenedor, titulo, texto) {
    graficasActivas.forEach((grafica, id) => {
        if (contenedor.querySelector(`#${id}`)) {
            grafica.destroy();
            graficasActivas.delete(id);
        }
    });
    const figura = crearElemento("figure", "grafica");
    figura.append(crearElemento("figcaption", "grafica-titulo", titulo), crearElemento("p", "texto-secundario", texto));
    contenedor.replaceChildren(figura);
}
