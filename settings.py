"""Compatibility import for legacy references to the former root settings module.

The active Django settings module is ``beatcloud.settings`` (see ``manage.py``).
Keep all environment loading, database configuration, and security settings in
that single module.
"""

from beatcloud.settings import *  # noqa: F401,F403
