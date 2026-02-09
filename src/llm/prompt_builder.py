# llm/prompts.py
from langchain_core.prompts import ChatPromptTemplate
from src.llm.prompt.system_prompt import SYSTEM_PROMPT


def build_chat_prompt(
    *,
    bot_system_prompt: str,
    context: str,
    question: str,
) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("system", bot_system_prompt),
        ("system", f"Context:\n{context}"),
        ("human", question),
    ])
