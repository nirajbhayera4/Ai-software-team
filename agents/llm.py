import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


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
