from rich import print


def print_error(message: str) -> None:
    print(f"[red]{message}[/red]")


def print_success(message: str) -> None:
    print(f"[green]{message}[/green]")


def print_warning(message: str) -> None:
    print(f"[yellow]{message}[/yellow]")


def print_info(message: str) -> None:
    print(f"[blue]{message}[/blue]")
