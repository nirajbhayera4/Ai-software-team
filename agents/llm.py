import os
import time

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from db import save_llm_call


load_dotenv()


def create_chat_model(temperature=0.2):
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    model = os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", model),
            temperature=temperature,
        )

    api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("LLM_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    api_version = os.getenv("LLM_API_VERSION") or os.getenv("OPENAI_API_VERSION")

    if not api_key:
        raise ValueError(
            "Missing API key. Set LLM_API_KEY or OPENAI_API_KEY in your .env file."
        )

    google_providers = {"gemini", "genai", "google"}
    supported_providers = {"openai", "openai-compatible", *google_providers}

    if provider in {"openai-compatible", *google_providers} and not base_url:
        raise ValueError(
            "Missing base URL. Set LLM_BASE_URL for OpenAI-compatible or Gemini/GenAI providers."
        )

    if provider not in supported_providers:
        raise ValueError(
            "Unsupported LLM_PROVIDER. Use openai, openai-compatible, gemini, genai, google, or ollama."
        )

    if api_version:
        os.environ["OPENAI_API_VERSION"] = api_version

    llm_kwargs = {
        "model": model,
        "temperature": temperature,
        "api_key": api_key,
    }

    if base_url:
        llm_kwargs["base_url"] = base_url

    return ChatOpenAI(**llm_kwargs)


def _message_text(messages):
    return "\n".join(getattr(message, "content", str(message)) for message in messages)


def _usage_from_response(response):
    usage = getattr(response, "usage_metadata", None) or {}
    response_metadata = getattr(response, "response_metadata", None) or {}
    token_usage = response_metadata.get("token_usage") or {}

    input_tokens = (
        usage.get("input_tokens")
        or token_usage.get("prompt_tokens")
        or token_usage.get("input_tokens")
        or 0
    )
    output_tokens = (
        usage.get("output_tokens")
        or token_usage.get("completion_tokens")
        or token_usage.get("output_tokens")
        or 0
    )
    return int(input_tokens or 0), int(output_tokens or 0)


def _cost_usd(input_tokens, output_tokens):
    try:
        input_cost = float(os.getenv("LLM_INPUT_COST_PER_1M_TOKENS", "0") or 0)
        output_cost = float(os.getenv("LLM_OUTPUT_COST_PER_1M_TOKENS", "0") or 0)
    except ValueError:
        input_cost = 0.0
        output_cost = 0.0
    return ((input_tokens * input_cost) + (output_tokens * output_cost)) / 1_000_000


def current_model_name():
    provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
    if provider == "ollama":
        return os.getenv("OLLAMA_MODEL") or os.getenv("LLM_MODEL") or "ollama"
    return os.getenv("LLM_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def invoke_agent_llm(agent_name, messages, temperature=0.2, task_id=None, agent_run_id=None):
    model_name = current_model_name()
    started = time.perf_counter()
    input_tokens = 0
    output_tokens = 0
    try:
        llm = create_chat_model(temperature=temperature)
        response = llm.invoke(messages)
        latency_ms = int((time.perf_counter() - started) * 1000)
        input_tokens, output_tokens = _usage_from_response(response)
        save_llm_call(
            agent_name=agent_name,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=_cost_usd(input_tokens, output_tokens),
            status="completed",
            task_id=task_id,
            agent_run_id=agent_run_id,
        )
        return response
    except Exception as error:
        latency_ms = int((time.perf_counter() - started) * 1000)
        if not input_tokens:
            input_tokens = max(0, len(_message_text(messages)) // 4)
        save_llm_call(
            agent_name=agent_name,
            model=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            cost_usd=_cost_usd(input_tokens, output_tokens),
            status="failed",
            error=str(error),
            task_id=task_id,
            agent_run_id=agent_run_id,
        )
        raise
