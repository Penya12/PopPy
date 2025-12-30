"""Run app from command line interface."""
from __future__ import annotations

import json

import typer
from pydantic import ValidationError

from poppy.core.events import EventCreate
from poppy.db.session import (
    DATABASE_URL,
    init_db_engine_and_sessionmaker,
    session_scope,
)
from poppy.services.event_handlers import create_event, list_week

app = typer.Typer(help="poppy (POP): your Popeye-powered secretary")
DEFAULT_TAGS = typer.Option([], "--tags", help="Repeat --tags for multiple values (e.g. --tags foo --tags bar)")


@app.command()
def add(
    kind: str = typer.Option(
        ..., "--kind", help="Available kinds: action, decision, idea, paper, note, meeting"
    ),
    text: str = typer.Argument(...),
    why: str | None = typer.Option(None, "--why"),
    tags: list[str] | None = DEFAULT_TAGS,
    meta: str | None = typer.Option(None, "--meta", help="JSON string, e.g. '{\"url\": \"...\"}'"),
) -> None:
    """Add an event (action/decision/idea/paper/note/meeting)."""
    meta_obj = {}
    if meta:
        meta_obj = json.loads(meta)

    try:
        payload = EventCreate(kind=kind, text=text, why=why, tags=tags, meta=meta_obj, source="cli")
    except ValidationError as e:
        typer.echo(str(e))
        raise typer.Exit(code=2) from e

    with session_scope() as connected_session:
        ev = create_event(connected_session, payload)
        typer.echo(f"Saved #{ev.id} [{ev.kind}] {ev.text}")


@app.command()
def week() -> None:
    """Show this week's events (UTC week)."""
    with session_scope() as connected_session:
        events = list_week(connected_session)
    for ev in events:
        ts = ev.created_at.isoformat(timespec="minutes")
        if ev.why:
            typer.echo(f"{ts}  [{ev.kind}]  {ev.text} because {ev.why}")
        else:
            typer.echo(f"{ts}  [{ev.kind}]  {ev.text}")


@app.callback()
def main() -> None:
    """Initialize the DB engine and sessionmaker for CLI commands. Runs for every command."""
    # runs for every command
    init_db_engine_and_sessionmaker(DATABASE_URL)
