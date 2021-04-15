import discord

class DiscordMultipleChoice:
    def __init__(self, ctx, bot, multiple_choice=True):
        self.ctx = ctx
        self.message = None
        self.emojies = ["1️⃣","2️⃣","3️⃣", "4️⃣", "5️⃣"] if multiple_choice else ["👍", "👎"]
        self.bot = bot
        self.numberOfChoices = None

    def check_if_valid_reaction(self, reaction, user):
        if reaction.message.id != self.message.id:
            return False
        if user != self.ctx.message.author:
            return False
        if str(reaction.emoji) not in self.emojies[:self.numberOfChoices]:
            return False
        return True
        

    async def createMessage(self, title, text, numberOfChoices=5):
        message = discord.Embed(title=title, description=text)
        if (numberOfChoices > len(self.emojies)):
            numberOfChoices = len(self.emojies)
        self.numberOfChoices = numberOfChoices
        if self.message == None:
            self.message = await self.ctx.send(embed=message)
        else:
            await self.message.edit(embed=message)
        for i in range(numberOfChoices):
            await self.message.add_reaction(self.emojies[i])
        res, user = await self.bot.wait_for('reaction_add', check=self.check_if_valid_reaction)
        for i in range(numberOfChoices):
            if (self.emojies[i] in str(res.emoji)):
                await self.message.remove_reaction(self.emojies[i], user)
                return i + 1