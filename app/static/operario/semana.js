// Vista "Semana" del Operario (alcance, Secciones 6.1 y 6.2; observaciones 8, 11 y 12 del usuario).
// Cada día con su programación, calculada en el servidor con las mismas reglas de Hoy
// (GET /programacion-de-la-semana): lo pasado, con lo finalizado en sus horas reales; hoy, dinámico;
// lo futuro, proyectado desde el inicio del turno. Lo de horario flexible va en su hora estimada, con "~".
// Calendario propio, con el lenguaje de Hoy y del tablero: en computador, siete columnas con las horas
// de arriba abajo; en celular, un día a la vez como la línea de tiempo de Hoy. Todo se lee: tocar una
// actividad abre su detalle, que solo ofrece acciones en la jornada vigente con la entrada marcada.

const PANTALLA_ANGOSTA = window.matchMedia("(max-width: 50em)");
const PX_POR_MINUTO = 1.2;          // Alto de la cuadrícula: 72 px por hora (lo lee el CSS en --alto-hora).
const DURACION_MINIMA_MIN = 50;     // Un bloque corto se dibuja con este alto: caben la hora y dos renglones.
const DURACION_BLOQUE_LARGO_MIN = 45;   // Desde aquí el nombre puede ocupar tres renglones.
const UN_MINUTO = 60000;

let lunes = inicioDeSemana(new Date());
let semana = null;
let actividades = [];
let diaElegido = null;              // En celular: la fecha que se ve.
let cargadaEn = 0;                  // Cuándo llegó la semana: el tiempo en curso se adelanta desde ahí.

function hora(momento) {
    const fecha = new Date(momento);
    return `${String(fecha.getHours()).padStart(2, "0")}:${String(fecha.getMinutes()).padStart(2, "0")}`;
}

// "lun 19"
function diaCorto(textoFecha) {
    const fecha = fechaDesdeTexto(textoFecha);
    const dia = fecha.toLocaleDateString("es-CO", { weekday: "short" }).replace(".", "");
    return `${dia} ${fecha.getDate()}`;
}

function actividadDe(tramo) {
    return actividades.find((actividad) => actividad.id === tramo.actividad_id);
}

// La carga del día: lo trabajado más lo que falta, frente a la capacidad del turno.
function cargaDelDia(dia) {
    const { trabajado_min: trabajado, pendiente_min: pendiente, capacidad_min: capacidad } = dia.resumen;
    return { total: trabajado + pendiente, capacidad, sobrecarga: trabajado + pendiente > capacidad };
}

function textoCarga(dia) {
    const { total, capacidad } = cargaDelDia(dia);
    return total ? `${duracionTexto(total)} de ${duracionTexto(capacidad)}` : "Sin actividades";
}

// El detalle solo ofrece acciones en la jornada vigente y con la entrada marcada (alcance, Sección 5.1).
function abrirDetalle(actividad, dia) {
    const conEntrada = dia.asistencia && dia.asistencia.jornada === dia.fecha && !dia.asistencia.salida;
    abrirDetalleOperario(actividad, actividades, cargar, { volverA: "Semana", soloLectura: !(dia.es_vigente && conEntrada) });
}

// Lo que dice cada actividad: hora (con "~" si es estimada), nombre y, si hace falta, su estado.
function textoHora(tramo) {
    return (tramo.aproximada && tramo.tipo === "PENDIENTE" ? "~" : "") + hora(tramo.inicio);
}

function claseDeTramo(tramo, actividad) {
    if (tramo.tipo === "FINALIZADA") {
        return "semana-hecha";
    }
    if (tramo.tipo === "EN_CURSO") {
        return "semana-en-curso";
    }
    if (actividad.prioridad === "URGENTE") {
        return "semana-urgente";
    }
    return tramo.hora_fija ? "semana-fija" : "semana-flexible";
}

