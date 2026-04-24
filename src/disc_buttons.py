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





if __name__ == "__main__":

    pass 




#       GEMINI CODE

'''
class BotaoInteracao(View):
    def __init__(self, mensagem_inicial):
        super().__init__()
        self.mensagem_inicial = mensagem_inicial

    @discord.ui.button(label="Opção A", style=discord.ButtonStyle.primary)
    async def botao_a(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content=f"{self.mensagem_inicial}\n\nUsuário escolheu a Opção A!", view=None)

    @discord.ui.button(label="Opção B", style=discord.ButtonStyle.secondary)
    async def botao_b(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content=f"{self.mensagem_inicial}\n\nUsuário escolheu a Opção B!", view=None)
'''