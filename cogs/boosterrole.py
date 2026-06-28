import discord
from discord.ext import commands
from discord import app_commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class BoosterRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if not ctx.guild:
            return False
        # Check if user is a booster or has admin privileges
        if ctx.author.premium_since or ctx.author.guild_permissions.administrator:
            return True
        await ctx.send(embed=discord.Embed(description="This command is restricted to server boosters.", color=DARK_COLOR))
        return False

    @commands.hybrid_group(name="boosterrole", aliases=["br"], invoke_without_command=True)
    async def br_base(self, ctx):
        """Manage your custom booster role."""
        embed = discord.Embed(
            title="Booster Role Commands",
            description="Available choices: setup, claim, name, color, icon, delete, list",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @br_base.command(name="setup")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(base_role="The anchor role that custom roles will be placed beneath")
    async def br_setup(self, ctx, base_role: discord.Role):
        """Set up the layout positioning anchor role for custom booster roles."""
        await self.bot.db.execute(
            "INSERT INTO booster_settings (guild_id, base_role_id) VALUES (?, ?) ON CONFLICT(guild_id) DO UPDATE SET base_role_id=excluded.base_role_id",
            (ctx.guild.id, base_role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Booster role anchor tracking set to {base_role.mention}.", color=DARK_COLOR))

    @br_base.command(name="claim")
    @app_commands.describe(name="The name of your new custom role")
    async def br_claim(self, ctx, *, name: str):
        """Claim your personal booster role if you do not already have one."""
        async with self.bot.db.execute("SELECT role_id FROM booster_roles WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id)) as c:
            row = await c.fetchone()
        
        if row:
            return await ctx.send(embed=discord.Embed(description="You already possess a custom booster role mapping.", color=DARK_COLOR))

        async with self.bot.db.execute("SELECT base_role_id FROM booster_settings WHERE guild_id = ?", (ctx.guild.id,)) as c:
            settings = await c.fetchone()

        # Check for word filters
        async with self.bot.db.execute("SELECT word FROM booster_filters WHERE guild_id = ?", (ctx.guild.id,)) as c:
            filters = await c.fetchall()
            
        for filter_word in filters:
            if filter_word[0] in name.lower():
                return await ctx.send(embed=discord.Embed(description="That name contains a restricted text filter.", color=DARK_COLOR))

        # Position logic based on setup configuration
        role_kwargs = {"name": name, "reason": f"Booster role claimed by {ctx.author}"}
        new_role = await ctx.guild.create_role(**role_kwargs)

        if settings and settings[0]:
            anchor_role = ctx.guild.get_role(settings[0])
            if anchor_role:
                try:
                    await new_role.edit(position=anchor_role.position)
                except discord.Forbidden:
                    pass

        await ctx.author.add_roles(new_role)
        
        await self.bot.db.execute(
            "INSERT INTO booster_roles (guild_id, user_id, role_id) VALUES (?, ?, ?)",
            (ctx.guild.id, ctx.author.id, new_role.id)
        )
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Successfully generated your custom role: {new_role.mention}", color=DARK_COLOR))

    @br_base.command(name="name")
    @app_commands.describe(name="The new name for your custom role")
    async def br_name(self, ctx, *, name: str):
        """Update the name string of your custom booster role."""
        async with self.bot.db.execute("SELECT role_id FROM booster_roles WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id)) as c:
            row = await c.fetchone()
        if not row:
            return await ctx.send(embed=discord.Embed(description="No active custom booster role found for your account.", color=DARK_COLOR))

        async with self.bot.db.execute("SELECT word FROM booster_filters WHERE guild_id = ?", (ctx.guild.id,)) as c:
            filters = await c.fetchall()
        for filter_word in filters:
            if filter_word[0] in name.lower():
                return await ctx.send(embed=discord.Embed(description="That name contains a restricted text filter.", color=DARK_COLOR))

        role = ctx.guild.get_role(row[0])
        if role:
            await role.edit(name=name)
            await ctx.send(embed=discord.Embed(description=f"Role updated to `{name}`.", color=DARK_COLOR))
        else:
            await ctx.send(embed=discord.Embed(description="Target role could not be located in server index hierarchy.", color=DARK_COLOR))

    @br_base.command(name="color")
    @app_commands.describe(hex_code="The hex color code (e.g. #ff0000 or ff0000)")
    async def br_color(self, ctx, hex_code: str):
        """Update the color hex format value of your custom booster role."""
        async with self.bot.db.execute("SELECT role_id FROM booster_roles WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id)) as c:
            row = await c.fetchone()
        if not row:
            return await ctx.send(embed=discord.Embed(description="No active custom booster role found for your account.", color=DARK_COLOR))

        hex_code = hex_code.lstrip("#")
        try:
            color_value = int(hex_code, 16)
        except ValueError:
            return await ctx.send(embed=discord.Embed(description="Invalid hex parameters sequence format provided.", color=DARK_COLOR))

        role = ctx.guild.get_role(row[0])
        if role:
            await role.edit(color=discord.Color(color_value))
            await ctx.send(embed=discord.Embed(description=f"Role color shifted to `#{hex_code}`.", color=DARK_COLOR))

    @br_base.command(name="icon")
    @app_commands.describe(emoji="The custom emoji or standard unicode asset profile to bind")
    async def br_icon(self, ctx, emoji: str = None):
        """Modify or clear the custom icon image metric attached to your booster role."""
        async with self.bot.db.execute("SELECT role_id FROM booster_roles WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id)) as c:
            row = await c.fetchone()
        if not row:
            return await ctx.send(embed=discord.Embed(description="No active custom booster role found for your account.", color=DARK_COLOR))

        role = ctx.guild.get_role(row[0])
        if not role:
            return

        if "ROLE_ICONS" not in ctx.guild.features:
            return await ctx.send(embed=discord.Embed(description="This server lacks the required boost level tier requirements to support role icons.", color=DARK_COLOR))

        if not emoji:
            await role.edit(display_icon=None)
            return await ctx.send(embed=discord.Embed(description="Cleared custom display icon graphic specifications.", color=DARK_COLOR))

        # Dynamic parameter processing evaluation check
        try:
            await role.edit(display_icon=emoji)
            await ctx.send(embed=discord.Embed(description="Booster role display icon configuration updated.", color=DARK_COLOR))
        except discord.HTTPException:
            await ctx.send(embed=discord.Embed(description="Unable to apply specified display icon parameter.", color=DARK_COLOR))

    @br_base.command(name="delete")
    async def br_delete(self, ctx):
        """Permanently remove your custom booster role."""
        async with self.bot.db.execute("SELECT role_id FROM booster_roles WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id)) as c:
            row = await c.fetchone()
        if not row:
            return await ctx.send(embed=discord.Embed(description="No active custom booster role found for your account.", color=DARK_COLOR))

        role = ctx.guild.get_role(row[0])
        if role:
            await role.delete(reason="Booster choice teardown execution.")
        
        await self.bot.db.execute("DELETE FROM booster_roles WHERE guild_id = ? AND user_id = ?", (ctx.guild.id, ctx.author.id))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description="Your custom booster role has been permanently deleted.", color=DARK_COLOR))

    @br_base.command(name="list")
    async def br_list(self, ctx):
        """List active custom booster roles inside the current server."""
        async with self.bot.db.execute("SELECT user_id, role_id FROM booster_roles WHERE guild_id = ?", (ctx.guild.id,)) as c:
            rows = await c.fetchall()
            
        lines = []
        for r in rows:
            member = ctx.guild.get_member(r[0])
            role = ctx.guild.get_role(r[1])
            if member and role:
                lines.append(f"{member.mention} -> {role.mention}")

        embed = discord.Embed(title="Server Booster Roles", description="\n".join(lines) if lines else "No custom booster roles active.", color=DARK_COLOR)
        await ctx.send(embed=embed)

    @br_base.group(name="filter", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def filter_base(self, ctx):
        """Manage text filtering block criteria parameters for role names."""
        await ctx.send(embed=discord.Embed(description="Available options: add, remove, list", color=DARK_COLOR))

    @filter_base.command(name="add")
    async def filter_add(self, ctx, *, word: str):
        """Add a word phrase restriction parameter targeting naming formats."""
        await self.bot.db.execute("INSERT OR IGNORE INTO booster_filters (guild_id, word) VALUES (?, ?)", (ctx.guild.id, word.lower()))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Appended `{word}` to custom booster role name filters.", color=DARK_COLOR))

    @filter_base.command(name="remove")
    async def filter_remove(self, ctx, *, word: str):
        """Remove a word phrase restriction rule targeting naming formats."""
        await self.bot.db.execute("DELETE FROM booster_filters WHERE guild_id = ? AND word = ?", (ctx.guild.id, word.lower()))
        await self.bot.db.commit()
        await ctx.send(embed=discord.Embed(description=f"Removed `{word}` from booster role name filters.", color=DARK_COLOR))

    @filter_base.command(name="list")
    async def filter_list(self, ctx):
        """List active booster role phrase naming blocks criteria metrics rules."""
        async with self.bot.db.execute("SELECT word FROM booster_filters WHERE guild_id = ?", (ctx.guild.id,)) as c:
            rows = await c.fetchall()
        words = [f"`{r[0]}`" for r in rows]
        embed = discord.Embed(title="Booster Name Filters", description=", ".join(words) if words else "No active name filters configured.", color=DARK_COLOR)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BoosterRole(bot))