// El estado que se escribe dentro del bloque: Urgente, En curso o Pausada. Lo normal no lleva texto.
function estadoDelBloque(tramo, actividad) {
    if (tramo.tipo === "FINALIZADA") {
        return null;
    }
    if (actividad.prioridad === "URGENTE") {
        return { clase: "semana-estado-urgente", icono: "triangle-alert", texto: "Urgente" };
    }
    if (tramo.tipo === "EN_CURSO") {
        return { clase: "semana-estado-en-curso", icono: "circle", texto: tramo.parte ? "Parte 1, en curso" : "En curso" };
    }
    if (tramo.parte === 2) {
        return { clase: "semana-estado-en-curso", icono: "circle", texto: "Parte 2" };
    }
    if (actividad.estado === "PAUSADA") {
        return { clase: "semana-estado-pausada", icono: "pause", texto: "Pausada" };
    }
    return null;
}

function iconoDeTramo(tramo) {
    if (tramo.tipo === "FINALIZADA") {
        return "check";
    }
    return tramo.hora_fija ? "lock" : "";
}

// ---------- Computador: la cuadrícula de la semana ----------

// Las horas visibles: de una hora antes del turno más temprano a una hora después del más tardío; si
// algo cae fuera, el rango se amplía (alcance, Sección 6.2, horarios). Sin turnos, de 06:00 a 18:00.
function rangoDeHoras() {
    const minutosDe = (momento) => {
        const fecha = new Date(momento);
        return fecha.getHours() * 60 + fecha.getMinutes();
    };
    let desde = Infinity;
    let hasta = -Infinity;
    for (const dia of semana.dias) {
        if (dia.turno) {
            desde = Math.min(desde, minutosDe(dia.turno.inicio) - 60);
            const fin = minutosDe(dia.turno.fin);
            hasta = Math.max(hasta, (fin <= minutosDe(dia.turno.inicio) ? 24 * 60 : fin) + 60);
        }
        for (const tramo of dia.tramos) {
            if (fechaTexto(new Date(tramo.inicio)) !== dia.fecha) {
                continue;     // Lo que pasa a otro día no amplía el rango.
            }
            desde = Math.min(desde, minutosDe(tramo.inicio));
            hasta = Math.max(hasta, minutosDe(tramo.inicio) + Math.max(DURACION_MINIMA_MIN, (new Date(tramo.fin) - new Date(tramo.inicio)) / UN_MINUTO));
        }
    }
    if (!Number.isFinite(desde)) {
        return { desde: 6 * 60, hasta: 18 * 60 };
    }
    return { desde: Math.max(0, Math.floor(desde / 60) * 60), hasta: Math.min(24 * 60, Math.ceil(hasta / 60) * 60) };
}

function crearBloque(tramo, dia, rango) {
    const actividad = actividadDe(tramo);
    const inicio = new Date(tramo.inicio);
    const minutoInicio = inicio.getHours() * 60 + inicio.getMinutes();
    const duracion = Math.max(DURACION_MINIMA_MIN, (new Date(tramo.fin) - inicio) / UN_MINUTO);
    const bloque = crearElemento("button", `semana-bloque ${claseDeTramo(tramo, actividad)}`);
    bloque.type = "button";
    bloque.style.top = `${(minutoInicio - rango.desde) * PX_POR_MINUTO}px`;
    bloque.style.height = `${duracion * PX_POR_MINUTO - 2}px`;
    if (duracion >= DURACION_BLOQUE_LARGO_MIN) {
        bloque.classList.add("semana-bloque-largo");
    }
    const cabeza = crearElemento("span", "semana-bloque-hora cifra");
    const iconoNombre = iconoDeTramo(tramo);
    if (iconoNombre) {
        cabeza.insertAdjacentHTML("beforeend", icono(iconoNombre));
    }
    cabeza.append(textoHora(tramo));
    // El estado que no es lo normal va con su ícono y su texto, no solo con el borde (6.3, regla 1). En
    // la misma línea de la hora, para que el nombre conserve sus renglones.
    const estado = estadoDelBloque(tramo, actividad);
    if (estado) {
        cabeza.append(crearConIcono("span", `semana-bloque-estado ${estado.clase}`, estado.icono, estado.texto));
    }
    bloque.append(cabeza);
    bloque.append(crearElemento("span", "semana-bloque-nombre", actividad.titulo));
    // El nombre accesible dice todo lo que se ve: hora, estado y nombre.
    bloque.setAttribute("aria-label", `${textoHora(tramo)}${estado ? `, ${estado.texto}` : ""}, ${actividad.titulo}. Ver detalle`);
    bloque.title = actividad.titulo;
    bloque.addEventListener("click", () => abrirDetalle(actividad, dia));
    return bloque;
}

