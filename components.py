from discord.ui import Select
from discord.components import SelectOption


def create_music_select(list_of_items: list[str]) -> Select:
    return Select(
        placeholder="Select music",
        max_values=5,
        options=[
            SelectOption(label="siema", value="test"),
            SelectOption(label="siema", value="test"),
            SelectOption(label="siema", value="test"),
        ],
    )
