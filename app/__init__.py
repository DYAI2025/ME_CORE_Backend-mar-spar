"""Alias module to maintain backward compatibility.

This file allows legacy imports using the ``app`` package to resolve
to the current ``backend`` package structure. It maps the module
name ``app`` to ``backend`` at runtime so that statements like
``from app.services import ...`` continue to function.
"""

import sys
import backend as _backend

# Expose the backend package under the name "app"
sys.modules[__name__] = _backend