// Lo que no es turno se raya en gris, como en el tablero; lo que pasa de su fin, en rojo (sobrecarga).
function crearFranjasDelTurno(dia, rango) {
    const franjas = [];
    const alto = (rango.hasta - rango.desde) * PX_POR_MINUTO;
    if (!dia.turno) {
        return franjas;
    }
    const minutos = (momento) => {
        const fecha = new Date(momento);
        const base = fecha.getHours() * 60 + fecha.getMinutes();
        return fechaTexto(fecha) === dia.fecha ? base : 24 * 60;
    };
    const inicio = (minutos(dia.turno.inicio) - rango.desde) * PX_POR_MINUTO;
    const fin = (minutos(dia.turno.fin) - rango.desde) * PX_POR_MINUTO;
    const franja = (clase, desde, hasta) => {
        const elemento = crearElemento("span", clase);
        elemento.style.top = `${Math.max(0, desde)}px`;
        elemento.style.height = `${Math.max(0, Math.min(alto, hasta) - Math.max(0, desde))}px`;
        return elemento;
    };
    franjas.push(franja("semana-fuera-turno", 0, inicio));
    franjas.push(franja(dia.resumen.fuera_del_turno_min ? "semana-sobrecarga" : "semana-fuera-turno", fin, alto));
    return franjas;
}

// Si dos bloques se cruzan (por ejemplo, una pausada a la que le falta poco y la siguiente), van lado
// a lado en lugar de taparse. Se agrupan los que se cruzan entre sí y solo esos se angostan: cada uno
// en el primer carril libre de su grupo.
function repartirEnCarriles(bloques) {
    const medida = (bloque) => {
        const arriba = parseFloat(bloque.style.top);
        return { bloque, arriba, abajo: arriba + parseFloat(bloque.style.height) };
    };
    const ordenados = bloques.map(medida).sort((a, b) => a.arriba - b.arriba);
    const grupos = [];
    for (const item of ordenados) {
        const grupo = grupos.at(-1);
        if (grupo && item.arriba < grupo.fin) {
            grupo.items.push(item);
            grupo.fin = Math.max(grupo.fin, item.abajo);
        } else {
            grupos.push({ items: [item], fin: item.abajo });
        }
    }
    for (const grupo of grupos.filter((g) => g.items.length > 1)) {
        const finesDeCarril = [];
        const carriles = grupo.items.map((item) => {
            let carril = finesDeCarril.findIndex((fin) => fin <= item.arriba);
            if (carril === -1) {
                carril = finesDeCarril.push(item.abajo) - 1;
            } else {
                finesDeCarril[carril] = item.abajo;
            }
            return carril;
        });
        grupo.items.forEach(({ bloque }, indice) => {
            bloque.style.left = `calc(${(carriles[indice] * 100) / finesDeCarril.length}% + 2px)`;
            bloque.style.width = `calc(${100 / finesDeCarril.length}% - 4px)`;
            bloque.style.right = "auto";
        });
    }
    return bloques;
}

