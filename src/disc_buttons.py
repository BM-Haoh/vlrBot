from discord.ui import View, Button
import discord

class EmbedChangePage(View):
    def __init__(self, embedList, embedIndex):
        super().__init__()
        self.embedList = embedList
        self.embedIndex = embedIndex

    @discord.ui.button(label="Página Anterior", style=discord.ButtonStyle.primary)
    async def button_prev(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if self.embedIndex > 0:
            self.embedIndex -= 1
            await interaction.edit_original_response(embed=self.embedList[self.embedIndex])
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Próxima Página", style=discord.ButtonStyle.primary)
    async def button_next(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        if self.embedIndex < len(self.embedList) - 1:
            self.embedIndex += 1
            await interaction.edit_original_response(embed=self.embedList[self.embedIndex])
        else:
            await interaction.response.defer()

class Menu(discord.ui.Select):
    def __init__(self, embedList):
        self.embedList = embedList
        self.display_message = None

        options = [
            discord.SelectOption(
                label="Overview",
                value=0,
                description="Informações gerais do time",
                emoji="📋"
            ),
            discord.SelectOption(
                label="Maps",
                value=1,
                description="atk/def/map win%",
                emoji="🗺️"
            ),

            discord.SelectOption(
                label="Stats",
                value=2,
                description="Médias estatísticas do time historicamente",
                emoji="📊"
            )
        ]

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


class MenuView(discord.ui.View):
    def __init__(self, embedList):
        super().__init__()
        self.add_item(Menu(embedList))




if __name__ == "__main__":
    pass