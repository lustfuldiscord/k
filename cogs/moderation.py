import discord
from discord.ext import commands
from discord import app_commands
import datetime

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_flags(self, argument_list):
        """Parse raw arguments to extract flags like --do."""
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

    @commands.hybrid_command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    @app_commands.describe(amount="The number of messages to delete")
    async def m_purge(self, ctx: commands.Context, amount: int):
        """Delete messages from the current channel."""
        if amount <= 0:
            return await ctx.send(embed=discord.Embed(description="❌ Please specify an amount greater than 0.", color=DARK_COLOR))
            
        amount = min(amount, 100)
        
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        try:
            purge_limit = amount if ctx.interaction else amount + 1
            deleted = await ctx.channel.purge(limit=purge_limit, bulk=True)
            actual_deleted = len(deleted) if ctx.interaction else len(deleted) - 1
            
            success_embed = discord.Embed(
                description=f"🧹 Successfully deleted `{actual_deleted}` messages.", 
                color=DARK_COLOR
            )
            await ctx.send(embed=success_embed, delete_after=3)
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(description="❌ I don't have permission to manage messages here.", color=DARK_COLOR))
        except discord.HTTPException as e:
            await ctx.send(embed=discord.Embed(description=f"❌ Failed to purge messages: `{e}`", color=DARK_COLOR))

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The member to ban", args="Reason for the ban (supports --do flag)")
    async def m_ban(self, ctx, member: discord.Member, *, args: str = ""):
        """Ban a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="❌ You cannot moderate a member with an equal or higher role.", color=DARK_COLOR))

        flags, reason = self.parse_flags(args.split())
        reason = reason or "No reason provided."
        
        await member.ban(reason=reason)
        
        embed = discord.Embed(title="Member Banned", color=DARK_COLOR)
        embed.add_field(name="User", value=f"{member.name} ({member.id})", inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        if flags["do"]:
            embed.add_field(name="Follow-up Action", value=flags['do'], inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="kick")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    async def m_kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided."):
        """Kick a member from the server."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="❌ You cannot moderate a member with an equal or higher role.", color=DARK_COLOR))

        await member.kick(reason=reason)
        await ctx.send(embed=discord.Embed(description=f"✅ Kicked {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="mute")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to mute", reason="Reason for the mute")
    async def m_mute(self, ctx, member: discord.Member, *, reason: str = "None"):
        """Mute a member in the server."""
        await ctx.send(embed=discord.Embed(description=f"✅ Muted {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    @app_commands.describe(member="The member to unmute")
    async def m_unmute(self, ctx, member: discord.Member):
        """Unmute a member in the server."""
        await ctx.send(embed=discord.Embed(description=f"✅ Unmuted {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="The member to timeout", minutes="Duration in minutes", reason="Reason for the timeout")
    async def m_timeout(self, ctx, member: discord.Member, minutes: int, *, reason: str = "None"):
        """Timeout a member in the server."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="❌ You cannot moderate a member with an equal or higher role.", color=DARK_COLOR))

        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(embed=discord.Embed(description=f"✅ Timed out {member.mention} for {minutes} minutes.", color=DARK_COLOR))

    @commands.hybrid_command(name="untimeout")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="The member to remove the timeout from")
    async def m_untimeout(self, ctx, member: discord.Member):
        """Remove a timeout from a member."""
        await member.timeout(None)
        await ctx.send(embed=discord.Embed(description=f"✅ Removed timeout from {member.mention}.", color=DARK_COLOR))

    @commands.hybrid_group(name="jail", invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="The member to jail", reason="Reason for jailing")
    async def m_jail(self, ctx, member: discord.Member, *, reason: str = "None"):
        """Send a member to the jail channel."""
        await ctx.send(embed=discord.Embed(description=f"✅ Sent {member.mention} to jail.", color=DARK_COLOR))

    @commands.hybrid_command(name="warn")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    async def m_warn(self, ctx, member: discord.Member, *, reason: str):
        """Issue a warning to a member."""
        await ctx.send(embed=discord.Embed(description=f"✅ Warned {member.mention} for: {reason}.", color=DARK_COLOR))

    @commands.hybrid_command(name="softban")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="The member to softban", reason="Reason for the softban")
    async def m_softban(self, ctx, member: discord.Member, *, reason: str = "None"):
        """Ban and instantly unban a member to clear their recent messages."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send(embed=discord.Embed(description="❌ You cannot moderate a member with an equal or higher role.", color=DARK_COLOR))

        await member.ban(reason=f"Softban: {reason}", delete_message_days=7)
        await ctx.guild.unban(member)
        await ctx.send(embed=discord.Embed(description=f"✅ Softbanned {member.mention} and cleared their messages.", color=DARK_COLOR))

    # --- Informational Queries ---

    @commands.hybrid_command(name="userinfo", aliases=["ui", "whois"])
    @app_commands.describe(member="The member to look up")
    async def m_userinfo(self, ctx, member: discord.Member = None):
        """Display information about a member."""
        member = member or ctx.author
        embed = discord.Embed(title=f"User Info - {member.name}", color=DARK_COLOR)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d") if member.joined_at else "Unknown", inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", aliases=["si"])
    async def m_serverinfo(self, ctx):
        """Display information about the server."""
        g = ctx.guild
        embed = discord.Embed(title=f"Server Info - {g.name}", color=DARK_COLOR)
        embed.add_field(name="Server ID", value=str(g.id), inline=True)
        embed.add_field(name="Member Count", value=str(g.member_count), inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="avatar", aliases=["av"])
    @app_commands.describe(member="The member whose avatar you want to view")
    async def m_avatar(self, ctx, member: discord.Member = None):
        """Display a member's avatar."""
        member = member or ctx.author
        embed = discord.Embed(title=f"Avatar - {member.name}", color=DARK_COLOR)
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    # --- System Category Placeholders ---

    @commands.hybrid_group(name="music", invoke_without_command=True)
    async def music_placeholder(self, ctx):
        """Music system commands placeholder."""
        await ctx.send(embed=discord.Embed(description="Music system placeholder active.", color=DARK_COLOR))

    @commands.hybrid_group(name="levels", invoke_without_command=True)
    async def levels_placeholder(self, ctx):
        """Leveling system commands placeholder."""
        await ctx.send(embed=discord.Embed(description="Leveling system placeholder active.", color=DARK_COLOR))

    @commands.hybrid_group(name="giveaways", invoke_without_command=True)
    async def giveaways_placeholder(self, ctx):
        """Giveaway system commands placeholder."""
        await ctx.send(embed=discord.Embed(description="Giveaway system placeholder active.", color=DARK_COLOR))

async def setup(bot):
    await bot.add_cog(Moderation(bot))
