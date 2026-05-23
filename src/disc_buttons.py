from discord.ui import View
import discord

class Menu(discord.ui.Select):
    def __init__(self, embedList, pool, pool_image=None, tipo=0):
        self.embedList = embedList
        self.display_message = None
        self.tipo = tipo
        self.pool = pool

        options = []
        if pool_image is not None:
            for i, mapa in enumerate(pool):
                if i in pool_image:
                    options.append(
                        discord.SelectOption(
                            label=mapa,
                            value=i+1,
                            description=f"Informações sobre o mapa {mapa}",
                            emoji="🗺️"
                        )
                    )
        else:
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
            description="Informações gerais",
            emoji="📋"
            )
        )

        options.append(
            discord.SelectOption(
                label="Stats",
                value=len(pool)+1,
                description="Médias estatísticas historicamente",
                emoji="📊"
            )
        )

        if tipo == 0:
            min_val = 1
            max_val = 1
        elif tipo == 1:
            min_val = 3
            max_val = 5
            options = options[1:-1]
        super().__init__(placeholder="Draft:", min_values=min_val, max_values=max_val, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.tipo == 1:
            if self.display_message is None:
                pool = []
                for map in self.values:
                    pool.append(int(map)-1)

                await interaction.response.send_message(
                    embed=self.embedList[0], 
                    view=MenuView(
                        self.embedList[1:], 
                        self.pool,
                        pool, 
                        tipo=0)
                    )
                self.display_message = await interaction.original_response()
            else:
                pool = []
                for map in self.values:
                    pool.append(int(map)-1)

                try:
                    await self.display_message.edit(
                        embed=self.embedList[0], 
                        view=MenuView(
                            self.embedList[1:], 
                            self.pool,
                            pool, 
                            tipo=0)
                        )
                    await interaction.response.defer()
                except discord.NotFound:
                    await interaction.response.send_message(
                        embed=self.embedList[0], 
                        view=MenuView(
                            self.embedList[1:], 
                            self.pool,
                            pool, 
                            tipo=0)
                        )
                    self.display_message = await interaction.original_response()
        else:
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
    def __init__(self, embedList, pool, pool_image=None, tipo=0):
        super().__init__()
        self.add_item(Menu(embedList, pool, pool_image=pool_image, tipo=tipo))


if __name__ == "__main__":
    pass