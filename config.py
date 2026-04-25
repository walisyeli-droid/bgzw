from __future__ import annotations

import os
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table


DEFAULT_API_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
ENV_FILE = Path(".env")


@dataclass
class AppConfig:
    api_base_url: str
    api_key: str
    model: str

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key.strip())


def _clean_url(url: str) -> str:
    return (url or DEFAULT_API_BASE_URL).strip().rstrip("/")


def _read_config_from_env() -> AppConfig:
    load_dotenv(ENV_FILE, override=False)
    return AppConfig(
        api_base_url=_clean_url(os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL)),
        api_key=os.getenv("API_KEY", "").strip(),
        model=(os.getenv("MODEL", DEFAULT_MODEL) or DEFAULT_MODEL).strip(),
    )


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return "未配置"
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def build_config_table(config: AppConfig) -> Table:
    table = Table(title="当前配置状态", show_header=True, header_style="bold cyan")
    table.add_column("配置项")
    table.add_column("状态")
    table.add_row("API_BASE_URL", config.api_base_url)
    table.add_row("API_KEY", mask_api_key(config.api_key))
    table.add_row("MODEL", config.model)
    return table


def _ask(console: Console, prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    value = console.input(f"[bold cyan]{prompt}{suffix}[/bold cyan]: ").strip()
    return value if value else (default or "")


def _ask_yes_no(console: Console, prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    value = console.input(f"[bold cyan]{prompt} ({hint})[/bold cyan]: ").strip().lower()
    if not value:
        return default
    return value in {"y", "yes", "是", "好", "保存"}


def _prompt_for_config(console: Console, existing: AppConfig) -> AppConfig:
    console.print("[yellow]首次运行或配置不完整，请填写 API 配置。API Key 输入时不会显示。[/yellow]")
    api_base_url = _ask(console, "API_BASE_URL", existing.api_base_url or DEFAULT_API_BASE_URL)
    model = _ask(console, "MODEL", existing.model or DEFAULT_MODEL)
    console.print("[dim]如需清空 API Key，直接回车即可。[/dim]")
    api_key = getpass("API_KEY: ").strip()
    config = AppConfig(api_base_url=_clean_url(api_base_url), api_key=api_key, model=model or DEFAULT_MODEL)
    if _ask_yes_no(console, "是否保存到 .env", default=True):
        save_config(config)
        console.print("[green]配置已保存到 .env。[/green]")
    return config


def save_config(config: AppConfig) -> None:
    lines = [
        f"API_BASE_URL={config.api_base_url}",
        f"API_KEY={config.api_key}",
        f"MODEL={config.model}",
        "",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")


def ensure_config(console: Console) -> AppConfig:
    config = _read_config_from_env()
    if config.has_api_key:
        return config
    return _prompt_for_config(console, config)
