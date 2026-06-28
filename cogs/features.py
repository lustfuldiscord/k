import discord
from discord.ext import commands
from discord import app_commands
import datetime

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Features(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- AFK System ---
    @commands.hybrid_command(name="afk", description="Set an AFK status for this server.")
    @app_commands.describe(reason="The reason for going AFK")
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO guild_afk (guild_id, user_id, reason, timestamp) VALUES (?, ?, ?, ?)",
            (ctx.guild.id, ctx.author.id, reason, now)
        )
        await self.bot.db.commit()

        try:
            if ctx.author.nick and not ctx.author.nick.startswith("[AFK] "):
                await ctx.author.edit(nick=f"[AFK] {ctx.author.nick}")
            elif not ctx.author.nick:
                await ctx.author.edit(nick=f"[AFK] {ctx.author.name}")
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            description=f"You are now AFK in this server: **{reason}**", 
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    # --- Nicklock Subsystem ---
    @commands.hybrid_group(name="nicklock", invoke_without_command=True)
    @commands.has_permissions(manage_nicknames=True)
    async def nicklock_base(self, ctx: commands.Context):
        """Manage forced nicknames on users."""
        embed = discord.Embed(
            title="Nicklock Subcommands",
            description="Available options: set, remove",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @nicklock_base.command(name="set", description="Lock a user's nickname in this server.")
    @app_commands.describe(member="The target user", nickname="The nickname to force")
    @commands.has_permissions(manage_nicknames=True)
    async def nicklock_set(self, ctx: commands.Context, member: discord.Member, *, nickname: str):
        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send(embed=discord.Embed(description="That user has a higher role than me.", color=DARK_COLOR))

        await self.bot.db.execute(
            "INSERT OR REPLACE INTO nicklock (guild_id, user_id, nickname) VALUES (?, ?, ?)",
            (ctx.guild.id, member.id, nickname)
        )
        await self.bot.db.commit()

        try:
            await member.edit(nick=nickname, reason="Nickname locked by staff")
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            description=f"Locked {member.mention}'s nickname to `{nickname}`.", 
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @nicklock_base.command(name="remove", description="Unlock a user's nickname.")
    @app_commands.describe(member="The target user")
    @commands.has_permissions(manage_nicknames=True)
    async def nicklock_remove(self, ctx: commands.Context, member: discord.Member):
        await self.bot.db.execute("DELETE FROM nicklock WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, member.id))
        await self.bot.db.commit()

        embed = discord.Embed(
            description=f"Unlocked nickname restrictions for {member.mention}.", 
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    # --- Event Listeners ---
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # 1. Check if the message sender was AFK to clear it
        async with self.bot.db.execute(
            "SELECT 1 FROM guild_afk WHERE guild_id = ? AND user_id = ?", 
            (message.guild.id, message.author.id)
        ) as c:
            is_afk = await c.fetchone()

        if is_afk:
            await self.bot.db.execute(
                "DELETE FROM guild_afk WHERE guild_id = ? AND user_id = ?", 
                (message.guild.id, message.author.id)
            )
            await self.bot.db.commit()
            
            try:
                if message.author.nick and message.author.nick.startswith("[AFK] "):
                    await message.author.edit(nick=message.author.nick[6:])
            except discord.Forbidden:
                pass

            embed = discord.Embed(
                description=f"Welcome back {message.author.mention}, I removed your AFK status.", 
                color=DARK_COLOR
            )
            await message.channel.send(embed=embed, delete_after=5)

        # 2. Check if anyone was pinged who is currently AFK
        if message.mentions:
            for mentioned in message.mentions:
                if mentioned.bot or mentioned.id == message.author.id:
                    continue
                
                async with self.bot.db.execute(
                    "SELECT reason, timestamp FROM guild_afk WHERE guild_id = ? AND user_id = ?", 
                    (message.guild.id, mentioned.id)
                ) as c:
                    afk_row = await c.fetchone()
                
                if afk_row:
                    reason, ts_str = afk_row[0], afk_row[1]
                    ts = datetime.datetime.fromisoformat(ts_str)
                    unix_format = int(ts.timestamp())
                    
                    embed = discord.Embed(
                        description=f"{mentioned.mention} is AFK: **{reason}** — <t:{unix_format}:R>", 
                        color=DARK_COLOR
                    )
                    await message.channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.nick == after.nick:
            return

        async with self.bot.db.execute(
            "SELECT nickname FROM nicklock WHERE guild_id = ? AND user_id = ?", 
            (after.guild.id, after.id)
        ) as c:
            row = await c.fetchone()

        if row:
            locked_nick = row[0]
            if after.nick != locked_nick:
                try:
                    await after.edit(nick=locked_nick, reason="Enforcing nicklock configuration")
                except discord.Forbidden:
                    pass

async def setup(bot):
    await bot.add_cog(Features(bot))