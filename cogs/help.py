import discord
from discord.ext import commands
from discord import app_commands

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help")
    @app_commands.describe(command="Specific command to view details for")
    async def help_command(self, ctx, *, command: str = None):
        """View available commands or get details on a specific command."""
        pref = await self.bot.get_prefix(ctx.message)
        pref = pref[0] if isinstance(pref, list) else pref

        if not command:
            embed = discord.Embed(
                title="Help Menu", 
                description=f"Use `{pref}help <command>` for usage details.", 
                color=DARK_COLOR
            )
            
            embed.add_field(
                name="Prefix", 
                value=f"`{pref}prefix`, `{pref}prefix self`, `{pref}prefix set`, `{pref}prefix remove`", 
                inline=False
            )
            embed.add_field(
                name="Moderation", 
                value=f"`{pref}ban`, `{pref}kick`, `{pref}mute`, `{pref}unmute`, `{pref}timeout`, `{pref}untimeout`, `{pref}jail`, `{pref}warn`, `{pref}softban`, `{pref}lock`, `{pref}purge`, `{pref}nicklock`", 
                inline=False
            )
            embed.add_field(
                name="Setup",
                value=f"`{pref}setup`",
                inline=False
            )
            embed.add_field(
                name="Welcome",
                value=f"`{pref}welcomeset`, `{pref}testwelcome`",
                inline=False
            )
            embed.add_field(
                name="Utility", 
                value=f"`{pref}alias`, `{pref}imgonly`, `{pref}invoke`, `{pref}roblox`, `{pref}snipe`, `{pref}afk`, `{pref}role`", 
                inline=False
            )
            embed.add_field(
                name="Settings", 
                value=f"`{pref}settings`, `{pref}settings welcomechannel`, `{pref}settings baserole`, `{pref}settings muterole`, `{pref}settings jailrole`, `{pref}settings modlogs`, `{pref}settings joinlogs`, `{pref}settings autonick`, `{pref}vanity set`, `{pref}vanity remove`, `{pref}vanity view`", 
                inline=False
            )
            embed.add_field(
                name="Boosterrole", 
                value=f"`{pref}boosterrole`, `{pref}boosterrole setup`, `{pref}boosterrole claim`, `{pref}boosterrole name`, `{pref}boosterrole color`, `{pref}boosterrole icon`, `{pref}boosterrole delete`, `{pref}boosterrole list`, `{pref}boosterrole filter`", 
                inline=False
            )
            embed.add_field(
                name="Voice Systems",
                value=f"`{pref}vcsetup`",
                inline=False
            )
            
            return await ctx.send(embed=embed)

        target_cmd = self.bot.get_command(command.lower())
        
        if not target_cmd:
            return await ctx.send(embed=discord.Embed(description="Command not found.", color=DARK_COLOR))

        embed = discord.Embed(title=f"Command: {target_cmd.qualified_name}", color=DARK_COLOR)
        embed.add_field(name="Description", value=target_cmd.help or "No description provided.", inline=False)
        
        usage = f"`{pref}{target_cmd.qualified_name} {target_cmd.signature}`"
        embed.add_field(name="Usage", value=usage, inline=False)

        if target_cmd.aliases:
            embed.add_field(name="Aliases", value=", ".join([f"`{a}`" for a in target_cmd.aliases]), inline=False)

        if isinstance(target_cmd, commands.Group):
            subcommands = [f"`{sub.name}`" for sub in target_cmd.commands]
            if subcommands:
                embed.add_field(name="Subcommands", value=", ".join(subcommands), inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))