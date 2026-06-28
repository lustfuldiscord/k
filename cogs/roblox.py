import discord
from discord.ext import commands
import aiohttp
from dateutil import parser

DARK_COLOR = discord.Color.from_rgb(47, 49, 54)

class Roblox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="roblox", description="View a user's Roblox profile details.")
    @discord.app_commands.describe(username="The Roblox username to look up")
    async def roblox_profile(self, ctx: commands.Context, username: str):
        await ctx.defer()

        # 1. Fetch User ID from Username
        async with aiohttp.ClientSession() as session:
            id_url = "https://users.roblox.com/v1/usernames/users"
            payload = {"filenames": [username], "excludeBannedUsers": False}
            
            # Roblox API expects "usernames" array in the request json
            async with session.post(id_url, json={"usernames": [username], "excludeBannedUsers": False}) as resp:
                if resp.status != 200:
                    return await ctx.send("❌ Failed to connect to Roblox servers.")
                data = await resp.json()
                
                if not data.get("data"):
                    return await ctx.send(f"❌ Could not find a Roblox user named `{username}`.")
                
                user_data = data["data"][0]
                user_id = user_data["id"]
                display_name = user_data["displayName"]
                requested_name = user_data["name"]

            # 2. Fetch Detailed Profile Info (Created date, About, Status)
            profile_url = f"https://users.roblox.com/v1/users/{user_id}"
            async with session.get(profile_url) as resp:
                profile_data = await resp.json() if resp.status == 200 else {}

            # 3. Fetch Friends & Followers Counts
            friends_url = f"https://friends.roblox.com/v1/users/{user_id}/friends/count"
            followers_url = f"https://friends.roblox.com/v1/users/{user_id}/followers/count"
            following_url = f"https://friends.roblox.com/v1/users/{user_id}/followings/count"

            async with session.get(friends_url) as r1, session.get(followers_url) as r2, session.get(following_url) as r3:
                friends_count = (await r1.json()).get("count", 0) if r1.status == 200 else 0
                followers_count = (await r2.json()).get("count", 0) if r2.status == 200 else 0
                following_count = (await r3.json()).get("count", 0) if r3.status == 200 else 0

            # 4. Fetch User Avatar Headshot Image
            avatar_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=180x180&format=Png&isCircular=false"
            async with session.get(avatar_url) as resp:
                avatar_data = await resp.json() if resp.status == 200 else {}
                avatar_image = "https://tr.rbxcdn.com/30day-avatarheadshot-unknown"
                if avatar_data.get("data"):
                    avatar_image = avatar_data["data"][0].get("imageUrl", avatar_image)

        # 5. Format Timestamps and Build the Custom Layout Embed
        created_at_raw = profile_data.get("created", "")
        if created_at_raw:
            dt = parser.isoparse(created_at_raw)
            created_str = dt.strftime("%B %d, %Y")
            # Calculate roughly how many years ago
            years_ago = 2026 - dt.year
            time_suffix = f" ({years_ago} years ago)" if years_ago > 0 else ""
            created_display = f"{created_str}{time_suffix}"
        else:
            created_display = "Unknown"

        about_text = profile_data.get("description") or "c:"
        is_banned = "Banned" if profile_data.get("isBanned") else "Active/Unknown"

        embed = discord.Embed(
            title=f"{display_name} (@{requested_name})", 
            description=about_text, 
            color=DARK_COLOR
        )
        embed.set_thumbnail(url=avatar_image)
        
        embed.add_field(name="Created", value=created_display, inline=False)
        embed.add_field(name="About\n| Status", value=is_banned, inline=False)
        
        social_metrics = (
            f"**| Friends:** {friends_count}\n"
            f"**| Following:** {following_count}\n"
            f"**| Followers:** {followers_count}"
        )
        embed.add_field(name="Social", value=social_metrics, inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Roblox(bot))