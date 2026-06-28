import discord
from discord.ext import commands
import asyncio

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class VoiceInterfaceView(discord.ui.View):
    def __init__(self, channel_id: int, creator_id: int, bot):
        super().__init__(timeout=None)
        self.channel_id = channel_id
        self.creator_id = creator_id
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.data.get("custom_id") == "vc_claim":
            return True
            
        if interaction.user.id != self.creator_id:
            await interaction.response.send_message("❌ You are not the manager of this room.", ephemeral=True)
            return False
        return True

    @discord.ui.button(custom_id="vc_lock", label="🔒 Lock", style=discord.ButtonStyle.secondary, row=0)
    async def lock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=False, view_channel=True)
            await interaction.response.send_message("Room locked.", ephemeral=True)

    @discord.ui.button(custom_id="vc_unlock", label="🔓 Unlock", style=discord.ButtonStyle.secondary, row=0)
    async def unlock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, connect=True, view_channel=True)
            await interaction.response.send_message("Room unlocked.", ephemeral=True)

    @discord.ui.button(custom_id="vc_ghost", label="👻 Ghost", style=discord.ButtonStyle.secondary, row=0)
    async def ghost_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await interaction.response.send_message("Room hidden.", ephemeral=True)

    @discord.ui.button(custom_id="vc_reveal", label="👁️ Reveal", style=discord.ButtonStyle.secondary, row=0)
    async def reveal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            await channel.set_permissions(interaction.guild.default_role, view_channel=True)
            await interaction.response.send_message("Room revealed.", ephemeral=True)

    @discord.ui.button(custom_id="vc_claim", label="🎤 Claim", style=discord.ButtonStyle.secondary, row=0)
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if not channel:
            return

        if self.creator_id in [m.id for m in channel.members]:
            return await interaction.response.send_message("❌ The current room manager is still in the channel.", ephemeral=True)

        self.creator_id = interaction.user.id
        await channel.set_permissions(interaction.user, connect=True, view_channel=True, manage_channels=True)
        
        await self.bot.db.execute("UPDATE active_voice_rooms SET owner_id = ? WHERE channel_id = ?", (interaction.user.id, self.channel_id))
        await self.bot.db.commit()
        await interaction.response.send_message("👑 Claimed ownership.", ephemeral=True)

    @discord.ui.button(custom_id="vc_disconnect", label="🔌 Disconnect", style=discord.ButtonStyle.secondary, row=1)
    async def disconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Right-click a user and select 'Disconnect' to remove them.", ephemeral=True)

    @discord.ui.button(custom_id="vc_activity", label="🎮 Start Activity", style=discord.ButtonStyle.secondary, row=1)
    async def activity_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Use the Activities launcher button inside your Discord panel to start a session.", ephemeral=True)

    @discord.ui.button(custom_id="vc_info", label="ℹ️ Info", style=discord.ButtonStyle.secondary, row=1)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            limit = channel.user_limit if channel.user_limit > 0 else "Unlimited"
            await interaction.response.send_message(f"**Room Info**\n• Owner: <@{self.creator_id}>\n• Members: `{len(channel.members)}` slots\n• Limit: `{limit}`", ephemeral=True)

    @discord.ui.button(custom_id="vc_increase", label="➕ Increase", style=discord.ButtonStyle.secondary, row=1)
    async def increase_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            new_limit = min(channel.user_limit + 1, 99) if channel.user_limit > 0 else 1
            await channel.edit(user_limit=new_limit)
            await interaction.response.send_message(f"Limit: `{new_limit}` slots", ephemeral=True)

    @discord.ui.button(custom_id="vc_decrease", label="➖ Decrease", style=discord.ButtonStyle.secondary, row=1)
    async def decrease_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.guild.get_channel(self.channel_id)
        if channel:
            new_limit = max(channel.user_limit - 1, 0)
            await channel.edit(user_limit=new_limit)
            await interaction.response.send_message(f"Limit: `{new_limit if new_limit > 0 else 'Unlimited'}` slots", ephemeral=True)


