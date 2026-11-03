import os
from dotenv import load_dotenv
from groq import Groq
from langchain_groq import ChatGroq
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

load_dotenv()

MODEL = "openai/gpt-oss-120b"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_TOKENS = 2048


def _get_api_key() -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except StreamlitSecretNotFoundError:
            api_key = None

    if not api_key:
        raise RuntimeError(
            "Clé API Groq introuvable. Définissez GROQ_API_KEY dans .env "
            "ou dans les secrets de Streamlit."
        )
    return api_key


_client = Groq(api_key=_get_api_key())


def get_langchain_llm():
    return ChatGroq(
        model=MODEL,
        api_key=_get_api_key(),
        temperature=DEFAULT_TEMPERATURE,
    )

def chat(messages: list[dict], tools: list[dict] | None = None,
         temperature: float = DEFAULT_TEMPERATURE,
         max_tokens: int = DEFAULT_MAX_TOKENS):
    
    kwargs = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    response = _client.chat.completions.create(**kwargs)
    return response.choices[0].message