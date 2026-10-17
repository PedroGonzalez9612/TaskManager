// Vista "Inicio" del Operario (alcance, Sección 6.1): la página que lo recibe después de iniciar
// sesión. Muestra la hora con la barra del turno, la barra de la jornada, cuántas actividades tiene y
// cuál sigue. Sus acciones dependen de la asistencia: antes de la entrada, "Marcar entrada" (y pasa a
// Hoy) o "Ver mi día" en modo de lectura; durante el día, "Ir a mi día" y, al final, "Marcar salida";
// después de la salida, el cierre de la jornada.

const RUTA_HOY = "/static/operario/index.html";

let programacion = null;
let nombreOperario = "";
let reloj = null;

// "Buenos días" hasta el mediodía, "Buenas tardes" hasta las 7 de la noche y después "Buenas noches".
function saludo() {
    const hora = new Date().getHours();
    let parte = "Buenas noches";
    if (hora >= 5 && hora < 12) {
        parte = "Buenos días";
    } else if (hora >= 12 && hora < 19) {
        parte = "Buenas tardes";
    }
    return `${parte}, ${nombreOperario}`;
}

function crearDatos(filas) {
    const datos = crearElemento("dl", "portada-datos");
    for (const [nombre, valor] of filas) {
        datos.append(crearElemento("dt", "", nombre), crearElemento("dd", "cifra", valor));
    }
    return datos;
}

function porId() {
    return new Map(programacion.actividades.map((actividad) => [actividad.id, actividad]));
}

// Lo que sigue: la actividad en curso o la siguiente por hacer, con su hora. Se toca para ir a Hoy.
function crearLoQueSigue() {
    const actividades = porId();
    const tramo = programacion.tramos.find((t) => t.tipo === "EN_CURSO")
        || programacion.tramos.find((t) => t.siguiente);
    if (!tramo) {
        return [];
    }
    const actividad = actividades.get(tramo.actividad_id);
    const enlace = crearElemento("a", "inicio-sigue");
    enlace.href = RUTA_HOY;
    const textos = crearElemento("span", "inicio-sigue-textos");
    const encabezado = tramo.tipo === "EN_CURSO" ? "En curso" : `Lo que sigue, ${tramo.aproximada ? "~" : ""}${horaDeMomento(tramo.inicio)}`;
    textos.append(
        crearElemento("span", "inicio-sigue-etiqueta cifra", encabezado),
        crearElemento("strong", "", actividad.titulo),
    );
    enlace.append(crearSenalPrioridad(actividad.prioridad), textos);
    enlace.insertAdjacentHTML("beforeend", icono("chevron-right"));
    return [enlace];
}

function crearJornada() {
    const pendientes = programacion.tramos.filter((tramo) => tramo.tipo !== "FINALIZADA").length;
    const hechas = programacion.tramos.length - pendientes;
    let resumen = "No tienes actividades programadas para hoy.";
    if (programacion.tramos.length) {
        resumen = `${hechas} de ${programacion.tramos.length} actividades finalizadas`;
    }
    return [crearElemento("p", "inicio-nota cifra", resumen), ...crearLoQueSigue()];
}

// Después de la salida: las marcas, el tiempo trabajado y lo que quedó sin finalizar.
function crearCierre() {
    const { tramos, resumen, asistencia } = programacion;
    const finalizadas = tramos.filter((tramo) => tramo.tipo === "FINALIZADA").length;
    const sinFinalizar = tramos.length - finalizadas;
    const contenido = [
        crearElemento("h2", "inicio-subtitulo", "Tu jornada terminó"),
        crearDatos([
            ["Entrada", horaDeMomento(asistencia.entrada)],
            ["Salida", horaDeMomento(asistencia.salida)],
            ["Tiempo presente", duracionTexto(asistencia.minutos_presente)],
            ["Tiempo en actividades", duracionTexto(resumen.trabajado_min)],
            ["Actividades finalizadas", `${finalizadas} de ${tramos.length}`],
        ]),
    ];
    if (sinFinalizar) {
        const cuantas = sinFinalizar === 1 ? "Quedó 1 actividad sin finalizar." : `Quedaron ${sinFinalizar} actividades sin finalizar.`;
        contenido.push(crearConIcono("p", "aviso aviso-info", "info", `${cuantas} Las de horario flexible pasan a tu siguiente jornada.`));
    }
    contenido.push(crearElemento("p", "texto-suave", "Si marcaste la salida por error, pide a tu Administrador que la corrija."));
    return contenido;
}

