import typer

app = typer.Typer(help="Personal Operations Platform")

@app.command()
def hello():
    """Sanity check."""
    typer.echo("POP is alive")

if __name__ == "__main__":
    app()
