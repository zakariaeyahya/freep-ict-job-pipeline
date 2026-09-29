"""OllamaClient: talks to a local Ollama server via /api/chat with JSON
mode. Mocks requests.post so this test never depends on Ollama actually
running — a separate manual/integration check (see README.md) covers the
real container.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
import requests

from src.freep_pipeline.extraction.ollama_client import OllamaClient, OllamaUnavailableError


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


def test_generate_json_returns_the_parsed_model_response() -> None:
    ollama_payload = {"message": {"content": json.dumps({"skills": ["Python"]})}}

    with patch("src.freep_pipeline.extraction.ollama_client.requests.post", return_value=_FakeResponse(ollama_payload)):
        result = OllamaClient(base_url="http://localhost:11434", model="qwen2.5:7b-instruct").generate_json(
            "system", "user text"
        )

    assert result == {"skills": ["Python"]}


def test_generate_json_sends_deterministic_options_and_json_format() -> None:
    ollama_payload = {"message": {"content": "{}"}}
    captured = {}

    def _capture_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse(ollama_payload)

    with patch("src.freep_pipeline.extraction.ollama_client.requests.post", side_effect=_capture_post):
        OllamaClient(base_url="http://localhost:11434", model="qwen2.5:7b-instruct").generate_json("sys", "usr")

    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["json"]["format"] == "json"
    assert captured["json"]["options"]["temperature"] == 0
    assert captured["json"]["model"] == "qwen2.5:7b-instruct"


def test_connection_failure_raises_ollama_unavailable_error() -> None:
    with patch(
        "src.freep_pipeline.extraction.ollama_client.requests.post",
        side_effect=requests.ConnectionError("refused"),
    ):
        with pytest.raises(OllamaUnavailableError):
            OllamaClient().generate_json("system", "user text")


def test_http_error_status_raises_ollama_unavailable_error() -> None:
    with patch(
        "src.freep_pipeline.extraction.ollama_client.requests.post",
        return_value=_FakeResponse({}, status_code=500),
    ):
        with pytest.raises(OllamaUnavailableError):
            OllamaClient().generate_json("system", "user text")


def test_non_json_model_content_raises_ollama_unavailable_error() -> None:
    ollama_payload = {"message": {"content": "not valid json at all"}}

    with patch("src.freep_pipeline.extraction.ollama_client.requests.post", return_value=_FakeResponse(ollama_payload)):
        with pytest.raises(OllamaUnavailableError):
            OllamaClient().generate_json("system", "user text")
