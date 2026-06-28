import discord
from discord.ext import commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class SystemSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="setup", description="Configure required roles and channels for the server.")
    @commands.has_permissions(administrator=True)
    async def server_setup(self, ctx: commands.Context):
        """Initializes the server with Muted/Jailed roles and isolates permissions server-wide."""
        await ctx.defer()
        
        guild = ctx.guild
        log_messages = []

        # 1. Setup Muted Role
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            try:
                muted_role = await guild.create_role(name="Muted", reason="Katana system setup")
                log_messages.append("Created 'Muted' role.")
            except discord.Forbidden:
                return await ctx.send(embed=discord.Embed(description="I do not have permissions to manage roles.", color=DARK_COLOR))
        else:
            log_messages.append("'Muted' role already exists.")

        # 2. Setup Jailed Role
        jailed_role = discord.utils.get(guild.roles, name="Jailed")
        if not jailed_role:
            jailed_role = await guild.create_role(name="Jailed", reason="Katana system setup")
            log_messages.append("Created 'Jailed' role.")
        else:
            log_messages.append("'Jailed' role already exists.")

        # 3. Setup Jail Text Channel
        jail_channel = discord.utils.get(guild.text_channels, name="jail")
        if not jail_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                jailed_role: discord.PermissionOverwrite(read_messages=True, read_message_history=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }
            jail_channel = await guild.create_text_channel(name="jail", overwrites=overwrites, reason="Katana system setup")
            log_messages.append(f"Created {jail_channel.mention} channel.")
        else:
            log_messages.append(f"{jail_channel.mention} channel already exists.")

        # 4. Global Server Lockdown for Jailed Role
        locked_channels_count = 0
        for channel in guild.channels:
            if channel == jail_channel:
                continue
                
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel)):
                try:
                    await channel.set_permissions(jailed_role, view_channel=False, send_messages=False, connect=False, reason="Katana global isolation setup")
                    locked_channels_count += 1
                except discord.Forbidden:
                    continue

        log_messages.append(f"Isolated the 'Jailed' role across {locked_channels_count} channels.")

        embed = discord.Embed(
            title="System Initialization Complete", 
            description="\n".join([f"• {msg}" for msg in log_messages]), 
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SystemSetup(bot))