from enum import Enum


class Rol(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMINISTRADOR = "ADMINISTRADOR"
    OPERARIO = "OPERARIO"


class Prioridad(str, Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"  # Interrumpe la actividad que el operario tenga en curso.

    @property
    def peso(self) -> int:
        """Orden numérico de la prioridad: se ordena por este valor, nunca comparando textos."""
        return _PESO_PRIORIDAD[self.value]


_PESO_PRIORIDAD = {"BAJA": 1, "MEDIA": 2, "ALTA": 3, "URGENTE": 4}


class Categoria(str, Enum):
    """Tipos de trabajo que sirven para cualquier empresa (alcance, Sección 5.1)."""
    OPERACION = "OPERACION"             # El trabajo principal del área.
    ATENCION = "ATENCION"               # Atender a clientes o a personas.
    ADMINISTRATIVA = "ADMINISTRATIVA"   # Registros, trámites e informes.
    REVISION = "REVISION"               # Controlar, verificar o inspeccionar.
    TRASLADO = "TRASLADO"               # Mover, entregar o despachar.


class EstadoActividad(str, Enum):
    PENDIENTE = "PENDIENTE"            # Sin operarios asignados.
    ASIGNADA = "ASIGNADA"              # Con operarios; ninguno la tiene en curso ni pausada.
    EN_EJECUCION = "EN_EJECUCION"      # Al menos un operario la tiene en curso.
    PAUSADA = "PAUSADA"                # Nadie la tiene en curso y al menos uno la pausó.
    DEVUELTA = "DEVUELTA"              # El último operario asignado la devolvió al Administrador.
    COMPLETADA = "COMPLETADA"          # Final: todos los asignados la finalizaron.
    NO_REALIZADA = "NO_REALIZADA"      # Final: era de hora fija y no se terminó en su día.
    CANCELADA = "CANCELADA"            # Final: la canceló el Administrador, con motivo.

    @property
    def es_final(self) -> bool:
        """Un estado final ya no cambia: la actividad no se edita, no se reasigna y no se cancela."""
        return self in (EstadoActividad.COMPLETADA, EstadoActividad.NO_REALIZADA, EstadoActividad.CANCELADA)


class EstadoEjecucion(str, Enum):
    """La ejecución nace cuando el operario inicia, por eso no existe un estado "no iniciada"."""
    EN_PROGRESO = "EN_PROGRESO"
    PAUSADA = "PAUSADA"
    FINALIZADA = "FINALIZADA"          # El operario la terminó.
    CERRADA = "CERRADA"                # Terminó sin completarse: actividad cancelada, no realizada u operario retirado.

    @property
    def esta_abierta(self) -> bool:
        return self in (EstadoEjecucion.EN_PROGRESO, EstadoEjecucion.PAUSADA)


class EstadoPresencia(str, Enum):
    """Si la persona está en su jornada (alcance, Sección 5.1). Lo calcula presencia_en_jornada; no se guarda."""
    SIN_TURNO = "SIN_TURNO"                    # No tiene turno ese día y no marcó entrada.
    POR_LLEGAR = "POR_LLEGAR"                  # Tiene turno y todavía no pasa la tolerancia de la entrada.
    LLEGADA_TARDE = "LLEGADA_TARDE"            # Pasó la tolerancia sin entrada: aviso de posible ausencia.
    EN_TURNO = "EN_TURNO"                      # Marcó entrada y no ha salido.
    TIEMPO_ADICIONAL = "TIEMPO_ADICIONAL"      # Sigue sin salir después del fin de su turno.
    JORNADA_TERMINADA = "JORNADA_TERMINADA"    # Marcó la salida.
    NO_VINO = "NO_VINO"                        # Su turno terminó y nunca marcó entrada.
    SIN_SALIDA = "SIN_SALIDA"                  # Una jornada anterior quedó sin marcar la salida.


class EstadoCarga(str, Enum):
    """Cuánto trabajo tiene una persona en su jornada (alcance, Sección 5.1). Lo calcula estado_de_carga."""
    SOBRECARGADO = "SOBRECARGADO"      # Pasa del 100 % de su capacidad.
    CON_ESPACIO = "CON_ESPACIO"        # Le queda 1 hora libre o más.
    NORMAL = "NORMAL"


class EstadoReporte(str, Enum):
    """Un reporte de actividad espera la revisión del Administrador (alcance, Sección 5.1)."""
    PENDIENTE = "PENDIENTE"            # Por revisar: todavía no es trabajo del día.
    CONVERTIDO = "CONVERTIDO"          # Final: el Administrador creó una actividad con él.
    DESCARTADO = "DESCARTADO"          # Final: el Administrador lo descartó, con motivo.


class EstadoAsignacion(str, Enum):
    """Una asignación no se borra: se cierra, y queda como historial."""
    ACTIVA = "ACTIVA"
    DEVUELTA = "DEVUELTA"              # El operario devolvió la actividad antes de iniciarla.
    RETIRADA = "RETIRADA"              # El Administrador le quitó la actividad.


# Motivos de pausa que el sistema conoce. Los demás los escribe el operario en "Otro" y quedan
# guardados en el catálogo de su empresa (alcance, Sección 5.1).
MOTIVO_PAUSA_URGENTE = "Actividad urgente"
MOTIVO_PAUSA_HORA_FIJA = "Actividad de hora fija"
MOTIVO_PAUSA_FIN_JORNADA = "Fin de jornada"
MOTIVOS_PAUSA_FIJOS = (MOTIVO_PAUSA_URGENTE, MOTIVO_PAUSA_HORA_FIJA, MOTIVO_PAUSA_FIN_JORNADA)
# Una de hora fija no se pausa, salvo para detenerla por una emergencia, con uno de estos motivos.
MOTIVOS_DETENER_HORA_FIJA = ("Emergencia", "Falla del equipo")

# Motivos para devolver una actividad. Esta lista es fija; con "Otro" el operario escribe el suyo.
MOTIVOS_DEVOLUCION = (
    "Falta información",
    "Me la asignaron por error",
    "Falta herramienta o material",
    "El equipo no está disponible",
)


class TipoCatalogo(str, Enum):
    """Listas por empresa que se van llenando con lo que escriben las personas: los motivos (con
    "Otro") y las sugerencias de la información de la actividad."""
    MOTIVO_PAUSA = "MOTIVO_PAUSA"
    MOTIVO_CANCELACION = "MOTIVO_CANCELACION"
    HERRAMIENTA = "HERRAMIENTA"
    EQUIPO = "EQUIPO"
    PRECAUCION = "PRECAUCION"
    CONTACTO = "CONTACTO"
