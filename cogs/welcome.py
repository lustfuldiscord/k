import discord
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_welcome_channel(self, guild: discord.Guild):
        """Queries database configurations tracking to map routing targets."""
        async with self.bot.db.execute(
            "SELECT welcome_channel_id FROM guild_settings WHERE guild_id = ?", 
            (guild.id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return guild.get_channel(row[0])
        return None

    @commands.hybrid_command(name="welcomeset", description="Set or reset the channel where welcome messages are sent.")
    @commands.has_permissions(administrator=True)
    @discord.app_commands.describe(channel="The channel destination or leave blank to disable")
    async def welcome_set(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Configures or clears the targeted channel registry entry for welcome broadcasts."""
        if channel is None:
            await ctx.bot.db.execute(
                "INSERT INTO guild_settings (guild_id, welcome_channel_id) VALUES (?, NULL) "
                "ON CONFLICT(guild_id) DO UPDATE SET welcome_channel_id = NULL",
                (ctx.guild.id,)
            )
            await ctx.bot.db.commit()
            return await ctx.send("Welcome messages have been disabled.")

        await ctx.bot.db.execute(
            "INSERT INTO guild_settings (guild_id, welcome_channel_id) VALUES (?, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET welcome_channel_id = ?",
            (ctx.guild.id, channel.id, channel.id)
        )
        await ctx.bot.db.commit()
        await ctx.send(f"Welcome messages channel routing target updated to {channel.mention}.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        welcome_channel = await self.get_welcome_channel(guild)
        
        if not welcome_channel:
            welcome_channel = guild.system_channel
            if not welcome_channel:
                welcome_channel = next((ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages), None)
            
        if welcome_channel and welcome_channel.permissions_for(guild.me).send_messages:
            member_count = guild.member_count
            await welcome_channel.send(f"Welcome {member.mention} you are the {member_count} member")

    @commands.hybrid_command(name="testwelcome", description="Test the welcome message structure for yourself.")
    async def test_welcome(self, ctx: commands.Context):
        """Triggers a simulated welcome broadcast sequence for testing."""
        guild = ctx.guild
        welcome_channel = await self.get_welcome_channel(guild) or ctx.channel
        
        member_count = guild.member_count
        await welcome_channel.send(f"Welcome {ctx.author.mention} you are the {member_count} member")
        if welcome_channel != ctx.channel:
            await ctx.send(f"Test message sent to {welcome_channel.mention}.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))