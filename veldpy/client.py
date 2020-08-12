"""
Copyright (c) 2020, Jens Reidel
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import asyncio
import logging

from collections import defaultdict
from functools import partial
from typing import Any, Callable, Dict, List, Optional

import socketio

from .events import GatewayEvent
from .models import Message, User

# This is an implementation of a simple Client for the socket.io server
# It does only faciliate connecting, models and events
# For a command framework, try the exts

log = logging.getLogger(__name__)


class Client:
    def __init__(self) -> None:
        self.sio = socketio.AsyncClient()
        self._listeners: Dict[GatewayEvent, List[Callable]] = defaultdict(lambda: [])
        self.register_handlers()
        self._parsers = {
            GatewayEvent.USR_MSG: Message.from_dict,
            GatewayEvent.SYS_JOIN: User.from_dict,
            GatewayEvent.SYS_LEAVE: User.from_dict,
            GatewayEvent.USR_TYP: User.from_dict,
            GatewayEvent.READY: self._process_ready,
        }
        self.users: List[User] = []
        self.user: Optional[User] = None

    def _process_ready(self, data: Dict[str, Any]):
        for user in data["members"]:
            self.users.append(User.from_dict(user))
        self.user = User.from_dict(data["user"])

    def register_handlers(self) -> None:
        """
        Method used to provide handlers for each
        Veldchat event.

        It creates a wrapper function for each event that
        looks for a handler registered on this client.
        """

        # This sadly has to be a coro instead of returning callback
        # https://github.com/miguelgrinberg/python-socketio/blob/master/socketio/asyncio_client.py#L388
        async def forward(event: GatewayEvent, data: Dict[str, Any]) -> None:
            log.debug(f"Received event: {event}")
            if parser := self._parsers.get(event, None):
                parsed = parser(data)
            else:
                parsed = data
            callbacks = self._listeners[event]
            for callback in callbacks:
                await callback(parsed)

        for event in GatewayEvent:
            self.sio.on(event.name, partial(forward, event))

    def event(self) -> Callable[[Callable], Callable]:
        """
        Registers a new event handler.
        """

        def inner(func):
            # Remove on_
            try:
                name = func.__name__[3:].upper()
            except IndexError:
                return
            event = getattr(GatewayEvent, name, None)
            if event is None:
                return

            self._listeners[event].append(func)

            return func

        return inner

    async def send_message(self, text: str) -> None:
        await self.sio.emit("usr-msg", {"message": text})

    async def set_nick(self, name: str) -> None:
        """
        Sets the nickname for the bot.
        """
        await self.send_message(f"/nick {name}")

    async def login(self, token: Optional[str] = None, bot: bool = True) -> None:
        log.debug("Logging in")
        await self.sio.emit("login", {"token": token, "bot": bot})

    async def start(self, *args, **kwargs) -> None:
        self._listeners[GatewayEvent.CONNECT].append(
            partial(self.login, *args, **kwargs)
        )
        log.debug(f"About to connect, listeners are: {self._listeners}")
        try:
            await self.sio.connect("https://chat-gateway.veld.dev")
            await self.sio.wait()
        except Exception:
            import traceback

            traceback.print_exc()
        finally:
            await self.sio.disconnect()

    def run(self, *args, **kwargs) -> None:
        log.debug("Starting asyncio event loop")
        asyncio.run(self.start(*args, **kwargs))