function pintarCuadricula() {
    const rango = rangoDeHoras();
    const alto = (rango.hasta - rango.desde) * PX_POR_MINUTO;
    const cuadricula = document.getElementById("semana-cuadricula");
    const horas = crearElemento("div", "semana-horas");
    horas.setAttribute("aria-hidden", "true");
    horas.append(crearElemento("span", "semana-esquina"));
    const regla = crearElemento("div", "semana-regla");
    regla.style.height = `${alto}px`;
    for (let minuto = rango.desde; minuto < rango.hasta; minuto += 60) {
        const marca = crearElemento("span", "cifra", `${String(minuto / 60).padStart(2, "0")}:00`);
        marca.style.top = `${(minuto - rango.desde) * PX_POR_MINUTO}px`;
        regla.append(marca);
    }
    horas.append(regla);

    const columnas = semana.dias.map((dia) => {
        const columna = crearElemento("section", `semana-columna${dia.es_vigente ? " semana-hoy" : ""}`);
        columna.setAttribute("aria-label", fechaLarga(fechaDesdeTexto(dia.fecha)));
        const cabeza = crearElemento("header", "semana-cabeza");
        const carga = cargaDelDia(dia);
        const textoDeCarga = carga.sobrecarga
            ? crearConIcono("span", "semana-carga semana-carga-exceso", "triangle-alert", textoCarga(dia))
            : crearElemento("span", "semana-carga cifra", textoCarga(dia));
        cabeza.append(crearElemento("strong", "", dia.es_vigente ? `${diaCorto(dia.fecha)}, hoy` : diaCorto(dia.fecha)), textoDeCarga);

        const cuerpo = crearElemento("div", "semana-cuerpo");
        cuerpo.style.height = `${alto}px`;
        cuerpo.style.setProperty("--alto-hora", `${60 * PX_POR_MINUTO}px`);
        cuerpo.append(...crearFranjasDelTurno(dia, rango));
        const bloques = dia.tramos
            .filter((tramo) => actividadDe(tramo) && fechaTexto(new Date(tramo.inicio)) === dia.fecha)
            .map((tramo) => crearBloque(tramo, dia, rango));
        cuerpo.append(...repartirEnCarriles(bloques));
        if (dia.es_vigente) {
            const ahora = new Date();
            const minuto = ahora.getHours() * 60 + ahora.getMinutes();
            if (minuto >= rango.desde && minuto <= rango.hasta) {
                const linea = crearElemento("span", "semana-ahora");
                linea.style.top = `${(minuto - rango.desde) * PX_POR_MINUTO}px`;
                linea.setAttribute("aria-label", `Ahora, ${hora(ahora)}`);
                cuerpo.append(linea);
            }
        }
        columna.append(cabeza, cuerpo);
        return columna;
    });
    cuadricula.replaceChildren(horas, ...columnas);
    cuadricula.hidden = false;
}

// ---------- Celular: un día a la vez, como la línea de tiempo de Hoy ----------

function pintarPestanas() {
    const contenedor = document.getElementById("semana-dias");
    contenedor.replaceChildren(...semana.dias.map((dia) => {
        const pestana = crearElemento("button", "semana-pestana");
        pestana.type = "button";
        // Botones que eligen el día: el elegido se anuncia como presionado.
        pestana.setAttribute("aria-pressed", String(dia.fecha === diaElegido));
        const carga = cargaDelDia(dia);
        // La carga corta, para que quepa en la pestaña: "4,4 h".
        const horas = (Math.round((carga.total / 60) * 10) / 10).toLocaleString("es-CO");
        pestana.append(
            crearElemento("strong", "", diaCorto(dia.fecha)),
            crearElemento("span", `cifra${carga.sobrecarga ? " semana-carga-exceso" : ""}`, carga.total ? `${horas} h` : "—"),
        );
        pestana.setAttribute("aria-label", `${fechaLarga(fechaDesdeTexto(dia.fecha))}, ${textoCarga(dia)}`);
        if (dia.es_vigente) {
            pestana.classList.add("semana-pestana-hoy");
        }
        pestana.addEventListener("click", () => {
            diaElegido = dia.fecha;
            pintar();
        });
        return pestana;
    }));
    contenedor.hidden = false;
}

