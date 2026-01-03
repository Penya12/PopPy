"""Run app from command line interface."""
from __future__ import annotations

import json
from datetime import datetime

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

from poppy.core.events import EventCreate
from poppy.db.session import (
    DATABASE_URL,
    init_db_engine_and_sessionmaker,
    session_scope,
)
from poppy.services.event_handlers import create_event, list_todo, list_week

app = typer.Typer(help="poppy (POP): your Popeye-powered secretary")
console = Console()
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
    due_at: datetime | None = typer.Option(None, "--due-at", help="Due date for the event in ISO format"),
    completed_at: datetime | None = typer.Option(None, "--completed-at", help="Completion date for the event in ISO format"),
) -> None:
    """Add an event (action/decision/idea/paper/note/meeting)."""
    meta_obj = {}
    if meta:
        meta_obj = json.loads(meta)

    try:
        payload = EventCreate(
            kind=kind,
            text=text,
            why=why,
            tags=tags,
            meta=meta_obj,
            due_at=due_at,
            completed_at=completed_at,
            source="cli"
        )
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


@app.command()
def todo(
    *, show_pending_only: bool = typer.Option(False, "--pending-only/--all", help="Show only pending items or all items")  # noqa: FBT003
) -> None:
    """List all pending todo items (actions)."""
    with session_scope() as connected_session:
        events = list_todo(connected_session, pending_only=show_pending_only)

    if not events:
        console.print("No todo items found", style="bold magenta")
        return

    table = Table(title="Todo List", title_style="bold blue", border_style="cyan", header_style="bold magenta", show_lines=True)
    table.add_column("ID", style="dim", width=6)
    table.add_column("Created At", style="dim", width=20)
    table.add_column("Due At", style="bold", width=20)
    table.add_column("Text", style="white")
    for ev in events:
        due_str = ev.due_at.isoformat(timespec="minutes") if ev.due_at else "no due date"
        table.add_row(str(ev.id), ev.created_at.isoformat(timespec="minutes"), due_str, ev.text)
    console.print(table)


@app.callback()
def main() -> None:
    """Initialize the DB engine and sessionmaker for CLI commands. Runs for every command."""
    # runs for every command
    init_db_engine_and_sessionmaker(DATABASE_URL)
