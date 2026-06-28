import discord
from discord.ext import commands
from discord import app_commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="settings", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def settings_base(self, ctx):
        """View or manage your server's configuration settings."""
        async with self.bot.db.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (ctx.guild.id,)) as c:
            row = await c.fetchone()

        embed = discord.Embed(title="Server Settings Configuration", color=DARK_COLOR)
        
        if not row:
            embed.description = "No custom configurations saved. Using default parameters."
            return await ctx.send(embed=embed)

        # Map current database configurations to view
        embed.add_field(name="Base Role", value=f"<@&{row[2]}>" if row[2] else "Not configured", inline=True)
        embed.add_field(name="Muted Role", value=f"<@&{row[13]}>" if row[13] else "Not configured", inline=True)
        embed.add_field(name="Jail Role", value=f"<@&{row[14]}>" if row[14] else "Not configured", inline=True)
        embed.add_field(name="Mod Log Channel", value=f"<#{row[8]}>" if row[8] else "Not configured", inline=True)
        embed.add_field(name="Join Log Channel", value=f"<#{row[9]}>" if row[9] else "Not configured", inline=True)
        embed.add_field(name="Auto-Nick Template", value=f"`{row[5]}`" if row[5] else "Disabled", inline=True)

        await ctx.send(embed=embed)

    @settings_base.command(name="baserole")
    @app_commands.describe(role="The primary base role given to members")
    async def set_baserole(self, ctx, role: discord.Role):
        """Configure the baseline role for members."""
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, baserole_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET baserole_id=excluded.baserole_id",
            (ctx.guild.id, role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Base role updated to {role.mention}.", color=DARK_COLOR))

    @settings_base.command(name="muterole")
    @app_commands.describe(role="The role applied to muted members")
    async def set_muterole(self, ctx, role: discord.Role):
        """Configure the role applied to muted accounts."""
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, muted_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET muted_id=excluded.muted_id",
            (ctx.guild.id, role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Mute role updated to {role.mention}.", color=DARK_COLOR))

    @settings_base.command(name="jailrole")
    @app_commands.describe(role="The role applied to jailed members")
    async def set_jailrole(self, ctx, role: discord.Role):
        """Configure the role applied to restricted jailed accounts."""
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, jailrole_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET jailrole_id=excluded.jailrole_id",
            (ctx.guild.id, role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Jail role updated to {role.mention}.", color=DARK_COLOR))

    @settings_base.command(name="modlogs")
    @app_commands.describe(channel="The channel where mod actions are logged")
    async def set_modlogs(self, ctx, channel: discord.TextChannel):
        """Configure the moderation actions logging channel."""
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, modlog_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET modlog_id=excluded.modlog_id",
            (ctx.guild.id, channel.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Moderation logs routed to {channel.mention}.", color=DARK_COLOR))

    @settings_base.command(name="joinlogs")
    @app_commands.describe(channel="The channel where member joins are logged")
    async def set_joinlogs(self, ctx, channel: discord.TextChannel):
        """Configure the user join logs channel."""
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, joinlogs_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET joinlogs_id=excluded.joinlogs_id",
            (ctx.guild.id, channel.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Join logs routed to {channel.mention}.", color=DARK_COLOR))

    @settings_base.command(name="autonick")
    @app_commands.describe(nickname="The template forced on new accounts (leave empty to disable)")
    async def set_autonick(self, ctx, *, nickname: str = None):
        """Configure or clear an automated forced join nickname template."""
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, autonick) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET autonick=excluded.autonick",
            (ctx.guild.id, nickname)
        )
        await self.bot.db.commit()
        
        status = f"set to `{nickname}`" if nickname else "disabled"
        await ctx.send(embed=discord.Embed(description=f"Auto-nickname template has been {status}.", color=DARK_COLOR))

async def setup(bot):
    await bot.add_cog(Settings(bot))