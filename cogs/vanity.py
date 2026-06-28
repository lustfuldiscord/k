import discord
from discord.ext import commands
from discord import app_commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Vanity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="vanity", invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def vanity_base(self, ctx: commands.Context):
        """Manage vanity role status reward configurations."""
        embed = discord.Embed(
            title="Vanity Subcommands",
            description="Available choices: set, remove, view",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @vanity_base.command(name="set", description="Configure the vanity status requirement string and reward role.")
    @app_commands.describe(vanity_string="The text string or invite link to look for", role="The role to award")
    @commands.has_permissions(manage_roles=True)
    async def vanity_set(self, ctx: commands.Context, vanity_string: str, role: discord.Role):
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send(embed=discord.Embed(description="That role is higher than my top role hierarchy placement.", color=DARK_COLOR))

        await self.bot.db.execute(
            "INSERT OR REPLACE INTO vanity_settings (guild_id, vanity_string, role_id) VALUES (?, ?, ?)",
            (ctx.guild.id, vanity_string, role.id)
        )
        await self.bot.db.commit()
        
        embed = discord.Embed(
            description=f"Setup complete. Users with `{vanity_string}` in their status will get {role.mention}.",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @vanity_base.command(name="remove", description="Disable vanity tracking for this server.")
    @commands.has_permissions(manage_roles=True)
    async def vanity_remove(self, ctx: commands.Context):
        await self.bot.db.execute("DELETE FROM vanity_settings WHERE guild_id = ?", (ctx.guild.id,))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description="Vanity tracking has been cleared and disabled.", color=DARK_COLOR))

    @vanity_base.command(name="view", description="View the current vanity reward configuration details.")
    async def vanity_view(self, ctx: commands.Context):
        async with self.bot.db.execute("SELECT vanity_string, role_id FROM vanity_settings WHERE guild_id = ?", (ctx.guild.id,)) as c:
            row = await c.fetchone()
        
        if not row:
            return await ctx.send(embed=discord.Embed(description="No vanity rules have been set up yet.", color=DARK_COLOR))
            
        role = ctx.guild.get_role(row[1])
        role_mention = role.mention if role else "`Deleted Role`"
        
        embed = discord.Embed(title="Vanity Configuration Settings", color=DARK_COLOR)
        embed.add_field(name="Required Text Phrase", value=f"`{row[0]}`", inline=True)
        embed.add_field(name="Reward Role", value=role_mention, inline=True)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if after.bot:
            return

        async with self.bot.db.execute("SELECT vanity_string, role_id FROM vanity_settings WHERE guild_id = ?", (after.guild.id,)) as c:
            row = await c.fetchone()
        if not row:
            return

        vanity_string, role_id = row[0], row[1]
        role = after.guild.get_role(role_id)
        if not role:
            return

        custom_status = None
        for activity in after.activities:
            if isinstance(activity, discord.CustomActivity):
                custom_status = activity.text
                break

        has_string = custom_status and (vanity_string in custom_status)
        has_role = role in after.roles

        try:
            if has_string and not has_role:
                await after.add_roles(role, reason="Vanity requirement met")
            elif not has_string and has_role:
                await after.remove_roles(role, reason="Vanity requirement no longer met")
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(Vanity(bot))