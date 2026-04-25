from __future__ import annotations

from typing import Any

import requests

from config import AppConfig


class LLMClientError(Exception):
    """Raised when the model API cannot return usable text."""


class LLMClient:
    def __init__(self, config: AppConfig, timeout: int = 60) -> None:
        self.config = config
        self.timeout = timeout

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
        if not self.config.api_key:
            raise LLMClientError("API Key 未配置。请设置环境变量、.env，或重启后重新输入。")

        url = f"{self.config.api_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.Timeout as exc:
            raise LLMClientError("请求超时，请检查网络或 API 服务状态。") from exc
        except requests.RequestException as exc:
            raise LLMClientError(f"网络请求失败：{exc}") from exc

        if response.status_code in {401, 403}:
            raise LLMClientError("鉴权失败，请检查 API Key 是否正确。")
        if response.status_code == 404:
            raise LLMClientError("接口地址不存在，请检查 API_BASE_URL 是否为 OpenAI-compatible /v1 地址。")
        if response.status_code >= 400:
            detail = _extract_error(response)
            raise LLMClientError(f"模型接口返回错误 HTTP {response.status_code}：{detail}")

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("模型返回格式异常，无法读取回复文本。") from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMClientError("模型返回了空内容。")
        return content.strip()


def _extract_error(response: requests.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text[:300] or "无错误详情"

    error = data.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("type") or error.get("code")
        if message:
            return str(message)
    return str(data)[:300]
