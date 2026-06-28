import discord
from discord.ext import commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Simple runtime set to store blacklisted user IDs
        self.blacklist = set()

        # Register the global check to block blacklisted users
        @bot.check
        async def check_global_blacklist(ctx: commands.Context):
            return ctx.author.id not in self.blacklist

    async def cog_check(self, ctx: commands.Context):
        return await self.bot.is_owner(ctx.author)

    @commands.command(name="sync")
    async def sync_tree(self, ctx: commands.Context):
        """Sync global slash application command structures."""
        await self.bot.tree.sync()
        await ctx.send(embed=discord.Embed(description="Global command tree synced successfully.", color=DARK_COLOR))

    @commands.command(name="status")
    async def change_status(self, ctx: commands.Context, *, status_text: str):
        """Update the bot global playing status text."""
        await self.bot.change_presence(activity=discord.Game(name=status_text))
        await ctx.send(embed=discord.Embed(description=f"Status text updated to: `{status_text}`", color=DARK_COLOR))

    @commands.command(name="servers")
    async def list_servers(self, ctx: commands.Context):
        """List all servers the bot is currently in."""
        if not self.bot.guilds:
            return await ctx.send(embed=discord.Embed(description="The bot is not currently in any servers.", color=DARK_COLOR))

        lines = [f"**{guild.name}** (`{guild.id}`) - {guild.member_count} members" for guild in self.bot.guilds]
        output = "\n".join(lines)

        # Handle message length limits if the bot is in a massive amount of servers
        if len(output) > 2000:
            output = output[:1950] + "\n...and more servers."

        embed = discord.Embed(title=f"Active Servers ({len(self.bot.guilds)})", description=output, color=DARK_COLOR)
        await ctx.send(embed=embed)

    @commands.command(name="globalban")
    async def global_ban(self, ctx: commands.Context, user_id: int):
        """Blacklist a user from using any bot commands globally."""
        if user_id == ctx.author.id:
            return await ctx.send(embed=discord.Embed(description="You cannot global ban yourself.", color=DARK_COLOR))

        if user_id in self.blacklist:
            self.blacklist.remove(user_id)
            embed = discord.Embed(description=f"Removed user ID `{user_id}` from the global blacklist.", color=DARK_COLOR)
        else:
            self.blacklist.add(user_id)
            embed = discord.Embed(description=f"Successfully global banned user ID `{user_id}` from all bot interactions.", color=DARK_COLOR)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Owner(bot))