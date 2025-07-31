"""
Database package for PythonTecnica_SOME

Aquest paquet conté les classes i utilitats per gestionar
les connexions i operacions amb la base de dades PostgreSQL.
"""

from .quality_measurement_adapter import QualityMeasurementDBAdapter

__all__ = ['QualityMeasurementDBAdapter']
