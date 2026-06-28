import discord
from discord.ext import commands
from discord import app_commands
from collections import deque
import datetime

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Maps channel_id to a deque storing the last 5 deleted messages
        self.snipe_storage = {}

    # --- Snipe Subsystem ---
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        channel_id = message.channel.id
        if channel_id not in self.snipe_storage:
            self.snipe_storage[channel_id] = deque(maxlen=5)

        self.snipe_storage[channel_id].appendleft({
            "author": message.author,
            "content": message.content,
            "attachments": [a.url for a in message.attachments],
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
        })

    @commands.hybrid_command(name="snipe", description="Snipe recently deleted messages from this channel.")
    @app_commands.describe(index="How many messages back to look (1-5)")
    async def snipe(self, ctx: commands.Context, index: int = 1):
        channel_id = ctx.channel.id
        
        if channel_id not in self.snipe_storage or not self.snipe_storage[channel_id]:
            return await ctx.send(embed=discord.Embed(description="There are no deleted messages to snipe in this channel.", color=DARK_COLOR))

        history = self.snipe_storage[channel_id]
        max_available = len(history)

        if index < 1 or index > max_available:
            return await ctx.send(embed=discord.Embed(
                description=f"Invalid index. You can only look back between `1` and `{max_available}` deleted messages for this channel.", 
                color=DARK_COLOR
            ))

        target_msg = history[index - 1]

        author = target_msg["author"]
        content = target_msg["content"] or "*Message contained no text content (Image/Embed/File)*"
        attachments = target_msg["attachments"]
        timestamp = target_msg["timestamp"]

        embed = discord.Embed(
            description=content, 
            color=DARK_COLOR, 
            timestamp=timestamp
        )
        embed.set_author(name=f"{author.name} ({author.id})", icon_url=author.display_avatar.url)
        embed.set_footer(text=f"Snipe Index: {index}/{max_available}")

        if attachments:
            embed.set_image(url=attachments[0])

        await ctx.send(embed=embed)

    # --- Role Creation Utility ---
    @commands.hybrid_command(name="role", description="Create a new server role with a specified color.")
    @app_commands.describe(name="The name of the new role", color="The hex color code (e.g. #ff0000)")
    @commands.has_permissions(manage_roles=True)
    async def create_role(self, ctx: commands.Context, name: str, color: str = "#000000"):
        if not color.startswith("#"):
            color = f"#{color}"
            
        try:
            hex_int = int(color.lstrip("#"), 16)
            discord_color = discord.Color(hex_int)
        except ValueError:
            return await ctx.send(embed=discord.Embed(description="Invalid hex color format. Use formats like `#ff0000` or `ff0000`.", color=DARK_COLOR))

        try:
            new_role = await ctx.guild.create_role(
                name=name,
                color=discord_color,
                reason=f"Role created by {ctx.author}"
            )
            
            embed = discord.Embed(
                description=f"Successfully created the role {new_role.mention} with color `{color}`.",
                color=DARK_COLOR
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send(embed=discord.Embed(description="I do not have permissions to manage roles in this server.", color=DARK_COLOR))

    # --- Alias Subsystem ---
    @commands.hybrid_group(name="alias", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def alias_base(self, ctx):
        """Manage custom command shortcuts."""
        embed = discord.Embed(
            title="Alias Subcommands",
            description="Available options: add, remove, removeall, list, reset, view",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @alias_base.command(name="add")
    @app_commands.describe(shortcut="The shortcut name", command="The command it triggers")
    async def a_add(self, ctx, shortcut: str, *, command: str):
        """Map a shortcut string to an existing command."""
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO aliases (guild_id, shortcut, command) VALUES (?, ?, ?)",
            (ctx.guild.id, shortcut.lower(), command.lower())
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Mapped alias `{shortcut}` to `{command}`", color=DARK_COLOR))

    @alias_base.command(name="remove")
    @app_commands.describe(shortcut="The shortcut to remove")
    async def a_remove(self, ctx, shortcut: str):
        """Remove a specific shortcut mapping."""
        await self.bot.db.execute("DELETE FROM aliases WHERE guild_id = ? AND shortcut = ?", (ctx.guild.id, shortcut.lower()))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Removed alias `{shortcut}`", color=DARK_COLOR))

    @alias_base.command(name="removeall")
    @app_commands.describe(command="The target command to clear all aliases from")
    async def a_removeall(self, ctx, *, command: str):
        """Remove all shortcut mappings bound to a command."""
        await self.bot.db.execute("DELETE FROM aliases WHERE guild_id = ? AND command = ?", (ctx.guild.id, command.lower()))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Cleared all aliases for `{command}`", color=DARK_COLOR))

    @alias_base.command(name="list")
    async def a_list(self, ctx):
        """List all active server aliases."""
        async with self.bot.db.execute("SELECT shortcut, command FROM aliases WHERE guild_id = ?", (ctx.guild.id,)) as c:
            rows = await c.fetchall()
        lines = [f"`{r[0]}` -> `{r[1]}`" for r in rows]
        embed = discord.Embed(title="Server Aliases", description="\n".join(lines) if lines else "No aliases configured.", color=DARK_COLOR)
        await ctx.send(embed=embed)

    @alias_base.command(name="reset")
    async def a_reset(self, alias_ctx):
        """Reset all custom command shortcuts."""
        await self.bot.db.execute("DELETE FROM aliases WHERE guild_id = ?", (alias_ctx.guild.id,))
        await self.bot.db.commit()
        await alias_ctx.send(embed=discord.Embed(description="Reset all server aliases.", color=DARK_COLOR))

    @alias_base.command(name="view")
    @app_commands.describe(shortcut="The shortcut to inspect")
    async def a_view(self, ctx, shortcut: str):
        """View the target command of an alias."""
        async with self.bot.db.execute("SELECT command FROM aliases WHERE guild_id = ? AND shortcut = ?", (ctx.guild.id, shortcut.lower())) as c:
            row = await c.fetchone()
        if row:
            return await ctx.send(embed=discord.Embed(description=f"`{shortcut}` maps to `{row[0]}`", color=DARK_COLOR))
        await ctx.send(embed=discord.Embed(description="Alias not found.", color=DARK_COLOR))

    # --- ImgOnly Subsystem ---
    @commands.hybrid_group(name="imgonly", invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def imgonly_base(self, ctx):
        """Manage image-only channel restrictions."""
        embed = discord.Embed(
            title="Imgonly Subcommands",
            description="Available options: add, remove, list",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @imgonly_base.command(name="add")
    @app_commands.describe(channel="The text channel to restrict")
    async def img_add(self, ctx, channel: discord.TextChannel):
        """Restrict a channel to media attachments only."""
        await self.bot.db.execute("INSERT OR IGNORE INTO imgonly_channels (guild_id, channel_id) VALUES (?, ?)", (ctx.guild.id, channel.id))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Set {channel.mention} to image-only mode.", color=DARK_COLOR))

    @imgonly_base.command(name="remove")
    @app_commands.describe(channel="The restricted channel")
    async def img_remove(self, ctx, channel: discord.TextChannel):
        """Remove media restrictions from a channel."""
        await self.bot.db.execute("DELETE FROM imgonly_channels WHERE guild_id = ? AND channel_id = ?", (ctx.guild.id, channel.id))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Removed image-only mode from {channel.mention}.", color=DARK_COLOR))

    @imgonly_base.command(name="list")
    async def img_list(self, ctx):
        """List all image-only channels."""
        async with self.bot.db.execute("SELECT channel_id FROM imgonly_channels WHERE guild_id = ?", (ctx.guild.id,)) as c:
            rows = await c.fetchall()
        ch_list = [f"<#{r[0]}>" for r in rows if ctx.guild.get_channel(r[0])]
        embed = discord.Embed(title="Image Only Channels", description=", ".join(ch_list) if ch_list else "No restricted channels.", color=DARK_COLOR)
        await ctx.send(embed=embed)

    # --- Invoke Subsystem ---
    @commands.hybrid_group(name="invoke", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def invoke_base(self, ctx):
        """Manage custom direct messages or announcements for moderation actions."""
        embed = discord.Embed(
            title="Invoke Subcommands",
            description="Available categories: ban, tempban, unban, jail, unjail, mute, runmute",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @invoke_base.group(name="ban")
    async def inv_ban(self, ctx):
        """Configure messages for the ban action."""
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(description="Available options: dm, message, view", color=DARK_COLOR))
    @inv_ban.command(name="dm")
    async def inv_ban_dm(self, ctx, *, message: str):
        """Set the DM notification sent to a banned user."""
        await ctx.send(embed=discord.Embed(description="Saved custom ban DM template.", color=DARK_COLOR))
    @inv_ban.command(name="message")
    async def inv_ban_msg(self, ctx, *, message: str):
        """Set the channel message sent during a ban action."""
        await ctx.send(embed=discord.Embed(description="Saved custom ban broadcast template.", color=DARK_COLOR))
    @inv_ban.command(name="view")
    async def inv_ban_view(self, ctx):
        """View configured templates for bans."""
        await ctx.send(embed=discord.Embed(description="Displaying active ban template layouts.", color=DARK_COLOR))

    @invoke_base.group(name="tempban")
    async def inv_tb(self, ctx):
        """Configure messages for the tempban action."""
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(description="Available options: dm, message, view", color=DARK_COLOR))
    @inv_tb.command(name="dm")
    async def inv_tb_dm(self, ctx, *, message: str):
        """Set the DM notification sent to a tempbanned user."""
        await ctx.send(embed=discord.Embed(description="Saved custom tempban DM template.", color=DARK_COLOR))
    @inv_tb.command(name="message")
    async def inv_tb_msg(self, ctx, *, message: str):
        """Set the channel message sent during a tempban action."""
        await ctx.send(embed=discord.Embed(description="Saved custom tempban broadcast template.", color=DARK_COLOR))
    @inv_tb.command(name="view")
    async def inv_tb_view(self, ctx):
        """View configured templates for tempbans."""
        await ctx.send(embed=discord.Embed(description="Displaying active tempban template layouts.", color=DARK_COLOR))

    @invoke_base.group(name="unban")
    async def inv_ub(self, ctx):
        """Configure messages for the unban action."""
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(description="Available options: dm, message, view", color=DARK_COLOR))
    @inv_ub.command(name="dm")
    async def inv_ub_dm(self, ctx, *, message: str):
        """Set the DM notification sent to an unbanned user."""
        await ctx.send(embed=discord.Embed(description="Saved custom unban DM template.", color=DARK_COLOR))
    @inv_ub.command(name="message")
    async def inv_ub_msg(self, ctx, *, message: str):
        """Set the channel message sent during an unban action."""
        await ctx.send(embed=discord.Embed(description="Saved custom unban broadcast template.", color=DARK_COLOR))
    @inv_ub.command(name="view")
    async def inv_ub_view(self, ctx):
        """View configured templates for unbans."""
        await ctx.send(embed=discord.Embed(description="Displaying active unban template layouts.", color=DARK_COLOR))

    @invoke_base.group(name="jail")
    async def inv_jl(self, ctx):
        """Configure messages for the jail action."""
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(description="Available options: dm, message, view", color=DARK_COLOR))
    @inv_jl.command(name="dm")
    async def inv_jl_dm(self, ctx, *, message: str):
        """Set the DM notification sent to a jailed user."""
        await ctx.send(embed=discord.Embed(description="Saved custom jail DM template.", color=DARK_COLOR))
    @inv_jl.command(name="message")
    async def inv_jl_msg(self, ctx, *, message: str):
        """Set the channel message sent during a jail action."""
        await ctx.send(embed=discord.Embed(description="Saved custom jail broadcast template.", color=DARK_COLOR))
    @inv_jl.command(name="view")
    async def inv_jl_view(self, ctx):
        """View configured templates for jail."""
        await ctx.send(embed=discord.Embed(description="Displaying active jail template layouts.", color=DARK_COLOR))

    @invoke_base.group(name="unjail")
    async def inv_uj(self, ctx):
        """Configure messages for the unjail action."""
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(description="Available options: dm, message, view", color=DARK_COLOR))
    @inv_uj.command(name="dm")
    async def inv_uj_dm(self, ctx, *, message: str):
        """Set the DM notification sent to an unjailed user."""
        await ctx.send(embed=discord.Embed(description="Saved custom unjail DM template.", color=DARK_COLOR))
    @inv_uj.command(name="message")
    async def inv_uj_msg(self, ctx, *, message: str):
        """Set the channel message sent during an unjail action."""
        await ctx.send(embed=discord.Embed(description="Saved custom unjail broadcast template.", color=DARK_COLOR))
    @inv_uj.command(name="view")
    async def inv_uj_view(self, ctx):
        """View configured templates for unjail."""
        await ctx.send(embed=discord.Embed(description="Displaying active unjail template layouts.", color=DARK_COLOR))

    @invoke_base.group(name="mute")
    async def inv_mt(self, ctx):
        """Configure messages for the mute action."""
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(description="Available options: dm, message, view", color=DARK_COLOR))
    @inv_mt.command(name="dm")
    async def inv_mt_dm(self, ctx, *, message: str):
        """Set the DM notification sent to a muted user."""
        await ctx.send(embed=discord.Embed(description="Saved custom mute DM template.", color=DARK_COLOR))
    @inv_mt.command(name="message")
    async def inv_mt_msg(self, ctx, *, message: str):
        """Set the channel message sent during a mute action."""
        await ctx.send(embed=discord.Embed(description="Saved custom mute broadcast template.", color=DARK_COLOR))
    @inv_mt.command(name="view")
    async def inv_mt_view(self, ctx):
        """View configured templates for mutes."""
        await ctx.send(embed=discord.Embed(description="Displaying active mute template layouts.", color=DARK_COLOR))

    @invoke_base.group(name="runmute")
    async def inv_rm(self, ctx):
        """Configure messages for the role unmute action."""
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(description="Available options: dm, message, view", color=DARK_COLOR))
    @inv_rm.command(name="dm")
    async def inv_rm_dm(self, ctx, *, message: str):
        """Set the DM notification sent during a role unmute action."""
        await ctx.send(embed=discord.Embed(description="Saved custom role unmute DM template.", color=DARK_COLOR))
    @inv_rm.command(name="message")
    async def inv_rm_msg(self, ctx, *, message: str):
        """Set the channel message sent during a role unmute action."""
        await ctx.send(embed=discord.Embed(description="Saved custom role unmute broadcast template.", color=DARK_COLOR))
    @inv_rm.command(name="view")
    async def inv_rm_view(self, ctx):
        """View configured templates for role unmutes."""
        await ctx.send(embed=discord.Embed(description="Displaying active role unmute template layouts.", color=DARK_COLOR))

    # --- Message Interception for Aliases and Restrictions ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        ctx = await self.bot.get_context(message)
        if not ctx.valid:
            pref = await self.bot.get_prefix(message)
            pref = pref[0] if isinstance(pref, list) else pref
            if message.content.startswith(pref):
                parts = message.content[len(pref):].split(" ")
                possible_shortcut = parts[0].lower()
                async with self.bot.db.execute("SELECT command FROM aliases WHERE guild_id = ? AND shortcut = ?", (message.guild.id, possible_shortcut)) as c:
                    row = await c.fetchone()
                if row:
                    remainder = " ".join(parts[1:])
                    message.content = f"{pref}{row[0]} {remainder}".strip()
                    await self.bot.process_commands(message)
                    return

        async with self.bot.db.execute("SELECT 1 FROM imgonly_channels WHERE guild_id = ? AND channel_id = ?", (message.guild.id, message.channel.id)) as c:
            is_restricted = await c.fetchone()
        if is_restricted:
            if not message.attachments and "http" not in message.content:
                try:
                    await message.delete()
                except discord.Forbidden:
                    pass

async def setup(bot):
    await bot.add_cog(Utility(bot))