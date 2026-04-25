from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from config import AppConfig, build_config_table
from llm_client import LLMClient, LLMClientError
from prompts import SYSTEM_PROMPT


MAX_HISTORY_MESSAGES = 16


class ChatLoop:
    def __init__(self, console: Console, client: LLMClient, config: AppConfig) -> None:
        self.console = console
        self.client = client
        self.config = config
        self.history: list[dict[str, str]] = []

    def run(self) -> None:
        self.console.print("[dim]输入 /help 查看帮助，输入 /exit 或 /quit 退出。[/dim]")
        while True:
            try:
                user_input = self.console.input("[bold green]小学生作文需求 > [/bold green]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]已退出。[/yellow]")
                return

            text = user_input.strip()
            if not text:
                self.console.print("[yellow]请输入作文需求，或输入 /help 查看帮助。[/yellow]")
                continue

            if self._handle_command(text):
                continue

            self._send_user_message(text)

    def _handle_command(self, text: str) -> bool:
        command = text.lower()
        if command in {"/exit", "/quit"}:
            self.console.print("[yellow]已退出。[/yellow]")
            raise SystemExit(0)
        if command == "/help":
            self._show_help()
            return True
        if command == "/config":
            self.console.print(build_config_table(self.config))
            return True
        if command == "/clear":
            self.history.clear()
            self.console.print("[green]已清空当前对话上下文。[/green]")
            return True
        if command.startswith("/"):
            self.console.print("[red]未知命令。输入 /help 查看可用命令。[/red]")
            return True
        return False

    def _send_user_message(self, text: str) -> None:
        self.history.append({"role": "user", "content": text})
        self._trim_history()
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *self.history]

        try:
            with self.console.status("[cyan]正在请万花筒打磨作文...[/cyan]", spinner="dots"):
                reply = self.client.chat(messages)
        except LLMClientError as exc:
            self.console.print(f"[red]请求失败：{exc}[/red]")
            self.history.pop()
            return

        self.history.append({"role": "assistant", "content": reply})
        self._trim_history()
        self.console.print(Panel(Markdown(reply), title="八股作文万花筒", border_style="cyan"))

    def _trim_history(self) -> None:
        if len(self.history) > MAX_HISTORY_MESSAGES:
            self.history = self.history[-MAX_HISTORY_MESSAGES:]

    def _show_help(self) -> None:
        help_text = """
可用命令：

- `/help`：查看帮助
- `/config`：查看当前配置状态（不会明文显示 API Key）
- `/clear`：清空当前对话上下文
- `/exit` 或 `/quit`：退出程序

可以直接输入小学作文需求，例如：

- 写一篇五年级作文《难忘的一天》，500 字左右
- 帮我把这段写景作文润色得更自然
- 写一篇三年级日记，主题是第一次学骑自行车
- 把这篇作文缩写到 300 字，并保留原意
"""
        self.console.print(Panel(Markdown(help_text), title="帮助", border_style="green"))
