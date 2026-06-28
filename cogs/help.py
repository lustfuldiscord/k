import discord
from discord.ext import commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="List all available commands or get details on a specific command.")
    @discord.app_commands.describe(command="The specific command you want to inspect")
    async def help_command(self, ctx: commands.Context, *, command: str = None):
        """Displays a menu of all available modules or details for a specific command."""
        pref = ctx.prefix

        # --- Scenario 1: Detailed Help for a Specific Command/Group ---
        if command:
            target = self.bot.get_command(command)
            if not target:
                return await ctx.send(embed=discord.Embed(
                    description=f"Command `{command}` could not be found.", 
                    color=DARK_COLOR
                ))

            embed = discord.Embed(
                title=f"Command Help: {target.qualified_name}",
                description=target.help or "No description provided.",
                color=DARK_COLOR
            )
            
            # Show aliases if they exist
            if target.aliases:
                embed.add_field(name="Aliases", value=", ".join(target.aliases), inline=False)
                
            # Show syntax usage format
            syntax = f"{pref}{target.qualified_name} {target.signature}"
            embed.add_field(name="Usage Syntax", value=f"`{syntax}`", inline=False)

            # If it's a command group (like autorole, honeypot, vanity), list its subcommands
            if isinstance(target, commands.Group):
                subcmds = [f"`{c.name}` - {c.short_doc}" for c in target.commands]
                if subcmds:
                    embed.add_field(name="Available Subcommands", value="\n".join(subcmds), inline=False)

            return await ctx.send(embed=embed)

        # --- Scenario 2: Main Help Menu (List all Cogs and Commands) ---
        embed = discord.Embed(
            title=f"{self.bot.user.name} Help Menu",
            description=f"Use `{pref}help <command>` to get more specific information on any command layout.",
            color=DARK_COLOR
        )

        for cog_name, cog in self.bot.cogs.items():
            # Skip the Help cog itself or cogs with hidden commands to keep the menu clean
            if cog_name.lower() == "help":
                continue

            # Get visible commands in this specific cog
            visible_commands = [
                f"`{c.name}`" for c in cog.get_commands() 
                if not c.hidden
            ]

            if visible_commands:
                # Clean up the name styling for the fields (e.g., cogs.moderation -> Moderation)
                display_name = cog_name.replace("cogs.", "").title()
                embed.add_field(
                    name=f"⚙️ {display_name} Module",
                    value=" ".join(visible_commands),
                    inline=False
                )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
