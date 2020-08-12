import logging

from veldpy import Client, GatewayEvent, Message, ReadyPayload, User

logging.basicConfig(format="%(filename)s: %(message)s", level=logging.WARNING)
log = logging.getLogger()

client = Client()


@client.event()
async def on_ready(payload: ReadyPayload) -> None:
    print(f"Logged in as {payload.user.name}")
    await client.set_nick("NotSoWorking")


@client.event()
async def on_usr_msg(message: Message) -> None:
    if message.user.bot or not message.content:
        return
    if message.content == ".ping":
        await client.send_message("poggers")
    elif message.content.startswith("."):
        await client.send_message("idk that command bro")


@client.event(GatewayEvent.SYS_JOIN)
async def user_joined(user: User):
    if user.id == client.user.id:
        return
    await client.send_message(f"{user.name} has joined the kool kidz klub!")


client.run()
