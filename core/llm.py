"""
LLM Integration — Dual-mode LLM factory supporting local Ollama and OpenAI API.
All LLM interactions go through this module to ensure consistent
system prompts, citation enforcement, and contradiction flagging.
"""

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models import BaseChatModel

import config


# System instruction enforced on ALL LLM calls
SYSTEM_INSTRUCTION = """You are StudyLens, an AI study assistant. Follow these rules strictly:

1. ONLY use information from the provided context. Never add external knowledge.
2. ALWAYS cite the source document name, page number, or slide number when referencing information.
3. If sources CONTRADICT each other, explicitly flag the contradiction and present both viewpoints with their sources.
4. If the context does not contain enough information to answer, say exactly:
   "I couldn't find relevant information in your uploaded documents for this question."
5. Never make up, hallucinate, or infer information not present in the context.
"""


def get_llm(mode: str = "local", api_key: str | None = None) -> BaseChatModel:
    """
    Create an LLM instance based on the selected mode.

    Args:
        mode: Either "local" (Ollama + Llama 3) or "api" (OpenAI GPT-4o-mini).
        api_key: OpenAI API key (required when mode is "api").

    Returns:
        A LangChain chat model ready for use.

    Raises:
        ValueError: If mode is "api" but no API key is provided.
    """
    if mode == "api":
        key = api_key or config.OPENAI_API_KEY
        if not key or key == "your_key_here":
            raise ValueError(
                "OpenAI API key is required for API mode. "
                "Please enter your API key in the sidebar."
            )
        return ChatOpenAI(
            model=config.OPENAI_MODEL,
            api_key=key,
            temperature=0.3,
            max_tokens=4096,
        )
    else:
        # Local mode using Ollama
        return ChatOllama(
            model=config.OLLAMA_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=0.3,
            num_predict=4096,
        )


def invoke_llm(
    llm: BaseChatModel,
    user_prompt: str,
    system_prompt: str | None = None,
) -> str:
    """
    Invoke the LLM with a system + user prompt pair.

    Args:
        llm: The LLM instance from get_llm().
        user_prompt: The formatted user prompt with context injected.
        system_prompt: Optional override for the system instruction.
                       Defaults to the StudyLens citation-enforcing prompt.

    Returns:
        The LLM's response as a string.
    """
    from langchain_core.messages import SystemMessage, HumanMessage

    sys_msg = system_prompt or SYSTEM_INSTRUCTION
    messages = [
        SystemMessage(content=sys_msg),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    return response.content
