import discord
from discord.ext import commands
from discord import app_commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Base Settings Group ---
    @commands.hybrid_group(name="settings", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def settings_base(self, ctx: commands.Context):
        """View or modify configuration parameters for server operations."""
        pref = ctx.prefix
        embed = discord.Embed(
            title="Server Settings Subcommands",
            description=(
                f"Configure the bot with the following subcommands:\n\n"
                f"`{pref}settings welcomechannel <channel>`\n"
                f"`{pref}settings baserole <role>`\n"
                f"`{pref}settings muterole <role>`\n"
                f"`{pref}settings jailrole <role>`\n"
                f"`{pref}settings modlogs <channel>`\n"
                f"`{pref}settings joinlogs <channel>`\n"
                f"`{pref}settings autonick <text>`\n"
                f"`{pref}autorole set <role>`\n"
                f"`{pref}vanity set <text> <role>`"
            ),
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @settings_base.command(name="welcomechannel", description="Set the text channel where welcome messages are delivered.")
    @app_commands.describe(channel="The target text channel")
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, welcome_channel_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET welcome_channel_id = ?",
            (ctx.guild.id, channel.id, channel.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Welcome channel set to {channel.mention}.", color=DARK_COLOR))

    @settings_base.command(name="baserole", description="Configure the primary verified identifier role assigned to members.")
    @app_commands.describe(role="The server member identity role")
    @commands.has_permissions(administrator=True)
    async def set_base_role(self, ctx: commands.Context, role: discord.Role):
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, baserole_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET baserole_id = ?",
            (ctx.guild.id, role.id, role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Base member verification role set to {role.mention}.", color=DARK_COLOR))

    @settings_base.command(name="muterole", description="Configure the mute role applied to users to strip talking permissions.")
    @app_commands.describe(role="The mute restriction role override setup")
    @commands.has_permissions(administrator=True)
    async def set_mute_role(self, ctx: commands.Context, role: discord.Role):
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, muterole_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET muterole_id = ?",
            (ctx.guild.id, role.id, role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Muted restriction role set to {role.mention}.", color=DARK_COLOR))

    @settings_base.command(name="jailrole", description="Configure the role used to strip visibility and lock users in the jail channel.")
    @app_commands.describe(role="The isolated cell block restriction role")
    @commands.has_permissions(administrator=True)
    async def set_jail_role(self, ctx: commands.Context, role: discord.Role):
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, jailrole_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET jailrole_id = ?",
            (ctx.guild.id, role.id, role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Jail restriction role set to {role.mention}.", color=DARK_COLOR))

    @settings_base.command(name="modlogs", description="Set the text channel where logging files for staff moderation events are sent.")
    @app_commands.describe(channel="The target moderation logging channel")
    @commands.has_permissions(administrator=True)
    async def set_mod_logs(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, modlog_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET modlog_id = ?",
            (ctx.guild.id, channel.id, channel.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Moderation event logs channel set to {channel.mention}.", color=DARK_COLOR))

    @settings_base.command(name="joinlogs", description="Set the text channel where member server entry logs are delivered.")
    @app_commands.describe(channel="The target audit stream channel")
    @commands.has_permissions(administrator=True)
    async def set_join_logs(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, joinlogs_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET joinlogs_id = ?",
            (ctx.guild.id, channel.id, channel.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Member entry tracking logs channel set to {channel.mention}.", color=DARK_COLOR))

    @settings_base.command(name="autonick", description="Set a formatting template text pattern applied to new members when joining.")
    @app_commands.describe(text="The string text template pattern configuration layout")
    @commands.has_permissions(administrator=True)
    async def set_auto_nick(self, ctx: commands.Context, *, text: str):
        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, autonick) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET autonick = ?",
            (ctx.guild.id, text, text)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Automated moniker template layout set to `{text}`.", color=DARK_COLOR))

    # --- Vanity Custom Status Group ---
    @commands.hybrid_group(name="vanity", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def vanity_base(self, ctx: commands.Context):
        """Manage custom text string rewards parameters for member profiles."""
        pref = ctx.prefix
        embed = discord.Embed(
            title="Vanity Reward Settings",
            description=f"Use `{pref}vanity set <text> <role>` to configure.\nUse `{pref}vanity remove` to disable.",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @vanity_base.command(name="set", description="Configure a reward role given to users who put a text phrase in their status.")
    @app_commands.describe(text="The matching text phrase required", role="The prize role given out")
    @commands.has_permissions(administrator=True)
    async def vanity_set(self, ctx: commands.Context, text: str, role: discord.Role):
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send(embed=discord.Embed(description="I cannot assign that role because it sits above my hierarchy layer role.", color=DARK_COLOR))

        await self.bot.db.execute(
            "INSERT INTO vanity_settings (guild_id, vanity_string, role_id) VALUES (?, ?, ?) ON CONFLICT(guild_id) DO UPDATE SET vanity_string = ?, role_id = ?",
            (ctx.guild.id, text, role.id, text, role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Vanity rewards configured. Users matching `{text}` will receive {role.mention}.", color=DARK_COLOR))

    @vanity_base.command(name="remove", description="Disable vanity tracking configurations.")
    @commands.has_permissions(administrator=True)
    async def vanity_remove(self, ctx: commands.Context):
        await self.bot.db.execute("DELETE FROM vanity_settings WHERE guild_id = ?", (ctx.guild.id,))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description="Successfully deleted server vanity tracker reward systems.", color=DARK_COLOR))

    @vanity_base.command(name="view", description="View currently configured vanity parameters.")
    async def vanity_view(self, ctx: commands.Context):
        async with self.bot.db.execute("SELECT vanity_string, role_id FROM vanity_settings WHERE guild_id = ?", (ctx.guild.id,)) as c:
            row = await c.fetchone()
        
        if not row:
            return await ctx.send(embed=discord.Embed(description="No vanity status rewards are configured on this server.", color=DARK_COLOR))
            
        role = ctx.guild.get_role(row[1])
        embed = discord.Embed(title="Active Server Vanity Reward Parameters", color=DARK_COLOR)
        embed.add_field(name="Required Matching String", value=f"`{row[0]}`", inline=True)
        embed.add_field(name="Assigned Reward Role", value=role.mention if role else "Unknown/Deleted Role", inline=True)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))
