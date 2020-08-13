import logging
import os

from veldpy import Client, Embed, GatewayEvent, Message, ReadyPayload, User

logging.basicConfig(format="%(filename)s: %(message)s", level=logging.DEBUG)
log = logging.getLogger()

client = Client()


@client.event()
async def on_ready(payload: ReadyPayload) -> None:
    print(f"Logged in as {payload.user.name}")
    await client.set_nick("NotSoWorking")
    await client.http.send_message(
        embed=Embed(
            title="lol",
            description="kek",
            image_url="https://avatars0.githubusercontent.com/u/38864617?s=460&u=29795ceb82cc3604529faa42f68928b69d0890b5&v=4",
        )
    )


@client.event()
async def on_usr_msg(message: Message) -> None:
    if message.user.bot or not message.content:
        return
    if message.content == ".ping":
        await client.http.send_message("poggers")
    elif message.content.startswith("."):
        await client.http.send_message("idk that command bro")


@client.event(GatewayEvent.SYS_JOIN)
async def user_joined(user: User):
    if user.id == client.user.id:
        return
    await client.http.send_message(f"{user.name} has joined the kool kidz klub!")


client.run(token=os.environ["TOKEN"])
