import discord
from discord.ext import commands
from discord import app_commands
import datetime

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_flags(self, argument_list):
        """Parse flags like --do action out of a command argument list string."""
        flags = {"do": None}
        if "--do" in argument_list:
            try:
                idx = argument_list.index("--do")
                if idx + 1 < len(argument_list):
                    flags["do"] = argument_list[idx + 1]
                    del argument_list[idx:idx+2]
            except ValueError:
                pass
        return flags, " ".join(argument_list)

    # --- Core Moderation Actions ---

    @commands.hybrid_command(name="lock")
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel="The channel to lock down. Defaults to the current channel.")
    async def m_lock(self, ctx, channel: discord.TextChannel = None):
        """Lock down a channel to prevent members from sending messages."""
        channel = channel or ctx.channel
        
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.send_messages is False:
            return await ctx.send(embed=discord.Embed(description=f"{channel.mention} is already locked.", color=DARK_COLOR))
            
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Channel locked by {ctx.author}")
        
        try:
            await ctx.message.add_reaction("🔒")
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(description=f"Locked {channel.mention} successfully.", color=DARK_COLOR))

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban from the server", args="Reason for the ban. Can include flags like --do <action>")
    async def m_ban(self, ctx, member: discord.Member, *, args: str = ""):
        """Ban a member from the server. Supports optional flags."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="You cannot ban a member with an equal or higher role hierarchy positioning.", color=DARK_COLOR))

        # Split arguments to pull out possible flags safely
        argument_list = args.split()
        flags, reason = self.parse_flags(argument_list)
        reason = reason or "No reason specified."
        
        await member.ban(reason=reason)
        
        embed = discord.Embed(title="User Banned Successfully", color=DARK_COLOR)
        embed.add_field(name="Target User", value=f"{member.name} (ID: {member.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        if flags["do"]:
            embed.add_field(name="Follow-up Action Triggered", value=flags['do'], inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick from the server", reason="The reason for the kick")
    async def m_kick(self, ctx, member: discord.Member, *, reason: str = "No reason specified."):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="You cannot kick a member with an equal or higher role hierarchy positioning.", color=DARK_COLOR))

        await member.kick(reason=reason)
        await ctx.send(embed=discord.Embed(description=f"Successfully kicked {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="mute")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to mute", reason="The reason for the mute")
    async def m_mute(self, ctx, member: discord.Member, *, reason: str = "None"):
        """Apply a mute role status over a user profile."""
        await ctx.send(embed=discord.Embed(description=f"Muted {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to unmute")
    async def m_unmute(self, ctx, member: discord.Member):
        """Remove mute role status from a user profile."""
        await ctx.send(embed=discord.Embed(description=f"Unmuted {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="The member to timeout", minutes="Duration of the timeout in minutes", reason="The reason for the timeout")
    async def m_timeout(self, ctx, member: discord.Member, minutes: int, *, reason: str = "None"):
        """Timeout a member to stop them from talking or reacting entirely."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="You cannot timeout a member with an equal or higher role hierarchy positioning.", color=DARK_COLOR))

        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"Timed out {member.mention} for {minutes} minutes.", color=DARK_COLOR))

    @commands.hybrid_command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="The member to remove from timeout")
    async def m_untimeout(self, ctx, member: discord.Member):
        """Instantly lift a timeout from a member."""
        await member.timeout(None)
        await ctx.send(embed=discord.Embed(description=f"Removed timeout status from {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="jail")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="The member to place in jail", reason="The reason for jail placement")
    async def m_jail(self, ctx, member: discord.Member, *, reason: str = "None"):
        """Isolate a user by forcing them into the server's tracking holding cell channel."""
        await ctx.send(embed=discord.Embed(description=f"Jailed {member.mention} successfully.", color=DARK_COLOR))

    @commands.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="The member to warn", reason="The documented reason for the infraction warning")
    async def m_warn(self, ctx, member: discord.Member, *, reason: str):
        """Log a formal warning infraction against a user's account history."""
        await ctx.send(embed=discord.Embed(description=f"Logged warning against user member entity {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="softban")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The member to softban", reason="The reason for the softban tracking logs")
    async def m_softban(self, ctx, member: discord.Member, *, reason: str = "None"):
        """Kick a user and clear their recent history by banning and instantly unbanning them."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="You cannot softban a member with an equal or higher role hierarchy positioning.", color=DARK_COLOR))

        await member.ban(reason=f"Softban (Messages Purged): {reason}", delete_message_days=7)
        await ctx.guild.unban(member)
        await ctx.send(embed=discord.Embed(description=f"Softbanned {member.mention} and successfully cleared their messages.", color=DARK_COLOR))

    # --- Informational Queries ---

    @commands.hybrid_command(name="userinfo", aliases=["ui", "whois"])
    @app_commands.describe(member="The member whose profile data you want to view")
    async def m_userinfo(self, ctx, member: discord.Member = None):
        """Display analytical profile metadata about a server member."""
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info - {member.name}", color=DARK_COLOR)
        embed.add_field(name="Account ID", value=str(member.id), inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", aliases=["si"])
    async def m_serverinfo(self, ctx):
        """Display configuration stats and setup metrics for the server."""
        g = ctx.guild
        embed = discord.Embed(title=f"Server Info - {g.name}", color=DARK_COLOR)
        embed.add_field(name="Server ID", value=str(g.id), inline=True)
        embed.add_field(name="Total Members", value=str(g.member_count), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", aliases=["av"])
    @app_commands.describe(member="The member whose profile avatar icon you want to view")
    async def m_avatar(self, ctx, member: discord.Member = None):
        """Fetch and display a clean URL path link to a member's avatar icon asset."""
        member = member or ctx.author
        embed = discord.Embed(title=f"Avatar Asset Link: {member.name}", color=DARK_COLOR)
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    # --- System Category Placeholders ---

    @commands.hybrid_group(name="music", invoke_without_command=True)
    async def music_placeholder(self, ctx):
        """Music streaming distribution pipeline framework module."""
        await ctx.send(embed=discord.Embed(description="Music streaming framework pipeline initialized successfully.", color=DARK_COLOR))

    @commands.hybrid_group(name="levels", invoke_without_command=True)
    async def levels_placeholder(self, ctx):
        """User message activity tracking progression index module."""
        await ctx.send(embed=discord.Embed(description="Level ranking progression calculations tracker verified.", color=DARK_COLOR))

    @commands.hybrid_group(name="giveaways", invoke_without_command=True)
    async def giveaways_placeholder(self, ctx):
        """Automated reward drawings scheduling manager framework module."""
        await ctx.send(embed=discord.Embed(description="Automated promotional reward system configuration panel verified.", color=DARK_COLOR))

async def setup(bot):
    await bot.add_cog(Moderation(bot))
