"""Arma los servicios de actividades con sus repositorios. Es el único lugar que sabe qué
necesita cada uno: las rutas y las pruebas piden aquí los servicios ya construidos."""
from types import SimpleNamespace

from app.repositories.actividad_repository import ActividadRepository
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.asistencia_repository import AsistenciaRepository
from app.repositories.catalogo_repository import CatalogoRepository
from app.repositories.ejecucion_repository import EjecucionRepository
from app.repositories.empresa_repository import EmpresaRepository
from app.repositories.orden_jornada_repository import OrdenJornadaRepository
from app.repositories.proyecto_repository import ProyectoRepository
from app.repositories.requerimiento_repository import RequerimientoRepository
from app.repositories.turno_repository import AsignacionTurnoRepository, TurnoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.actividad_service import ActividadService
from app.services.asistencia_service import AsistenciaService
from app.services.carga_service import CargaService
from app.services.catalogo_service import CatalogoService
from app.services.cierre_jornada_service import CierreJornadaService
from app.services.ejecucion_service import EjecucionService
from app.services.programacion_service import ProgramacionService
from app.services.proyecto_service import ProyectoService
from app.services.turno_service import TurnoService


def construir_servicios(db, reloj=None) -> SimpleNamespace:
    """Devuelve los servicios como atributos: actividades, ejecucion, carga, proyectos, catalogos,
    cierre_jornada, programacion, turnos y asistencia.
    "reloj" es para las pruebas; sin él, cada servicio usa la hora del servidor."""
    actividad_repository = ActividadRepository(db)
    asignacion_repository = AsignacionRepository(db)
    ejecucion_repository = EjecucionRepository(db)
    proyecto_repository = ProyectoRepository(db)
    usuario_repository = UsuarioRepository(db)
    empresa_repository = EmpresaRepository(db)

    # El cierre de jornada no depende de ningún otro servicio: los demás lo reciben y lo llaman
    # antes de leer o cambiar las actividades de una empresa.
    cierre_jornada = CierreJornadaService(
        actividad_repository, asignacion_repository, ejecucion_repository, empresa_repository, reloj=reloj,
    )
    # Los turnos dan la capacidad de cada operario por jornada (carga y programación del día).
    turnos = TurnoService(
        TurnoRepository(db), AsignacionTurnoRepository(db), usuario_repository, empresa_repository, reloj=reloj,
    )
    asistencia = AsistenciaService(
        AsistenciaRepository(db), turnos, usuario_repository, empresa_repository, reloj=reloj,
    )
    catalogos = CatalogoService(CatalogoRepository(db))
    carga = CargaService(actividad_repository, asignacion_repository, usuario_repository, cierre_jornada, turnos)
    actividades = ActividadService(
        actividad_repository, RequerimientoRepository(db), asignacion_repository,
        usuario_repository, ejecucion_repository, empresa_repository, carga,
        proyecto_repository, catalogos, cierre_jornada, reloj=reloj,
    )
    ejecucion = EjecucionService(
        ejecucion_repository, actividad_repository, asignacion_repository, actividades, catalogos,
        cierre_jornada, reloj=reloj,
    )
    proyectos = ProyectoService(proyecto_repository, actividad_repository, actividades, cierre_jornada, reloj=reloj)
    programacion = ProgramacionService(
        actividades, OrdenJornadaRepository(db), empresa_repository, usuario_repository, turnos, asistencia,
        reloj=reloj,
    )
    return SimpleNamespace(
        actividades=actividades, ejecucion=ejecucion, carga=carga, proyectos=proyectos, catalogos=catalogos,
        cierre_jornada=cierre_jornada, programacion=programacion, turnos=turnos, asistencia=asistencia,
    )