function crearEnlace(clase, iconoNombre, texto) {
    const enlace = crearConIcono("a", clase, iconoNombre, texto);
    enlace.href = RUTA_HOY;
    return enlace;
}

// Las acciones del momento: una sola principal (alcance, Sección 6.2).
function crearAcciones(estado) {
    const acciones = crearElemento("div", "inicio-acciones");
    if (estado === "inicio") {
        const entrada = crearConIcono("button", "boton boton-bloque", "log-in", "Marcar entrada");
        entrada.type = "button";
        entrada.addEventListener("click", () => marcarAsistencia(entrada, "/asistencia/entrada", "Entrada registrada.",
            async () => { window.location.href = RUTA_HOY; }));
        acciones.append(entrada, crearEnlace("boton-texto", "list-checks", "Ver mi día sin marcar la entrada"));
        if (programacion.asistencia && programacion.asistencia.jornada !== programacion.fecha) {
            acciones.append(crearElemento("p", "texto-suave", "Tu jornada anterior quedó sin marca de salida. Tu Administrador la corrige."));
        }
    } else if (estado === "dia") {
        acciones.append(crearEnlace("boton boton-bloque", "list-checks", "Ir a mi día"));
    } else {
        acciones.append(crearEnlace("boton-secundario boton-bloque", "list-checks", "Ver mi día"));
    }
    return acciones;
}

function pintar() {
    const estado = estadoDeJornada(programacion);
    document.getElementById("saludo").textContent = saludo();
    reloj = crearCintaDelDia(programacion);
    const panel = document.getElementById("inicio-panel");
    panel.replaceChildren(
        reloj.elemento,
        ...(estado === "cierre" ? crearCierre() : crearJornada()),
        crearAcciones(estado),
    );
    panel.hidden = false;
    pintarAvisoDelTurno(document.getElementById("aviso-turno"), programacion);

    // "Marcar salida" va al final, separado de lo demás (alcance, Sección 6.1).
    const salida = document.getElementById("inicio-salida");
    salida.hidden = estado !== "dia";
    if (estado === "dia") {
        const boton = crearConIcono("button", "boton-secundario", "log-out", "Marcar salida");
        boton.type = "button";
        boton.addEventListener("click", () => abrirSalida(programacion, cargar));
        salida.replaceChildren(crearElemento("p", "", "¿Terminaste tu jornada?"), boton);
    }
}

async function cargar() {
    const mensaje = document.getElementById("mensaje");
    try {
        programacion = await pedirApi("/programacion-del-dia");
        mensaje.hidden = true;
        pintar();
    } catch {
        mensaje.hidden = false;
        mensaje.textContent = "No pudimos cargar tu jornada. Revisa tu conexión e inténtalo de nuevo.";
        mensaje.classList.add("mensaje-error");
    }
}

iniciarPaginaProtegida(["OPERARIO"]).then((usuario) => {
    nombreOperario = usuario.nombre.split(" ")[0];
    const fecha = fechaLarga(new Date());
    document.getElementById("fecha-inicio").textContent = fecha.charAt(0).toUpperCase() + fecha.slice(1);
    // La hora y la barra del turno se mueven solas; los avisos se revisan cada medio minuto.
    setInterval(() => reloj?.actualizar(), 1000);
    setInterval(() => programacion && pintarAvisoDelTurno(document.getElementById("aviso-turno"), programacion), 30000);
    cargar();
});
