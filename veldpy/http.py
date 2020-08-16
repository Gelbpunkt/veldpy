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
import logging

from typing import Any, Dict, Optional

# https://chat-gateway.veld.dev/swagger/
import aiohttp

from .models import Channel, Embed, Message

log = logging.getLogger(__name__)


class HTTPException(Exception):
    """Generic exception when a HTTP operation failed."""

    pass


class HTTPClient:
    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()
        self.token: Optional[str] = None

    # /api/v1/channels
    async def create_channel(self, name: str) -> Channel:
        """
        Creates a new channel.
        """
        async with self.session.post(
            "https://chat-gateway.veld.dev/api/v1/channels",
            json={"name": name},
            headers={"Authorization": f"Bearer {self.token}"},
        ) as req:
            if req.status != 200:
                body = await req.text()
                log.debug(f"HTTP Response code {req.status}, body is {body}")
                raise HTTPException()
            json = await req.json()
        return Channel.from_dict(json)

    # /api/v1/channels/id/join
    async def join_channel(self, channel_id: int) -> bool:
        """
        Joins a channel
        """
        async with self.session.post(
            f"https://chat-gateway.veld.dev/api/v1/channels/{channel_id}/join",
            headers={"Authorization": f"Bearer {self.token}"},
        ) as req:
            if req.status != 204:
                body = await req.text()
                log.debug(f"HTTP Response code {req.status}, body is {body}")
                raise HTTPException()
        return True

    # /api/v1/channels/id/messages
    async def send_message(
        self,
        channel_id: int,
        content: Optional[str] = None,
        embed: Optional[Embed] = None,
    ) -> Message:
        """
        Sends a message to a channel
        """
        if content is None and embed is None:
            raise ValueError("Either content or embed must be supplied")

        data: Dict[str, Any] = {"content": content}
        if embed is not None:
            data["embed"] = embed.to_dict()
        async with self.session.post(
            f"https://chat-gateway.veld.dev/api/v1/channels/{channel_id}/messages",
            json=data,
            headers={"Authorization": f"Bearer {self.token}"},
        ) as req:
            if req.status != 204:
                body = await req.text()
                log.debug(f"HTTP Response code {req.status}, body is {body}")
                raise HTTPException()
        return Message.from_dict(data)
