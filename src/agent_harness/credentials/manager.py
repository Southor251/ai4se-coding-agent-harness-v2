import os
from pathlib import Path
from typing import Any


class CredentialManager:
    def __init__(
        self,
        service: str = "agent-harness",
        username: str = "openai-api-key",
        backend: Any = None,
        env_file: str | Path = ".env",
    ):
        self.service = service
        self.username = username
        self.backend = backend or self._default_backend()
        self.env_file = Path(env_file)

    def get(self) -> str | None:
        runtime_value = os.environ.get("OPENAI_API_KEY")
        if runtime_value:
            return runtime_value
        try:
            value = self.backend.get_password(self.service, self.username)
            if value:
                return value
        except Exception:
            pass
        return self._read_env_value()

    def update(self, secret: str):
        try:
            self.backend.set_password(self.service, self.username, secret)
            return
        except Exception:
            self._write_env_value(secret)

    def clear(self):
        try:
            self.backend.delete_password(self.service, self.username)
        except Exception:
            pass
        self._remove_env_value()

    def show_status(self) -> str:
        return "configured" if self.get() else "not configured"

    def _read_env_value(self) -> str | None:
        if not self.env_file.exists():
            return None
        for line in self.env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip()
        return None

    def _write_env_value(self, secret: str):
        self.env_file.write_text(f"OPENAI_API_KEY={secret}\n", encoding="utf-8")

    def _remove_env_value(self):
        if self.env_file.exists():
            remaining = [
                line
                for line in self.env_file.read_text(encoding="utf-8").splitlines()
                if not line.startswith("OPENAI_API_KEY=")
            ]
            self.env_file.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")

    def _default_backend(self):
        import keyring

        return keyring

