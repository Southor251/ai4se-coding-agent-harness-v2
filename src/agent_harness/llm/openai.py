import os
from openai import OpenAI
from agent_harness.llm.action_protocol import action_protocol_prompt, parse_agent_action
from agent_harness.llm.interface import LLMInterface, LLMResponse
from agent_harness.models import AgentAction


class OpenAILLM(LLMInterface):
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4",
        base_url: str | None = None,
        temperature: float = 0.7,
        client=None,
    ):
        self.api_key = os.environ.get("OPENAI_API_KEY", "") if api_key is None else api_key
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self._client = client

    def _get_client(self) -> OpenAI:
        if self._client is None:
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        return self._client

    def call(self, context: list[dict], menu: list[dict]) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(text="API key not configured", action=AgentAction(type="done"))
        messages = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in context]
        if menu:
            tool_desc = "\n".join(_format_tool_for_message(tool) for tool in menu)
            messages.append({"role": "system", "content": f"Available tools:\n{tool_desc}"})
        messages.append({"role": "system", "content": action_protocol_prompt(menu)})
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
            )
            text = response.choices[0].message.content or ""
            action = parse_agent_action(text)
            return LLMResponse(text=text, action=action)
        except Exception:
            return LLMResponse(
                text="API request failed; inspect provider configuration and logs securely",
                action=AgentAction(type="done"),
            )


def _format_tool_for_message(tool: dict) -> str:
    args_schema = tool.get("args_schema") or {}
    if not args_schema:
        return f"- {tool.get('name', '?')}: {tool.get('description', '')}"
    args = ", ".join(f"{key}: {value}" for key, value in args_schema.items())
    return f"- {tool.get('name', '?')}: {tool.get('description', '')}; args: {args}"
