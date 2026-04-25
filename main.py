from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from chat_loop import ChatLoop
from config import ensure_config
from llm_client import LLMClient


def show_title(console: Console) -> None:
    title = Text()
    title.append("八股作文万花筒\n", style="bold cyan")
    title.append("一个专门写小学作文的命令行小工具", style="white")
    console.print(Panel(title, border_style="cyan", expand=False))


def main() -> None:
    console = Console()
    show_title(console)
    config = ensure_config(console)
    client = LLMClient(config=config)
    ChatLoop(console=console, client=client, config=config).run()


if __name__ == "__main__":
    main()
