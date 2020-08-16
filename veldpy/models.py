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
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# This is an implementation of the veldchat gateway models as described here:
# https://github.com/velddev/node-chat-server/wiki/Model


class Status(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DND = "dnd"
    AWAY = "away"


@dataclass
class Embed:
    author: Optional[EmbedAuthor] = None
    title: Optional[str] = None
    description: Optional[str] = None
    color: Optional[int] = None
    footer: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Embed:
        if (author := data.get("author", None)) is not None:
            author = EmbedAuthor.from_dict(author)
        title = data.get("title", None)
        description = data.get("description", None)
        color = data.get("color", None)
        footer = data.get("footer", None)
        image_url = data.get("imageUrl", None)
        thumbnail_url = data.get("thumbnailUrl", None)
        return cls(
            author=author,
            title=title,
            description=description,
            color=color,
            footer=footer,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
        )

    def to_dict(self) -> Dict[str, Any]:
        if self.author is not None:
            author: Optional[Dict[str, Any]] = self.author.to_dict()
        else:
            author = None
        return {
            "author": author,
            "title": self.title,
            "description": self.description,
            "color": self.color,
            "footer": self.footer,
            "imageUrl": self.image_url,
            "thumbnailUrl": self.thumbnail_url,
        }


@dataclass
class EmbedAuthor:
    value: str
    icon_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EmbedAuthor:
        value = data["value"]
        icon_url = data.get("iconUrl", None)
        return cls(value=value, icon_url=icon_url)

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "iconUrl": self.icon_url}


@dataclass
class Message:
    id: int
    user: User
    channel: Channel
    mentions: List[User]
    content: Optional[str] = None
    embed: Optional[Embed] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Message:
        id = int(data["id"])
        user = data["user"]
        channel = data["channel"]
        mentions = data["mentions"]
        content = data.get("content", None)
        if embed := data.get("embed", None):
            embed = Embed.from_dict(embed)
        return cls(
            id=id,
            user=user,
            channel=channel,
            mentions=mentions,
            content=content,
            embed=embed,
        )


@dataclass
class User:
    # compare needs to be False for id to be used for comparison
    id: int
    name: str = field(compare=False)
    bot: bool = field(compare=False)
    status: UserStatus = field(compare=False)
    avatar_url: Optional[str] = field(default=None, compare=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> User:
        id = int(data["id"])
        name = data["name"]
        bot = data["bot"]
        status = UserStatus.from_dict(data["status"])
        avatar_url = data.get("avatarUrl", None)
        return cls(id=id, name=name, bot=bot, status=status, avatar_url=avatar_url)


@dataclass
class ReadyPayload:
    user: User
    members: List[User]
    token: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReadyPayload:
        user = User.from_dict(data["user"])
        members = [User.from_dict(d) for d in data["members"]]
        token = data["token"]
        return cls(user=user, members=members, token=token)


@dataclass
class TokenResponse:
    id: int
    token: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenResponse:
        id = int(data["id"])
        token = data["token"]
        return cls(id=id, token=token)


@dataclass
class Emoji:
    name: str
    value: str
    image: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Emoji:
        name = data["name"]
        value = data["value"]
        image = data["image"]
        return cls(name=name, value=value, image=image)


@dataclass
class UserStatus:
    value: Status
    status_text: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserStatus:
        value = Status[data["value"].upper()]
        status_text = data.get("statusText", None)
        return cls(value=value, status_text=status_text)


@dataclass
class Channel:
    id: int
    name: str = field(compare=False)
    members: List[User] = field(default_factory=lambda: [], compare=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Channel:
        id = int(data["id"])
        name = data["name"]
        members = [User.from_dict(d) for d in data.get("members", [])]
        return cls(id=id, name=name, members=members)


@dataclass
class MemberEvent:
    channel: Channel
    user: User

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MemberEvent:
        channel = Channel.from_dict(data["channel"])
        user = User.from_dict(data["user"])
        return cls(channel=channel, user=user)
