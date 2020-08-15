import logging
import os

from veldpy import (
    Channel,
    Client,
    Embed,
    GatewayEvent,
    MemberEvent,
    Message,
    ReadyPayload,
)

logging.basicConfig(format="%(filename)s: %(message)s", level=logging.DEBUG)
log = logging.getLogger()

client = Client()


@client.event()
async def on_ready(payload: ReadyPayload) -> None:
    print(f"Logged in as {payload.user.name}")
    # await client.set_nick("NotSoWorking")


@client.event()
async def on_channel_join(channel: Channel):
    await client.http.send_message(
        channel.id,
        embed=Embed(
            title="lol",
            description="kek",
            image_url="https://avatars0.githubusercontent.com/u/38864617?s=460&u=29795ceb82cc3604529faa42f68928b69d0890b5&v=4",
        ),
    )


@client.event()
async def on_message_create(message: Message) -> None:
    if message.user.bot or not message.content:
        return
    if message.content == ".ping":
        await client.http.send_message(message.channel.id, "poggers")
    elif message.content.startswith("."):
        await client.http.send_message(message.channel.id, "idk that command bro")


@client.event(GatewayEvent.MEMBER_CREATE)
async def user_joined(member: MemberEvent):
    if member.user.id == client.user.id:
        return
    await client.http.send_message(
        member.channel.id, f"{member.user.name} has joined the kool kidz klub!"
    )


client.run(token=os.environ["TOKEN"])
