// Funciones compartidas para hablar con la API REST de GestLab.
// Todas las pantallas usan estas funciones en lugar de llamar a fetch directamente.

const RUTA_LOGIN = "/static/login.html";

// Pantalla de inicio de cada rol después de iniciar sesión.
const INICIO_POR_ROL = {
    SUPERADMIN: "/static/superadmin/empresas.html",
    ADMINISTRADOR: "/static/admin/equipo.html",
    OPERARIO: "/static/operario/index.html",
};

// El servidor rechaza las peticiones que cambian datos si no traen este encabezado: así sabe que
// vienen de esta interfaz y no de otra página (protección contra CSRF, app/utils/seguridad.py).
const ENCABEZADO_PROPIO = { "X-Requested-With": "GestLab" };

async function pedirApi(ruta, opciones = {}) {
    // Con archivos (FormData) el navegador pone su propio Content-Type; con JSON lo ponemos nosotros.
    const esArchivo = opciones.body instanceof FormData;
    const respuesta = await fetch(ruta, {
        headers: esArchivo ? ENCABEZADO_PROPIO : { ...ENCABEZADO_PROPIO, "Content-Type": "application/json" },
        ...opciones,
    });

    // Sesión vencida o inexistente: se vuelve al login (salvo que ya estemos en él).
    if (respuesta.status === 401 && window.location.pathname !== RUTA_LOGIN) {
        window.location.href = RUTA_LOGIN;
        throw new Error("Debes iniciar sesión");
    }

    if (!respuesta.ok) {
        let mensaje = `Error ${respuesta.status}`;
        try {
            const cuerpo = await respuesta.json();
            mensaje = cuerpo.error || mensaje;
        } catch (e) {
            // La respuesta no traía JSON; se deja el mensaje genérico.
        }
        throw new Error(mensaje);
    }

    if (respuesta.status === 204) {
        return null;
    }
    return respuesta.json();
}

function enviarJson(ruta, metodo, datos) {
    return pedirApi(ruta, { method: metodo, body: JSON.stringify(datos) });
}

// Convierte los campos de texto de un formulario en un objeto { nombre_campo: valor }.
// Los archivos se ignoran aquí: se envían aparte con subirLogo.
function datosFormulario(formulario) {
    const datos = {};
    for (const [campo, valor] of new FormData(formulario).entries()) {
        if (!(valor instanceof File)) {
            datos[campo] = valor;
        }
    }
    return datos;
}

// ---------- Logo y límites de la empresa ----------

const TAMANO_MAXIMO_LOGO = 512 * 1024;
const TIPOS_LOGO = new Set(["image/png", "image/jpeg", "image/webp"]);

// Revisa el archivo en el navegador antes de enviarlo (el servidor vuelve a validarlo).
function validarArchivoLogo(archivo) {
    if (!archivo) {
        return null;
    }
    if (!TIPOS_LOGO.has(archivo.type)) {
        return "El logo debe ser una imagen PNG, JPG o WEBP.";
    }
    if (archivo.size > TAMANO_MAXIMO_LOGO) {
        return "El logo no puede pesar más de 512 KB.";
    }
    return null;
}

function subirLogo(empresaId, archivo) {
    const datos = new FormData();
    datos.append("logo", archivo);
    return pedirApi(`/empresas/${encodeURIComponent(empresaId)}/logo`, { method: "PUT", body: datos });
}

// La URL cambia con cada carga para que el navegador no muestre un logo viejo tras cambiarlo.
function urlLogo(empresaId) {
    return `/empresas/${encodeURIComponent(empresaId)}/logo?v=${Date.now()}`;
}

// Texto del tipo "3 de 10" para los límites de usuarios. Sin límite definido: "3 (sin límite)".
function textoLimite(actuales, limite) {
    return limite == null ? `${actuales} (sin límite)` : `${actuales} de ${limite}`;
}

function limiteAlcanzado(empresa, rol) {
    const campo = rol === "ADMINISTRADOR" ? "limite_administradores" : "limite_operarios";
    const limite = empresa[campo];
    return limite != null && (empresa.usuarios_actuales[rol] || 0) >= limite;
}

// ---------- Catálogos: mismos valores que los enums del servidor (app/models/enums.py) ----------

// Peso numérico de cada prioridad: se ordena por número, nunca comparando textos.
const PESO_PRIORIDAD = {
    URGENTE: 4,
    ALTA: 3,
    MEDIA: 2,
    BAJA: 1,
};

const NOMBRE_PRIORIDAD = {
    URGENTE: "Urgente",
    ALTA: "Alta",
    MEDIA: "Media",
    BAJA: "Baja",
};

const NOMBRE_ESTADO = {
    PENDIENTE: "Sin asignar",
    ASIGNADA: "Por iniciar",
    EN_EJECUCION: "En curso",
    PAUSADA: "Pausada",
    DEVUELTA: "Devuelta",
    COMPLETADA: "Finalizada",
    NO_REALIZADA: "No realizada",
    CANCELADA: "Cancelada",
};

const NOMBRE_CATEGORIA = {
    PRODUCCION: "Producción",
    MANTENIMIENTO: "Mantenimiento",
    CALIDAD: "Calidad",
    LIMPIEZA: "Limpieza",
    LOGISTICA: "Logística",
};

const NOMBRE_ROL = {
    SUPERADMIN: "Superadmin",
    ADMINISTRADOR: "Administrador",
    OPERARIO: "Operario",
};

// ---------- Fechas y tiempos ----------

// Fecha local como texto "AAAA-MM-DD" (el formato que usa la API).
function fechaTexto(fecha) {
    const mes = String(fecha.getMonth() + 1).padStart(2, "0");
    const dia = String(fecha.getDate()).padStart(2, "0");
    return `${fecha.getFullYear()}-${mes}-${dia}`;
}

// Convierte "AAAA-MM-DD" (y opcionalmente "HH:MM") en una fecha local.
function fechaDesdeTexto(fecha, hora = "00:00") {
    const [anio, mes, dia] = fecha.split("-").map(Number);
    const [horas, minutos] = hora.split(":").map(Number);
    return new Date(anio, mes - 1, dia, horas, minutos);
}

function sumarDias(fecha, dias) {
    const copia = new Date(fecha);
    copia.setDate(copia.getDate() + dias);
    return copia;
}

// Lunes de la semana de una fecha.
function inicioDeSemana(fecha) {
    const diaSemana = (fecha.getDay() + 6) % 7;     // lunes = 0 ... domingo = 6
    const lunes = sumarDias(fecha, -diaSemana);
    lunes.setHours(0, 0, 0, 0);
    return lunes;
}

// 95 -> "1 h 35 min"; 60 -> "1 h"; 45 -> "45 min".
function duracionTexto(minutos) {
    const horas = Math.floor(minutos / 60);
    const resto = Math.round(minutos % 60);
    if (horas && resto) {
        return `${horas} h ${resto} min`;
    }
    return horas ? `${horas} h` : `${resto} min`;
}

// "miércoles 7 de octubre"
function fechaLarga(fecha) {
    return fecha.toLocaleDateString("es-CO", { weekday: "long", day: "numeric", month: "long" });
}

// "mié 7 oct"
function fechaCorta(fecha) {
    const dia = fecha.toLocaleDateString("es-CO", { weekday: "short" }).replace(".", "");
    const mes = fecha.toLocaleDateString("es-CO", { month: "short" }).replace(".", "");
    return `${dia} ${fecha.getDate()} ${mes}`;
}
