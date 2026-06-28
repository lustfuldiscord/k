import discord
from discord.ext import commands
from discord import app_commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="prefix", fallback="view", invoke_without_command=True)
    async def prefix_base(self, ctx):
        """View the current operational prefixes for this server and your account."""
        if not ctx.guild:
            return await ctx.send(embed=discord.Embed(description="This command can only be executed inside a server.", color=DARK_COLOR))

        async with self.bot.db.execute("SELECT prefix FROM guild_settings WHERE guild_id = ?", (ctx.guild.id,)) as c:
            g_row = await c.fetchone()
        async with self.bot.db.execute("SELECT prefix FROM user_prefixes WHERE user_id = ?", (ctx.author.id,)) as c:
            u_row = await c.fetchone()
        
        g_pref = g_row[0] if g_row else ","
        u_pref = u_row[0] if u_row else "None configured"
        
        embed = discord.Embed(title="Prefix Configuration Status", color=DARK_COLOR)
        embed.add_field(name="Guild Default Prefix", value=f"`{g_pref}`", inline=False)
        embed.add_field(name="Personal User Override", value=f"`{u_pref}`", inline=False)
        await ctx.send(embed=embed)

    @prefix_base.command(name="self")
    @app_commands.describe(prefix="The new custom prefix for your personal commands execution")
    async def prefix_self(self, ctx, prefix: str):
        """Configure a personal custom prefix override for yourself."""
        if len(prefix) > 5:
            return await ctx.send(embed=discord.Embed(description="Prefix length cannot exceed 5 characters.", color=DARK_COLOR))

        await self.bot.db.execute("INSERT OR REPLACE INTO user_prefixes (user_id, prefix) VALUES (?, ?)", (ctx.author.id, prefix))
        await self.bot.db.commit()
        
        embed = discord.Embed(description=f"Personal prefix override successfully set to `{prefix}`", color=DARK_COLOR)
        await ctx.send(embed=embed)

    @prefix_base.command(name="set")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(prefix="The new default prefix for this entire server")
    async def prefix_set(self, ctx, prefix: str):
        """Configure a server-wide default prefix override."""
        if len(prefix) > 5:
            return await ctx.send(embed=discord.Embed(description="Prefix length cannot exceed 5 characters.", color=DARK_COLOR))

        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, prefix) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET prefix=excluded.prefix", 
            (ctx.guild.id, prefix)
        )
        await self.bot.db.commit()
        
        embed = discord.Embed(description=f"Guild baseline prefix updated to `{prefix}`", color=DARK_COLOR)
        await ctx.send(embed=embed)

    @prefix_base.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def prefix_remove(self, ctx):
        """Revert the server-wide custom prefix back to the global default system parameter."""
        await self.bot.db.execute("INSERT INTO guild_settings (guild_id, prefix) VALUES (?, ',') ON CONFLICT(guild_id) DO UPDATE SET prefix=','", (ctx.guild.id,))
        await self.bot.db.commit()
        
        embed = discord.Embed(description="Guild default prefix reverted back to system baseline `,`", color=DARK_COLOR)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Prefix(bot))