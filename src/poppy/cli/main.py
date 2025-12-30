"""Run app from command line interface."""
from __future__ import annotations

import json
import typer
from pydantic import ValidationError

from poppy.db.session import get_session
from poppy.core.events import EventCreate
from poppy.services.event_handlers import create_event, list_week

app = typer.Typer(help="poppy (POP): your Popeye-powered secretary")


@app.command()
def add(
    kind: str = typer.Option(
        ..., "--kind", help="Available kinds: action, decision, idea, paper, note, meeting"
    ),
    text: str = typer.Argument(...),
    why: str | None = typer.Option(None, "--why"),
    tags: list[str] = typer.Option(
        [], "--tags", help="Repeat --tags for multiple values (e.g. --tags foo --tags bar)"
    ),
    meta: str | None = typer.Option(None, "--meta", help="JSON string, e.g. '{\"url\": \"...\"}'"),
):
    """
    Add an event (action/decision/idea/paper/note/meeting).
    """
    meta_obj = {}
    if meta:
        meta_obj = json.loads(meta)

    try:
        payload = EventCreate(kind=kind, text=text, why=why, tags=tags, meta=meta_obj, source="cli")
    except ValidationError as e:
        typer.echo(str(e))
        raise typer.Exit(code=2)

    session = get_session()
    try:
        ev = create_event(session, payload)
        typer.echo(f"Saved #{ev.id} [{ev.kind}] {ev.text}")
    finally:
        session.close()


@app.command()
def week():
    """
    Show this week's events (UTC week).
    """
    session = get_session()
    try:
        events = list_week(session)
        for ev in events:
            ts = ev.created_at.isoformat(timespec="minutes")
            typer.echo(f"{ts}  [{ev.kind}]  {ev.text}")
    finally:
        session.close()
