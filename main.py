import asyncio
import os
import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
from dotenv import load_dotenv

load_dotenv()

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

async def get_prefix(bot, message):
    if not message.guild:
        return ","
        
    async with bot.db.execute("SELECT prefix FROM user_prefixes WHERE user_id = ?", (message.author.id,)) as cursor:
        user_row = await cursor.fetchone()
        if user_row:
            return user_row[0]
            
    async with bot.db.execute("SELECT prefix FROM guild_settings WHERE guild_id = ?", (message.guild.id,)) as cursor:
        guild_row = await cursor.fetchone()
        if guild_row:
            return guild_row[0]
            
    return ","

class CoreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=get_prefix, 
            intents=intents, 
            help_command=None,
            owner_ids={1446215395358015559}
        )
        self.db = None

    async def setup_hook(self):
        self.db = await aiosqlite.connect("bot_database.db")
        
        with open("schema.sql", "r") as f:
            await self.db.executescript(f.read())
        await self.db.commit()

        initial_extensions = [
            "cogs.prefix",
            "cogs.boosterrole",
            "cogs.settings",
            "cogs.automation",
            "cogs.utility",
            "cogs.moderation",
            "cogs.voice",
            "cogs.setup",
            "cogs.welcome",
            "cogs.help",
            "cogs.roblox",
            "cogs.features",
            "cogs.owner"
        ]
        
        for ext in initial_extensions:
            try:
                await self.load_extension(ext)
                print(f"Loaded extension: {ext}")
            except Exception as e:
                print(f"Failed to load extension {ext}: {e}")
        
        self.tree.on_error = self.on_app_command_error
        await self.tree.sync()

    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        error = getattr(error, 'original', error)

        if isinstance(error, discord.Forbidden):
            msg = "I do not have permissions to do that."
        elif isinstance(error, app_commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions).replace("_", " ").title()
            msg = f"You need the following permission: `{missing_perms}`"
        elif isinstance(error, app_commands.CommandOnCooldown):
            msg = f"Cooldown. Try again in `{error.retry_after:.2f}s`."
        else:
            msg = f"An error occurred: `{error}`"

        if interaction.response.is_done():
            await interaction.followup.send(content=msg, ephemeral=True)
        else:
            await interaction.response.send_message(content=msg, ephemeral=True)

    async def close(self):
        if self.db:
            await self.db.close()
        await super().close()

bot = CoreBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")

# Clean global message listener that allows command processing alongside cog hooks
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
        
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, 'on_error'):
        return

    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound):
        return
        
    elif isinstance(error, discord.Forbidden):
        await ctx.send("I do not have permissions to do that.")
        
    elif isinstance(error, commands.MissingPermissions):
        missing_perms = ", ".join(error.missing_permissions).replace("_", " ").title()
        await ctx.send(f"You need the following permission: `{missing_perms}`")
        
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Cooldown. Try again in `{error.retry_after:.2f}s`.")
        
    elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
        await ctx.send(f"Incorrect usage. Try: `{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`")
        
    else:
        await ctx.send(f"An error occurred: `{error}`")

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN is missing from .env")
    bot.run(token)