function pintarDiaElegido() {
    const dia = semana.dias.find((d) => d.fecha === diaElegido) || semana.dias[0];
    const lista = document.getElementById("semana-dia");
    const nodos = [];
    const encabezado = crearElemento("li", "semana-dia-titulo");
    encabezado.append(crearElemento("h2", "", fechaLarga(fechaDesdeTexto(dia.fecha))),
        crearElemento("p", `texto-secundario${cargaDelDia(dia).sobrecarga ? " semana-carga-exceso" : ""}`,
            `${textoCarga(dia)}${dia.turno ? `. Turno de ${dia.turno.hora_inicio} a ${dia.turno.hora_fin}` : ""}`));
    nodos.push(encabezado);
    const tramos = dia.tramos.filter(actividadDe);
    if (!tramos.length) {
        nodos.push(crearElemento("li", "texto-secundario semana-vacio", "No hay actividades este día."));
    }
    for (const tramo of tramos) {
        const actividad = actividadDe(tramo);
        const zona = tramo.tipo === "FINALIZADA" ? "dia-pasado" : "dia-futuro";
        const nodo = crearElemento("li", `dia-nodo ${zona}`);
        const horaTexto = crearElemento("span", `dia-hora cifra ${tramo.aproximada && tramo.tipo === "PENDIENTE" ? "dia-hora-aproximada" : "dia-hora-exacta"}`, textoHora(tramo));
        const punto = crearElemento("span", `dia-punto${tramo.tipo === "FINALIZADA" ? " dia-punto-lleno" : ""}${tramo.tipo === "EN_CURSO" ? " dia-punto-curso" : ""}`);
        punto.setAttribute("aria-hidden", "true");
        // La misma fila de Hoy (operario-comun.js): mismas etiquetas y misma frase de datos.
        const tipo = { FINALIZADA: "hecha", EN_CURSO: "en-curso" }[tramo.tipo] || "pendiente";
        const fila = crearFilaDeActividad({
            actividad, tramo, tipo, vencida: tramo.vencida, siguiente: dia.es_vigente && tramo.siguiente,
            urgenteComoEtiqueta: true,
        }, cargadaEn, (elegida) => abrirDetalle(elegida, dia));
        nodo.append(horaTexto, punto, fila);
        nodos.push(nodo);
    }
    lista.replaceChildren(...nodos);
    lista.hidden = false;
}

// ---------- Pintar y cargar ----------

function pintar() {
    if (!semana) {
        return;
    }
    const angosta = PANTALLA_ANGOSTA.matches;
    document.getElementById("semana-cuadricula").hidden = angosta;
    document.getElementById("semana-dias").hidden = !angosta;
    document.getElementById("semana-dia").hidden = !angosta;
    if (angosta) {
        pintarPestanas();
        pintarDiaElegido();
    } else {
        pintarCuadricula();
    }
}

async function cargar() {
    const domingo = sumarDias(lunes, 6);
    const formato = { day: "numeric", month: "long" };
    document.getElementById("rango-semana").textContent =
        `Del ${lunes.toLocaleDateString("es-CO", formato)} al ${domingo.toLocaleDateString("es-CO", formato)}`;
    const mensaje = document.getElementById("mensaje");
    try {
        semana = await pedirApi(`/programacion-de-la-semana?desde=${fechaTexto(lunes)}&hasta=${fechaTexto(domingo)}`);
        actividades = semana.actividades;
        cargadaEn = Date.now();
        if (!semana.dias.some((dia) => dia.fecha === diaElegido)) {
            diaElegido = (semana.dias.find((dia) => dia.es_vigente) || semana.dias[0]).fecha;
        }
        mensaje.hidden = true;
        pintar();
    } catch (error) {
        mensaje.hidden = false;
        mensaje.textContent = `No pudimos cargar tu semana: ${error.message}`;
        mensaje.classList.add("mensaje-error");
    }
}

function moverSemana(semanas) {
    lunes = semanas === 0 ? inicioDeSemana(new Date()) : sumarDias(lunes, semanas * 7);
    if (semanas === 0) {
        diaElegido = null;
    }
    cargar();
}

iniciarPaginaProtegida(["OPERARIO"]).then(() => {
    const anterior = document.getElementById("semana-anterior");
    const siguiente = document.getElementById("semana-siguiente");
    anterior.insertAdjacentHTML("afterbegin", icono("chevron-left"));
    siguiente.insertAdjacentHTML("afterbegin", icono("chevron-right"));
    anterior.addEventListener("click", () => moverSemana(-1));
    siguiente.addEventListener("click", () => moverSemana(1));
    document.getElementById("semana-actual").addEventListener("click", () => moverSemana(0));
    PANTALLA_ANGOSTA.addEventListener("change", pintar);
    cargar();
});
