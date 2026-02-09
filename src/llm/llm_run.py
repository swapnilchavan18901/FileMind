# llm/chat.py
from src.llm.client import get_llm
from src.llm.prompt_builder import build_chat_prompt


async def run_chat(
    *,
    question: str,
    context: str,
    bot_system_prompt: str,
) -> str:
    llm = get_llm()
    prompt = build_chat_prompt(
        bot_system_prompt=bot_system_prompt,
        context=context,
        question=question,
    )

    chain = prompt | llm
    response = await chain.ainvoke({})

    return response.content
