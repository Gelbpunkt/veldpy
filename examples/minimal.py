import logging

from veldpy import Client

client = Client()


@client.event()
async def on_ready(data):
    print("poggers")


@client.event()
async def on_usr_msg(message):
    print(message)


log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.debug("starting this")
client.run()
