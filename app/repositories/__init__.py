def crear_indices(db) -> None:
    """Crea los índices de las colecciones que los necesitan. Se puede llamar en cada arranque:
    MongoDB no hace nada si el índice ya existe con la misma definición."""
    from app.repositories.actividad_repository import ActividadRepository
    from app.repositories.asignacion_repository import AsignacionRepository
    from app.repositories.asistencia_repository import AsistenciaRepository
    from app.repositories.catalogo_repository import CatalogoRepository
    from app.repositories.ejecucion_repository import EjecucionRepository
    from app.repositories.orden_jornada_repository import OrdenJornadaRepository
    from app.repositories.proyecto_repository import ProyectoRepository
    from app.repositories.turno_repository import AsignacionTurnoRepository, TurnoRepository

    repositorios = (
        ActividadRepository(db), AsignacionRepository(db), EjecucionRepository(db),
        ProyectoRepository(db), CatalogoRepository(db), OrdenJornadaRepository(db),
        TurnoRepository(db), AsignacionTurnoRepository(db), AsistenciaRepository(db),
    )
    for repositorio in repositorios:
        repositorio.crear_indices()
