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
import inspect
import logging

from collections import defaultdict
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Union

import socketio

from .events import GatewayEvent
from .models import Message, ReadyPayload, User

# This is an implementation of a simple Client for the socket.io server
# It does only faciliate connecting, models and events
# For a command framework, try the exts

log = logging.getLogger(__name__)


class Client:
    def __init__(self) -> None:
        self.sio = socketio.AsyncClient()
        self._listeners: Dict[GatewayEvent, List[Callable[..., Any]]] = defaultdict(
            lambda: []
        )
        self.register_handlers()
        self._parsers = {
            GatewayEvent.USR_MSG: Message.from_dict,
            GatewayEvent.SYS_JOIN: User.from_dict,
            GatewayEvent.SYS_LEAVE: User.from_dict,
            GatewayEvent.USR_TYP: User.from_dict,
            GatewayEvent.READY: ReadyPayload.from_dict,
        }
        self.users: List[User] = []
        self.user: Optional[User] = None

    def add_listener(self, event: GatewayEvent, callback: Callable[..., Any]) -> None:
        self._listeners[event].append(callback)

    def register_handlers(self) -> None:
        """
        Method used to provide handlers for each
        Veldchat event.

        It creates a wrapper function for each event that
        looks for a handler registered on this client.
        """

        # This sadly has to be a coro instead of returning callback
        # https://github.com/miguelgrinberg/python-socketio/blob/master/socketio/asyncio_client.py#L388
        async def forward(
            event: GatewayEvent, data: Optional[Dict[str, Any]] = None
        ) -> None:
            log.debug(f"Received event: {event}")
            callbacks = self._listeners[event]
            if not callbacks:
                return

            if data is not None:
                if parser := self._parsers.get(event, None):
                    parsed = parser(data)
                else:
                    parsed = data
                for callback in callbacks:
                    maybe_coro = callback(parsed)
                    if inspect.iscoroutine(maybe_coro):
                        await maybe_coro
            else:
                for callback in callbacks:
                    maybe_coro = callback()
                    if inspect.iscoroutine(maybe_coro):
                        await maybe_coro

        for event in GatewayEvent:
            # Check if there is a default method on the client
            if callback := getattr(self, f"on_{event.value.replace('-', '_')}", None):
                self.add_listener(event, callback)
            self.sio.on(event.value, partial(forward, event))

    def event(
        self, event_type: Optional[GatewayEvent] = None
    ) -> Callable[[Callable[[Any], Any]], Callable[[Any], Any]]:
        """
        Registers a new event handler.
        """

        # Hack to keep event_type in scope :^)
        def inner(
            func: Callable[[Any], Any], event_type: Optional[GatewayEvent] = event_type
        ) -> Callable[[Any], Any]:
            # If no event is provided, use the function name
            if event_type is None:
                # Remove on_
                try:
                    name = func.__name__[3:].upper()
                except IndexError:
                    return func
                event_type = getattr(GatewayEvent, name, None)
                if event_type is None:
                    return func

            self.add_listener(event_type, func)

            return func

        return inner

    async def send_message(self, text: str) -> None:
        await self.sio.emit("usr-msg", {"content": text})

    async def set_nick(self, name: str) -> None:
        """
        Sets the nickname for the bot.
        """
        await self.send_message(f"/nick {name}")

    async def login(self, token: Optional[str] = None, bot: bool = True) -> None:
        log.info(f"Logging in with token {token} and bot={bot}")
        await self.sio.emit("login", {"token": token, "bot": bot})

    async def start(
        self, *args: Optional[Union[str, bool]], **kwargs: Optional[Union[str, bool]]
    ) -> None:
        self.add_listener(GatewayEvent.CONNECT, partial(self.login, *args, **kwargs))
        log.debug(f"About to connect, listeners are: {self._listeners}")
        await self.sio.connect("https://chat-gateway.veld.dev")
        await self.sio.wait()

    def run(
        self, *args: Optional[Union[str, bool]], **kwargs: Optional[Union[str, bool]]
    ) -> None:
        log.info("Starting asyncio event loop")
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start(*args, **kwargs))
        except KeyboardInterrupt:
            pass
        except Exception:
            import traceback

            traceback.print_exc()
        finally:
            loop.run_until_complete(self.sio.disconnect())

    def on_ready(self, payload: ReadyPayload) -> None:
        self.users = payload.members
        self.user = payload.user

    def on_sys_join(self, user: User) -> None:
        self.users.append(user)

    def on_sys_leave(self, user: User) -> None:
        self.users.remove(user)
