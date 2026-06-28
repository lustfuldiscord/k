import discord
from discord.ext import commands
from discord import app_commands
import time

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Features(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Autorole System Commands ---
    @commands.hybrid_group(name="autorole", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def autorole_base(self, ctx: commands.Context):
        """Manage automatic role assignment configurations for new members."""
        pref = ctx.prefix
        embed = discord.Embed(
            title="Autorole Settings",
            description=f"Use `{pref}autorole set <role>` to set a role.\nUse `{pref}autorole remove` to disable it.",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @autorole_base.command(name="set", description="Set a role to be automatically given to joining members.")
    @app_commands.describe(role="The role to assign to new members")
    @commands.has_permissions(administrator=True)
    async def autorole_set(self, ctx: commands.Context, role: discord.Role):
        if role.position >= ctx.guild.me.top_role.position:
            return await ctx.send(embed=discord.Embed(description="I cannot assign that role because it is higher than my highest role.", color=DARK_COLOR))

        await self.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, autorole_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET autorole_id = ?",
            (ctx.guild.id, role.id, role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Successfully set {role.mention} as the server autorole.", color=DARK_COLOR))

    @autorole_base.command(name="remove", description="Disable automatic role assignment.")
    @commands.has_permissions(administrator=True)
    async def autorole_remove(self, ctx: commands.Context):
        await self.bot.db.execute("UPDATE guild_settings SET autorole_id = NULL WHERE guild_id = ?", (ctx.guild.id,))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description="Disabled the server autorole system.", color=DARK_COLOR))

    # --- Honeypot System Commands ---
    @commands.hybrid_group(name="honeypot", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def honeypot_base(self, ctx: commands.Context):
        """Manage honeypot trap channels."""
        embed = discord.Embed(title="Honeypot Subcommands", description="Available options: add, remove, list", color=DARK_COLOR)
        await ctx.send(embed=embed)

    @honeypot_base.command(name="add", description="Designate a channel as a honeypot trap.")
    @app_commands.describe(channel="The channel to turn into a trap")
    @commands.has_permissions(administrator=True)
    async def honeypot_add(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.db.execute("INSERT OR IGNORE INTO honeypots (guild_id, channel_id) VALUES (?, ?)", (ctx.guild.id, channel.id))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Successfully set {channel.mention} as a honeypot trap channel.", color=DARK_COLOR))

    @honeypot_base.command(name="remove", description="Remove honeypot status from a channel.")
    @app_commands.describe(channel="The honeypot channel to remove")
    @commands.has_permissions(administrator=True)
    async def honeypot_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.db.execute("DELETE FROM honeypots WHERE guild_id = ? AND channel_id = ?", (ctx.guild.id, channel.id))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Removed honeypot status from {channel.mention}.", color=DARK_COLOR))

    @honeypot_base.command(name="list", description="List all active server honeypots.")
    @commands.has_permissions(administrator=True)
    async def honeypot_list(self, ctx: commands.Context):
        async with self.bot.db.execute("SELECT channel_id FROM honeypots WHERE guild_id = ?", (ctx.guild.id,)) as c:
            rows = await c.fetchall()
        channels = [f"<#{r[0]}>" for r in rows if ctx.guild.get_channel(r[0])]
        embed = discord.Embed(title="Active Honeypots", description=", ".join(channels) if channels else "No active honeypots.", color=DARK_COLOR)
        await ctx.send(embed=embed)

    # --- Nicklock Command ---
    @commands.hybrid_command(name="nicklock", description="Force lock a user's nickname.")
    @commands.has_permissions(manage_nicknames=True)
    @app_commands.describe(member="The member to lock", nickname="The nickname to force apply")
    async def nicklock(self, ctx: commands.Context, member: discord.Member, *, nickname: str):
        """Force a nickname onto a member and lock it against changes."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="Hierarchy lock error: Target possesses higher roles.", color=DARK_COLOR))
            
        await self.bot.db.execute(
            "INSERT INTO nicklock (guild_id, user_id, nickname) VALUES (?, ?, ?) ON CONFLICT(guild_id, user_id) DO UPDATE SET nickname = ?",
            (ctx.guild.id, member.id, nickname, nickname)
        )
        await self.bot.db.commit()
        try:
            await member.edit(nick=nickname, reason="Nickname locked by staff")
        except discord.Forbidden:
            pass
        await ctx.send(embed=discord.Embed(description=f"Locked nickname for {member.mention} to `{nickname}`.", color=DARK_COLOR))

    # --- AFK Command ---
    @commands.hybrid_command(name="afk", description="Set an AFK status message.")
    @app_commands.describe(reason="The reason you are going away")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        """Set your status to away. The bot will notify users who mention you."""
        await self.bot.db.execute(
            "INSERT INTO guild_afk (guild_id, user_id, reason, timestamp) VALUES (?, ?, ?, ?) ON CONFLICT(guild_id, user_id) DO UPDATE SET reason = ?, timestamp = ?",
            (ctx.guild.id, ctx.author.id, reason, str(int(time.time())), reason, str(int(time.time())))
        )
        await self.bot.db.commit()
        
        # Safely attempt nickname adjust to show [AFK]
        try:
            if not ctx.author.nick or not ctx.author.nick.startswith("[AFK]"):
                current_nick = ctx.author.display_name
                await ctx.author.edit(nick=f"[AFK] {current_nick}"[:32])
        except discord.Forbidden:
            pass
            
        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is now AFK: **{reason}**", color=DARK_COLOR))

    # --- System Event Listeners ---

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Autorole assignment handler."""
        if member.bot:
            return
        async with self.bot.db.execute("SELECT autorole_id FROM guild_settings WHERE guild_id = ?", (member.guild.id,)) as c:
            row = await c.fetchone()
        if row and row[0]:
            role = member.guild.get_role(row[0])
            if role:
                try:
                    await member.add_roles(role, reason="Autorole assignment")
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Nickname lock protection handler and Custom Status Vanity role checker."""
        # 1. Nicklock Check
        async with self.bot.db.execute("SELECT nickname FROM nicklock WHERE guild_id = ? AND user_id = ?", (after.guild.id, after.id)) as c:
            row = await c.fetchone()
        if row and after.nick != row[0]:
            try:
                await after.edit(nick=row[0], reason="Forced nicklock enforcement")
            except discord.Forbidden:
                pass

        # 2. Vanity Custom Status Tracker Check
        async with self.bot.db.execute("SELECT vanity_string, role_id FROM vanity_settings WHERE guild_id = ?", (after.guild.id,)) as c:
            vanity_row = await c.fetchone()
            
        if vanity_row:
            required_string, role_id = vanity_row[0], vanity_row[1]
            target_role = after.guild.get_role(role_id)
            
            if target_role:
                # Find custom status text
                custom_status = None
                for act in after.activities:
                    if isinstance(act, discord.CustomActivity):
                        custom_status = act.name
                        break
                
                has_string = custom_status and required_string in custom_status
                has_role = target_role in after.roles
                
                try:
                    if has_string and not has_role:
                        await after.add_roles(target_role, reason="Vanity status reward")
                    elif not has_string and has_role:
                        await after.remove_roles(target_role, reason="Removed vanity string from status")
                except discord.Forbidden:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # 1. Honeypot Check
        async with self.bot.db.execute("SELECT 1 FROM honeypots WHERE guild_id = ? AND channel_id = ?", (message.guild.id, message.channel.id)) as c:
            if await c.fetchone():
                if not message.author.guild_permissions.administrator and message.author.top_role < message.guild.me.top_role:
                    try:
                        await message.guild.ban(message.author, reason="Triggered honeypot trap channel", delete_message_days=1)
                        await message.guild.unban(message.author, reason="Honeypot softban complete")
                        async with self.bot.db.execute("SELECT modlog_id FROM guild_settings WHERE guild_id = ?", (message.guild.id,)) as ml:
                            log_row = await ml.fetchone()
                        if log_row and log_row[0]:
                            log_channel = message.guild.get_channel(log_row[0])
                            if log_channel:
                                await log_channel.send(embed=discord.Embed(
                                    title="Honeypot Triggered",
                                    description=f"**User:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Action:** Softbanned.",
                                    color=DARK_COLOR
                                ))
                    except discord.Forbidden:
                        pass
                    return

        # 2. AFK Return Check
        async with self.bot.db.execute("SELECT 1 FROM guild_afk WHERE guild_id = ? AND user_id = ?", (message.guild.id, message.author.id)) as c:
            if await c.fetchone():
                await self.bot.db.execute("DELETE FROM guild_afk WHERE guild_id = ? AND user_id = ?", (message.guild.id, message.author.id))
                await self.bot.db.commit()
                try:
                    if message.author.nick and message.author.nick.startswith("[AFK]"):
                        clean_nick = message.author.nick.replace("[AFK] ", "", 1)
                        await message.author.edit(nick=clean_nick)
                except discord.Forbidden:
                    pass
                await message.channel.send(f"Welcome back {message.author.mention}, I have removed your AFK status.")

        # 3. AFK Mention Notification Check
        if message.mentions:
            for member in message.mentions:
                if member.bot or member.id == message.author.id:
                    continue
                async with self.bot.db.execute("SELECT reason, timestamp FROM guild_afk WHERE guild_id = ? AND user_id = ?", (message.guild.id, member.id)) as c:
                    afk_row = await c.fetchone()
                if afk_row:
                    await message.channel.send(embed=discord.Embed(
                        description=f"{member.mention} went AFK <t:{afk_row[1]}:R>: **{afk_row[0]}**",
                        color=DARK_COLOR
                    ))

async def setup(bot):
    await bot.add_cog(Features(bot))
