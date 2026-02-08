from src.sockets.ws_chats import sio
from src.db import prisma
from src.utils.api_key import hash_api_key

@sio.event
async def connect(sid, environ, auth):
    print(f"connectishere:")
    print(f"authishere: {auth}")
    api_key = auth.get("apiKey")
    bot_id = auth.get("botId")
    if not api_key or not bot_id:
        print(f"api_key or bot_id is not found")
        return False  # reject connection

    hashed = hash_api_key(api_key)

    api_key_obj = await prisma.apikey.find_unique(
        where={"keyHash": hashed}
    )

    if not api_key_obj or not api_key_obj.isActive:
        return False

    if api_key_obj.botId != bot_id:
        return False

    bot = await prisma.bot.find_unique(where={"id": bot_id})
    if not bot or not bot.isActive:
        return False

    # store context on socket
    sio.save_session(sid, {
        "botId": bot.id,
        "apiKeyId": api_key_obj.id,
    })

    print(f"Socket connected: {sid}")


@sio.event
async def start_chat(sid, data):
    session = sio.get_session(sid)
    print(f"start_chatishere:")
    # 1️⃣ Create chat session
    chat_session = await prisma.chatsession.create(
        data={
            "botId": session["botId"],
            "apiKeyId": session["apiKeyId"],
        }
    )

    # 2️⃣ Fetch bot to get system prompt
    bot = await prisma.bot.find_unique(
        where={"id": session["botId"]}
    )

    # 3️⃣ Insert SYSTEM message FIRST (CRITICAL)
    if bot.systemPrompt:
        await prisma.chatmessage.create(
            data={
                "sessionId": chat_session.id,
                "role": "system",
                "content": bot.systemPrompt,
            }
        )

    # 4️⃣ Join room (session == room)
    room = f"chat:{chat_session.id}"
    await sio.enter_room(sid, room)

    # 5️⃣ Save session context
    sio.save_session(sid, {
        **session,
        "sessionId": chat_session.id,
        "room": room
    })

    # 6️⃣ Notify client
    await sio.emit(
        "chat_started",
        {"sessionId": chat_session.id},
        to=sid
    )


@sio.event
async def user_message(sid, data):
    session = sio.get_session(sid)
    room = session["room"]

    message = data.get("content")
    if not message:
        return

    # store user message
    await prisma.chatmessage.create(
        data={
            "sessionId": session["sessionId"],
            "role": "user",
            "content": message,
        }
    )

    # mock assistant reply
    reply = f"You said: {message}"

    await prisma.chatmessage.create(
        data={
            "sessionId": session["sessionId"],
            "role": "assistant",
            "content": reply,
        }
    )

    await sio.emit("assistant_message", {
        "content": reply
    }, to=room)
