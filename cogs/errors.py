import discord
from discord.ext import commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global error listener for prefix and hybrid commands."""
        # Prevent double handling if the command has its own local error handler
        if hasattr(ctx.command, 'on_error'):
            return

        # Unwrap wrapped exceptions (like inside hybrid/app commands)
        error = getattr(error, 'original', error)

        # 1. Handle "403 Forbidden / Missing Permissions" (Your screenshot error)
        if isinstance(error, discord.Forbidden):
            embed = discord.Embed(
                title="Execution Error",
                description="bot missing permissions.",
                color=DARK_COLOR
            )
            return await ctx.send(embed=embed, delete_after=10)

        # 2. Handle when the user lacks the proper permissions
        if isinstance(error, commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions).replace("_", " ").title()
            embed = discord.Embed(
                title="Permission Denied",
                description=f"permission error: `{missing_perms}`",
                color=DARK_COLOR
            )
            return await ctx.send(embed=embed, delete_after=10)

        # 3. Handle Command Cooldowns
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Slow Down",
                description=f"Command Cooldown, Try in `{error.retry_after:.1f}` seconds.",
                color=DARK_COLOR
            )
            return await ctx.send(embed=embed, delete_after=5)

        # 4. Handle Bad/Missing Arguments
        if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            pref = ctx.prefix
            usage = f"`{pref}{ctx.command.qualified_name} {ctx.command.signature}`" if ctx.command else "Unknown"
            embed = discord.Embed(
                title="Invalid Arguments",
                description=f"the syntax provided is incorrect.\n\n**Correct Usage:**\n{usage}",
                color=DARK_COLOR
            )
            return await ctx.send(embed=embed)

        # 5. Silently ignore unknown commands so it doesn't spam console log
        if isinstance(error, commands.CommandNotFound):
            return

        # Fallback for unexpected system errors
        embed = discord.Embed(
            title="Command Failed",
            description="scary internal issue.",
            color=DARK_COLOR
        )
        try:
            await ctx.send(embed=embed, delete_after=10)
        except discord.DiscordException:
            pass
            
        # Log the actual raw error to your terminal so you can fix bugs
        print(f"Ignored exception in command {ctx.command}: {error}")

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))