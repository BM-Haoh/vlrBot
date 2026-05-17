from discord.ui import View
import discord

class Menu(discord.ui.Select):
    def __init__(self, embedList, pool):
        self.embedList = embedList
        self.display_message = None

        options = []
        for i, mapa in enumerate(pool):
            options.append(
                discord.SelectOption(
                    label=mapa,
                    value=i+1,
                    description=f"Informações sobre o mapa {mapa}",
                    emoji="🗺️"
                )
            )

        options.insert(0, discord.SelectOption(
            label="Overview",
            value=0,
            description="Informações gerais do time",
            emoji="📋"
            )
        )

        options.append(
            discord.SelectOption(
                label="Stats",
                value=len(pool)+1,
                description="Médias estatísticas do time historicamente",
                emoji="📊"
            )
        )

        super().__init__(placeholder="Página:", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        embedIndex = int(self.values[0])
        if self.display_message is None:
            await interaction.response.send_message(embed=self.embedList[embedIndex])
            self.display_message = await interaction.original_response()
        else:
            try:
                await self.display_message.edit(embed=self.embedList[embedIndex])
                await interaction.response.defer()
            except discord.NotFound:
                await interaction.response.send_message(embed=self.embedList[embedIndex])
                self.display_message = await interaction.original_response()


class MenuView(View):
    def __init__(self, embedList, pool):
        super().__init__()
        self.add_item(Menu(embedList, pool))


if __name__ == "__main__":
    pass