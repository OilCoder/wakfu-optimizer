"""Optimizador de builds de Wakfu.

Selecciona la combinación de ítems que maximiza el daño de una build sujeta a
restricciones (clase, nivel, rareza, breakpoints, ítems fijos), con garantía de
optimalidad dentro de un proxy lineal (solver CP-SAT) y un evaluador de daño no lineal.
"""

from __future__ import annotations

__version__ = "0.1.0"
