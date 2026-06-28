import discord
from discord.ext import commands
from discord import app_commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Features(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- Honeypot System Commands ---
    @commands.hybrid_group(name="honeypot", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def honeypot_base(self, ctx: commands.Context):
        """Manage honeypot trap channels."""
        embed = discord.Embed(
            title="Honeypot Subcommands",
            description="Available options: add, remove, list",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @honeypot_base.command(name="add", description="Designate a channel as a honeypot trap.")
    @app_commands.describe(channel="The channel to turn into a trap")
    @commands.has_permissions(administrator=True)
    async def honeypot_add(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.db.execute(
            "INSERT OR IGNORE INTO honeypots (guild_id, channel_id) VALUES (?, ?)",
            (ctx.guild.id, channel.id)
        )
        await self.bot.db.commit()

        embed = discord.Embed(
            description=f"Successfully set {channel.mention} as a honeypot trap channel.",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @honeypot_base.command(name="remove", description="Remove honeypot status from a channel.")
    @app_commands.describe(channel="The honeypot channel to remove")
    @commands.has_permissions(administrator=True)
    async def honeypot_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        await self.bot.db.execute(
            "DELETE FROM honeypots WHERE guild_id = ? AND channel_id = ?",
            (ctx.guild.id, channel.id)
        )
        await self.bot.db.commit()

        embed = discord.Embed(
            description=f"Removed honeypot status from {channel.mention}.",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @honeypot_base.command(name="list", description="List all active server honeypots.")
    @commands.has_permissions(administrator=True)
    async def honeypot_list(self, ctx: commands.Context):
        async with self.bot.db.execute("SELECT channel_id FROM honeypots WHERE guild_id = ?", (ctx.guild.id,)) as c:
            rows = await c.fetchall()

        channels = [f"<#{r[0]}>" for r in rows if ctx.guild.get_channel(r[0])]
        
        embed = discord.Embed(
            title="Active Honeypots",
            description=", ".join(channels) if channels else "No active honeypots configured.",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    # --- Global Message Events Listener ---
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # --- Honeypot Enforcement Check ---
        async with self.bot.db.execute(
            "SELECT 1 FROM honeypots WHERE guild_id = ? AND channel_id = ?", 
            (message.guild.id, message.channel.id)
        ) as c:
            is_honeypot = await c.fetchone()

        if is_honeypot:
            # Skip checking administrators or higher roles so staff don't accidentally get banned
            if message.author.guild_permissions.administrator or message.author.top_role >= message.guild.me.top_role:
                return

            try:
                # Softban sequence: Ban and delete 1 day of messages, then instantly unban
                await message.guild.ban(message.author, reason="Triggered honeypot trap channel", delete_message_days=1)
                await message.guild.unban(message.author, reason="Honeypot softban complete")

                # Try to log the event into your mod logs table if a channel is configured
                async with self.bot.db.execute("SELECT modlog_id FROM guild_settings WHERE guild_id = ?", (message.guild.id,)) as c:
                    log_row = await c.fetchone()
                
                if log_row and log_row[0]:
                    log_channel = message.guild.get_channel(log_row[0])
                    if log_channel:
                        log_embed = discord.Embed(
                            title="Honeypot Triggered",
                            description=f"**User:** {message.author.mention} ({message.author.id})\n**Channel:** {message.channel.mention}\n**Action:** Softbanned automatically.",
                            color=DARK_COLOR
                        )
                        await log_channel.send(embed=log_embed)
            except discord.Forbidden:
                pass
            return

async def setup(bot):
    await bot.add_cog(Features(bot))
