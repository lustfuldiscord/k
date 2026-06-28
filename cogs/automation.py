import discord
from discord.ext import commands, tasks
from typing import Optional

class AutomationEngine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_cache = {}  # Tracks last sticky message ID to avoid chat clutter
        self.cleanup_inactive_roles.start()

    def cog_unload(self):
        self.cleanup_inactive_roles.cancel()

    # ==========================================
    # 1. BOOSTER AUTOMATION & CLEANUP
    # ==========================================
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Detects when a member starts boosting
        if not before.premium_since and after.premium_since:
            async with self.bot.db.execute(
                "SELECT baserole_id FROM guild_settings WHERE guild_id = ?", 
                (after.guild.id,)
            ) as cursor:
                row = await cursor.fetchone()
                
            if row and row[0]:
                base_role = after.guild.get_role(row[0])
                if base_role:
                    try:
                        await after.add_roles(base_role, reason="Automation: User started boosting.")
                    except discord.Forbidden:
                        pass

    @tasks.loop(hours=24)
    async def cleanup_inactive_roles(self):
        """Background sweep to strip custom roles from expired boosters every 24 hours"""
        async with self.bot.db.execute("SELECT guild_id, user_id, role_id FROM booster_roles") as cursor:
            rows = await cursor.fetchall()

        for guild_id, user_id, role_id in rows:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue

            member = guild.get_member(user_id)
            # If they left the server or stopped boosting
            if not member or not member.premium_since:
                role = guild.get_role(role_id)
                if role:
                    try:
                        await role.delete(reason="Automation: User is no longer boosting.")
                    except discord.Forbidden:
                        continue
                
                await self.bot.db.execute(
                    "DELETE FROM booster_roles WHERE guild_id = ? AND user_id = ?", 
                    (guild_id, user_id)
                )
        await self.bot.db.commit()

    # ==========================================
    # 2. JOIN EVENTS (AUTONICK & WELCOME)
    # ==========================================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        
        # Auto-Nickname Application
        async with self.bot.db.execute(
            "SELECT autonick FROM guild_settings WHERE guild_id = ?", 
            (guild.id,)
        ) as cursor:
            row = await cursor.fetchone()
            
        if row and row[0]:
            target_nick = row[0].replace("{user}", member.name)
            try:
                await member.edit(nick=target_nick, reason="Automation: Auto-nickname applied.")
            except discord.Forbidden:
                pass

        # Welcome Message Dispatching
        async with self.bot.db.execute(
            "SELECT channel_id, message FROM welcome_settings WHERE guild_id = ?", 
            (guild.id,)
        ) as cursor:
            welcome_data = await cursor.fetchone()

        if welcome_data:
            channel_id, raw_msg = welcome_data
            channel = guild.get_channel(channel_id)
            if channel:
                formatted_msg = raw_msg.format(
                    user=member.mention,
                    server=guild.name,
                    count=guild.member_count
                )
                embed = discord.Embed(description=formatted_msg, color=discord.Color.dark_theme())
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    # ==========================================
    # 3. CHAT AUTOMATION (STICKY MESSAGES)
    # ==========================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        async with self.bot.db.execute(
            "SELECT message FROM sticky_messages WHERE channel_id = ?", 
            (message.channel.id,)
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            sticky_content = row[0]
            
            # Delete old sticky instance to keep chat clean
            if message.channel.id in self.sticky_cache:
                try:
                    old_msg = await message.channel.fetch_message(self.sticky_cache[message.channel.id])
                    await old_msg.delete()
                except (discord.NotFound, discord.Forbidden):
                    pass

            # Send the new sticky anchor at the bottom
            embed = discord.Embed(description=sticky_content, color=discord.Color.dark_theme())
            new_sticky = await message.channel.send(embed=embed)
            self.sticky_cache[message.channel.id] = new_sticky.id

async def setup(bot):
    await bot.add_cog(AutomationEngine(bot))