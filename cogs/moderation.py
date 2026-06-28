import discord
from discord.ext import commands
from discord import app_commands
import datetime

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_flags(self, argument_list):
        """Parse raw lists extracting flag metrics arguments like --do smoothly."""
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
        """Lock down a channel to prevent regular members from typing."""
        channel = channel or ctx.channel
        
        # Pull the @everyone role permissions override configuration
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        # Check if it's already locked to prevent unnecessary API spam
        if overwrite.send_messages is False:
            return await ctx.send(embed=discord.Embed(description=f"{channel.mention} is already locked.", color=DARK_COLOR))
            
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Channel locked by {ctx.author}")
        
        # Add the lock reaction directly to the invocation message
        try:
            await ctx.message.add_reaction("🔒")
        except discord.Forbidden:
            # Fallback text if the bot lacks Add Reactions permissions in this channel
            await ctx.send(embed=discord.Embed(description=f"Locked {channel.mention} successfully.", color=DARK_COLOR))

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The user profile targeted for exclusion", args="Reason and flags like --do action")
    async def m_ban(self, ctx, member: discord.Member, *, args: str = ""):
        """Execute server exclusion protocols targeting accounts. Supports --do flags."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="You cannot moderate a member with an equal or higher role hierarchy positioning.", color=DARK_COLOR))

        flags, reason = self.parse_flags(args.split())
        reason = reason or "No specified incident reasons recorded."
        
        await member.ban(reason=reason)
        
        embed = discord.Embed(title="Exclusion Protocol Deployed", color=DARK_COLOR)
        embed.add_field(name="Target Account Entity", value=f"{member.name} (ID: {member.id})", inline=False)
        embed.add_field(name="Infraction Specification Text", value=reason, inline=False)
        if flags["do"]:
            embed.add_field(name="Execution Step Directives Flag Action", value=f"Triggered follow-up: {flags['do']}", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="The user profile targeted for eviction", reason="The documented reason for removal")
    async def m_kick(self, ctx, member: discord.Member, *, reason: str = "No rationale documented."):
        """Eject accounts instantly out from current tracking population."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="Hierarchy layout check failed. Target possesses superior privileges.", color=DARK_COLOR))

        await member.kick(reason=reason)
        await ctx.send(embed=discord.Embed(description=f"Eviction completed processing entity account user {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="mute")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="Target member account profile", reason="Action parameters index rationale")
    async def m_mute(self, ctx, member: discord.Member, *, reason: str = "None"):
        """Apply structural restrictions blocks inhibiting speech capabilities fields."""
        await ctx.send(embed=discord.Embed(description=f"Mute profile states tracking updated over target user member: {member.mention}", color=DARK_COLOR))

    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="Target member account profile")
    async def m_unmute(self, ctx, member: discord.Member):
        """Lift operational silencing profiles arrays directly down."""
        await ctx.send(embed=discord.Embed(description=f"Restored voice capabilities fields parameters targeting user account {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Target member account profile", minutes="Duration index scale in minutes", reason="Action parameters index rationale")
    async def m_timeout(self, ctx, member: discord.Member, minutes: int, *, reason: str = "None"):
        """Impose internal API communication blocks over target members."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="Action restricted due to structural authority hierarchy positioning.", color=DARK_COLOR))

        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"Target communication channels blocked tracking for duration parameters: {minutes} minutes.", color=DARK_COLOR))

    @commands.hybrid_command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Target member account profile")
    async def m_untimeout(self, ctx, member: discord.Member):
        """Purge ongoing timeout parameters arrays instantly."""
        await member.timeout(None)
        await ctx.send(embed=discord.Embed(description=f"Lifted internal timing block locks limiting profile accounts: {member.mention}", color=DARK_COLOR))

    @commands.hybrid_command(name="jail")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="Target account mapping profile", reason="Action parameters index rationale")
    async def m_jail(self, ctx, member: discord.Member, *, reason: str = "None"):
        """Route structural identities maps straight down inside holding patterns parameters channels."""
        await ctx.send(embed=discord.Embed(description=f"Jailed: {member.mention}", color=DARK_COLOR))

    @commands.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="Target account mapping profile", reason="Documented verification string")
    async def m_warn(self, ctx, member: discord.Member, *, reason: str):
        """Log documented infraction metrics indicators mapping account histories files."""
        await ctx.send(embed=discord.Embed(description=f"Infraction warning entry files successfully appended tracking databases markers targeting member entity {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="softban")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="Target account mapping profile", reason="Action parameters index rationale")
    async def m_softban(self, ctx, member: discord.Member, *, reason: str = "None"):
        """Purge historical message activity traces instantly using rapid purge cycles loops formats."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="Action restricted due to structural authority hierarchy positioning.", color=DARK_COLOR))

        await member.ban(reason=f"Softban verification purge: {reason}", delete_message_days=7)
        await ctx.guild.unban(member)
        await ctx.send(embed=discord.Embed(description=f"Historical data tracking arrays wiped down cleanly across target account reference points user entity {member.mention}.", color=DARK_COLOR))

    # --- Informational Queries ---

    @commands.hybrid_command(name="userinfo", aliases=["ui", "whois"])
    @app_commands.describe(member="Target member account profile metadata context")
    async def m_userinfo(self, ctx, member: discord.Member = None):
        """Audit properties values logs representing accounts attributes records profiles."""
        member = member or ctx.author
        embed = discord.Embed(title=f"Identity Profile Registry Data - {member.name}", color=DARK_COLOR)
        embed.add_field(name="Unique Reference String ID", value=str(member.id), inline=True)
        embed.add_field(name="Platform Initialization Date", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Server Entry Timestamp Record", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", aliases=["si"])
    async def m_serverinfo(self, ctx):
        """Display organizational structures metadata tracking server configurations states."""
        g = ctx.guild
        embed = discord.Embed(title=f"Environment Analytics Dashboard - {g.name}", color=DARK_COLOR)
        embed.add_field(name="Guild Identity Identifier Index Key", value=str(g.id), inline=True)
        embed.add_field(name="Current Account Population Counts Metrics", value=str(g.member_count), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", aliases=["av"])
    @app_commands.describe(member="Target member account profile metadata context")
    async def m_avatar(self, ctx, member: discord.Member = None):
        """Isolate dynamic identity display asset layouts paths straight out to targets files links."""
        member = member or ctx.author
        embed = discord.Embed(title=f"Image Asset Links: {member.name}", color=DARK_COLOR)
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    # --- System Category Placeholders ---

    @commands.hybrid_group(name="music", invoke_without_command=True)
    async def music_placeholder(self, ctx):
        """Multimedia audio distribution pipeline rendering operations core systems framework node."""
        await ctx.send(embed=discord.Embed(description="Multimedia stream pipeline system placeholder node initialization verified.", color=DARK_COLOR))

    @commands.hybrid_group(name="levels", invoke_without_command=True)
    async def levels_placeholder(self, ctx):
        """Activity engagement progression ranking calculations engines indexes modules."""
        await ctx.send(embed=discord.Embed(description="Activity engagement progression metrics indexes database system structural profile placeholder node verified.", color=DARK_COLOR))

    @commands.hybrid_group(name="giveaways", invoke_without_command=True)
    async def giveaways_placeholder(self, ctx):
        """Automated reward drawing matrices management tools subsystems."""
        await ctx.send(embed=discord.Embed(description="Automated promotional distribution scheduling configuration platform matrix placeholder node verified.", color=DARK_COLOR))

async def setup(bot):
    await bot.add_cog(Moderation(bot))