class VoiceAutomation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vcsetup")
    @commands.has_permissions(administrator=True)
    async def vc_setup(self, ctx: commands.Context):
        try:
            category = await ctx.guild.create_category(name="Voice Rooms", reason="Automation: Setup")
            master_channel = await ctx.guild.create_voice_channel(name="Join to Create", category=category)
        except Exception as e:
            return await ctx.send(f"❌ Error: `{e}`")

        try:
            await self.bot.db.execute("""
                INSERT INTO voice_settings (guild_id, master_channel_id, category_id)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET 
                    master_channel_id = excluded.master_channel_id,
                    category_id = excluded.category_id
            """, (ctx.guild.id, master_channel.id, category.id))
            await self.bot.db.commit()
        except Exception as e:
            return await ctx.send(f"❌ Database error: `{e}`")

        embed = discord.Embed(
            title="Voice System Operational",
            description=f"✅ **Category Group:** `{category.name}`\n✅ **Voice Hub:** {master_channel.mention}\n\nJoin the hub to create a channel.",
            color=DARK_COLOR
        )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        guild = member.guild

        async with self.bot.db.execute(
            "SELECT master_channel_id, category_id FROM voice_settings WHERE guild_id = ?", 
            (guild.id,)
        ) as cursor:
            row = await cursor.fetchone()
        
        if not row:
            return
            
        master_id, category_id = row

        if after.channel and after.channel.id == master_id:
            category = guild.get_channel(category_id)
            if category:
                try:
                    temp_channel = await guild.create_voice_channel(
                        name=f"{member.name}'s room",
                        category=category,
                        reason="Automation: Initial naked creation"
                    )
                    
                    await asyncio.sleep(0.3)
                    
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True),
                        member: discord.PermissionOverwrite(connect=True, view_channel=True, manage_channels=True)
                    }
                    for target, overwrite in overwrites.items():
                        await temp_channel.set_permissions(target, overwrite=overwrite)

                    await self.bot.db.execute(
                        "INSERT INTO active_voice_rooms (channel_id, owner_id, guild_id) VALUES (?, ?, ?)",
                        (temp_channel.id, member.id, guild.id)
                    )
                    await self.bot.db.commit()
                    
                    await member.move_to(temp_channel)
                    
                    embed = discord.Embed(
                        title="VoiceMaster Interface",
                        description="Use the buttons below to manage your room rules.",
                        color=DARK_COLOR
                    )
                    embed.add_field(
                        name="Controls",
                        value="🔒 — **Lock** entries\n"
                              "🔓 — **Unlock** entries\n"
                              "👻 — **Ghost** hide channel\n"
                              "👁️ — **Reveal** show channel\n"
                              "🎤 — **Claim** ownership if empty\n\n"
                              "➕ — **Increase** player slots\n"
                              "➖ — **Decrease** player slots",
                        inline=False
                    )
                    
                    view = VoiceInterfaceView(channel_id=temp_channel.id, creator_id=member.id, bot=self.bot)
                    await temp_channel.send(embed=embed, view=view)
                except Exception as e:
                    print(f"Error handling dynamic user room: {e}")

        if before.channel:
            async with self.bot.db.execute(
                "SELECT owner_id FROM active_voice_rooms WHERE channel_id = ?", 
                (before.channel.id,)
            ) as cursor:
                is_temp_room = await cursor.fetchone()

            if is_temp_room and len(before.channel.members) == 0:
                try:
                    await before.channel.delete(reason="Automation: Room empty")
                    await self.bot.db.execute("DELETE FROM active_voice_rooms WHERE channel_id = ?", (before.channel.id,))
                    await self.bot.db.commit()
                except (discord.NotFound, discord.Forbidden):
                    pass

async def setup(bot):
    await bot.add_cog(VoiceAutomation(bot))