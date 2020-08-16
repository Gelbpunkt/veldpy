from veldpy import models


def test_user() -> None:
    assert models.User.from_dict(
        {
            "id": 29519,
            "avatarUrl": "https://lol.me/x.png",
            "name": "kek",
            "bot": True,
            "status": {"value": "dnd"},
        }
    ) == models.User(
        id=29519,
        avatar_url="https://lol.me/x.png",
        name="kek",
        bot=True,
        status=models.UserStatus(value=models.Status.DND),
    )


def test_optional_fields() -> None:
    assert models.Embed.from_dict(
        {
            "author": {"value": "hola", "iconUrl": "https://lol.png"},
            "description": "zomg",
        }
    ) == models.Embed(
        author=models.EmbedAuthor(value="hola", icon_url="https://lol.png"),
        title=None,
        description="zomg",
        color=None,
        footer=None,
        image_url=None,
        thumbnail_url=None,
    )
