"""Shared guards for commands that create or delete local QA data."""

from django.core.management.base import CommandError


LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1"}


def validate_local_database(database, *, prefixes=("beatscloud_qa_",)):
    """Reject production, remote, SQLite, or ambiguously named databases."""
    name = str(database.get("NAME", ""))
    host = str(database.get("HOST", "") or "").lower()
    engine = str(database.get("ENGINE", ""))
    if not any(name.startswith(prefix) for prefix in prefixes):
        raise CommandError(
            "Safety stop: database name must start with " + " or ".join(prefixes)
        )
    if host not in LOCAL_HOSTS:
        raise CommandError("Safety stop: QA commands require a local database host.")
    if "postgresql" not in engine:
        raise CommandError("Safety stop: use the isolated PostgreSQL QA database.")
    return name
