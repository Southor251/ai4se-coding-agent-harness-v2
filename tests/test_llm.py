import pytest
from agent_harness.llm.interface import LLMInterface, LLMResponse
from agent_harness.llm.mock import MockLLM
from agent_harness.models import AgentAction


from agent_harness.llm.openai import OpenAILLM


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        LLMInterface()


def test_mock_llm_returns_preset():
    expected = LLMResponse(text="hello", action=AgentAction(type="done"))
    mock = MockLLM(responses=[expected])
    result = mock.call([], [])
    assert result.text == "hello"
    assert result.action.type == "done"


def test_mock_llm_consumes_queue():
    r1 = LLMResponse(text="first", action=AgentAction(type="call_tool", tool="read_file"))
    r2 = LLMResponse(text="second", action=AgentAction(type="done"))
    mock = MockLLM(responses=[r1, r2])
    assert mock.call([], []).text == "first"
    assert mock.call([], []).text == "second"


def test_mock_llm_call_tool_when_exhausted():
    mock = MockLLM(responses=[])
    result = mock.call([], [])
    assert result.action.type == "call_tool"


def test_openai_llm_no_key():
    llm = OpenAILLM(api_key="")
    result = llm.call([], [])
    assert result.action.type == "done"
    assert "not configured" in result.text


def test_openai_llm_explicit_empty_key_does_not_fall_back_to_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")

    llm = OpenAILLM(api_key="")

    assert llm.api_key == ""


def test_openai_llm_does_not_expose_provider_exception_details():
    class FailingClient:
        class Chat:
            class Completions:
                def create(self, **kwargs):
                    raise RuntimeError("provider rejected secret-token")

            completions = Completions()

        chat = Chat()

    llm = OpenAILLM(api_key="test-key", client=FailingClient())

    result = llm.call([], [])

    assert result.action.type == "done"
    assert result.text == "API request failed; inspect provider configuration and logs securely"
    assert "secret-token" not in result.text


class FakeOpenAIMessage:
    content = '{"type": "call_tool", "tool": "read_file", "args": {"path": "README.md"}}'


class FakeOpenAIChoice:
    message = FakeOpenAIMessage()


class FakeOpenAIResponse:
    def __init__(self, text=None):
        if text is not None:
            self.choices = [type("Choice", (), {"message": type("Message", (), {"content": text})()})()]
        else:
            self.choices = [FakeOpenAIChoice()]


class FakeCompletions:
    def __init__(self):
        self.last_kwargs = None
        self.response_text = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return FakeOpenAIResponse(self.response_text)


class FakeChat:
    def __init__(self):
        self.completions = FakeCompletions()


class FakeClient:
    def __init__(self):
        self.chat = FakeChat()


def test_openai_llm_parses_structured_tool_action():
    llm = OpenAILLM(api_key="test-key")
    client = FakeClient()
    llm._client = client

    result = llm.call([], [{"name": "read_file", "description": "read"}])

    assert result.action.type == "call_tool"
    assert result.action.tool == "read_file"
    assert result.action.args == {"path": "README.md"}


def test_openai_llm_invalid_action_is_observable():
    llm = OpenAILLM(api_key="test-key")
    client = FakeClient()
    client.chat.completions.response_text = "not json"
    llm._client = client

    result = llm.call([], [])

    assert result.action.type == "invalid"
    assert "valid JSON" in result.action.args["error"]


def test_openai_llm_passes_model_and_temperature_to_client():
    llm = OpenAILLM(api_key="test-key", model="custom-model", temperature=0.2)
    client = FakeClient()
    llm._client = client

    llm.call([{"role": "user", "content": "hello"}], [])

    assert client.chat.completions.last_kwargs["model"] == "custom-model"
    assert client.chat.completions.last_kwargs["temperature"] == 0.2
    messages = client.chat.completions.last_kwargs["messages"]
    assert messages[0] == {"role": "user", "content": "hello"}
    assert "Respond with exactly one JSON object" in messages[-1]["content"]


def test_openai_llm_includes_tool_arg_schema_in_prompt():
    llm = OpenAILLM(api_key="test-key")
    client = FakeClient()
    llm._client = client

    llm.call(
        [],
        [
            {
                "name": "write_file",
                "description": "Write content to file",
                "args_schema": {"path": "File path to write", "content": "UTF-8 text content"},
            }
        ],
    )

    messages = client.chat.completions.last_kwargs["messages"]
    prompt_text = "\n".join(message["content"] for message in messages)
    assert "write_file" in prompt_text
    assert "path" in prompt_text
    assert "content" in prompt_text


def test_openai_llm_builds_client_with_base_url():
    llm = OpenAILLM(api_key="test-key", model="custom-model", base_url="https://example.test/v1")

    assert llm.base_url == "https://example.test/v1"
