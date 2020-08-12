# This example is a proof-of-concept regarding socketio and not part of
# any library-specific examples
import asyncio
from functools import partial
from typing import Any, Dict, TypeVar

import socketio

AnyJson = TypeVar("AnyJson")

# https://github.com/velddev/node-chat-server/wiki/Websocket-API
ALL_EVENTS = (
    "connect",
    "usr-msg",
    "sys-join",
    "sys-leave",
    "sys-error",
    "usr-typ",
    "ready",
    "sys-commands",
)


class VeldClient:
    def __init__(self) -> None:
        self.sio = socketio.AsyncClient()
        self.register_handlers()

    def register_handlers(self) -> None:
        """
        Method used to provide handlers for each
        Veldchat event.
        """

        # This sadly has to be a coro instead of returning callback
        # https://github.com/miguelgrinberg/python-socketio/blob/master/socketio/asyncio_client.py#L388
        async def forward(event_name: str, *args, **kwargs) -> None:
            event_name = event_name.replace("-", "_")
            callback = getattr(self, f"on_{event_name}", None)
            if callback is not None:
                await callback(*args, **kwargs)

        for event in ALL_EVENTS:
            self.sio.on(event, partial(forward, event))

    async def on_connect(self) -> None:
        await self.sio.emit("login", {"token": None, "bot": True})

    async def on_ready(self, info: AnyJson) -> None:
        print("We ready bois")
        await self.send_message("/nick AdriBotNoU")

    async def on_sys_join(self, user: AnyJson) -> None:
        await self.send_message(f"Welcome {user['name']}!")

    async def on_sys_leave(self, user: AnyJson) -> None:
        await self.send_message(f"Byee {user['name']}!")

    async def on_usr_msg(self, message: AnyJson) -> None:
        content = message.get("message", None)
        if content is None or message["user"]["bot"]:
            return

        if content == ".ping":
            await self.send_message("pong")
        elif content.startswith("."):
            await self.send_message("idk that command sry bro")

    async def send_message(self, text: str) -> None:
        await self.sio.emit("usr-msg", {"message": text})

    async def login(self) -> None:
        try:
            await self.sio.connect("https://chat-gateway.veld.dev")
            await self.sio.wait()
        except:
            import traceback

            traceback.print_exc()
        finally:
            await self.sio.disconnect()


asyncio.run(VeldClient().login())
