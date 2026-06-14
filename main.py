import discord
import os
import asyncio
from discord.ext import commands
from threading import Thread
from flask import Flask

# വെബ് സെർവർ സെറ്റപ്പ്
app = Flask('')
@app.route('/')
def home():
    return "Bot is Online and Ready!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# --- TICKET SYSTEM BUTTONS ---
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # കസ്റ്റം ഐഡി ഉള്ളതുകൊണ്ട് ഈ ബട്ടൺ എപ്പോഴും ലൈവ് ആയിരിക്കും

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Closing and deleting this ticket in 3 seconds...", ephemeral=False)
        await asyncio.sleep(3)
        await interaction.channel.delete()

class TicketSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📩 Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        
        existing_channel = discord.utils.get(guild.channels, name=f"ticket-{member.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"⚠️ You already have an open ticket here: {existing_channel.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        ticket_channel = await guild.create_text_channel(name=f"ticket-{member.name}", overwrites=overwrites)
        
        embed = discord.Embed(
            title="🎫 Support Ticket Created!",
            description=f"Hello {member.mention},\nOur Staff/Admins will assist you shortly. Please explain your issue here.\n\nClick the button below to **Close** this ticket when resolved.",
            color=0x00ff00
        )
        
        await ticket_channel.send(embed=embed, view=TicketCloseView())
        await interaction.response.send_message(f"✅ Ticket created! Go to {ticket_channel.mention}", ephemeral=True)


# ബോട്ട് ക്ലാസ് കസ്റ്റമൈസ് ചെയ്യുന്നു (Persistent Views ലോഡ് ചെയ്യാൻ)
class KVABot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # ബോട്ട് ലോഗിൻ ആകുന്നതിന് തൊട്ടുമുൻപ് ബട്ടണുകൾ ബാക്ക്ഗ്രൗണ്ടിൽ രജിസ്റ്റർ ചെയ്യുന്നു
        self.add_view(TicketSetupView())
        self.add_view(TicketCloseView())
        print("Persistent ticket views added successfully!")

bot = KVABot()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Managing Server & Tickets! 👑"))
    print(f'{bot.user.name} Is Ready and Loaded!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s) successfully!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# --- 🔥 വെൽക്കം സിസ്റ്റം ---
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="🛬丨ꜱᴩᴀᴡɴ-ᴀʀᴇᴀ")
    if channel:
        embed = discord.Embed(
            title="👋 Welcome to the Server!",
            description=f"Hey {member.mention}, welcome to **{member.guild.name}**! 🎉\n\nWe are extremely happy to have you here. Make sure to check out the rules and have a great time!",
            color=0x00ff00
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Member #{len(member.guild.members)}")
        await channel.send(f"Welcome {member.mention}! ✨", embed=embed)


# --- 1. SLASH COMMAND: INFO ---
@bot.tree.command(name="info", description="View all available bot commands")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(title="KVA BOT", description="Server Management & Ticket Slash Commands:", color=0x00ff00)
    embed.add_field(name="/info", value="Check all available commands", inline=False)
    embed.add_field(name="/ping", value="Check if the bot is online and active", inline=False)
    embed.add_field(name="/clear [amount]", value="Delete multiple messages instantly (Admin Only)", inline=False)
    embed.add_field(name="/kick [user] [reason]", value="Kick a user from the server (Admin Only)", inline=False)
    embed.add_field(name="/ban [user] [reason]", value="Ban a user from the server (Admin Only)", inline=False)
    embed.add_field(name="/announce [message]", value="Create a beautiful announcement box (Admin Only)", inline=False)
    embed.add_field(name="/setup_ticket", value="Setup the private support ticket system (Admin Only)", inline=False)
    await interaction.response.send_message(embed=embed)

# --- 2. SLASH COMMAND: PING ---
@bot.tree.command(name="ping", description="Check bot status")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("⚡ Bot is fully active and running smooth!")

# --- 3. SLASH COMMAND: CLEAR ---
@bot.tree.command(name="clear", description="Delete messages from the channel (Admin Only)")
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 Successfully deleted {len(deleted)} messages!", ephemeral=True)

# --- 4. SLASH COMMAND: KICK ---
@bot.tree.command(name="kick", description="Kick a member from the server (Admin Only)")
@discord.app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member.mention} has been kicked! Reason: {reason}")

# --- 5. SLASH COMMAND: BAN ---
@bot.tree.command(name="ban", description="Ban a member from the server (Admin Only)")
@discord.app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member.mention} has been permanently banned! Reason: {reason}")
# --- 6. SLASH COMMAND: ANNOUNCE (WITH DIRECT PING) ---
@bot.tree.command(name="announce", description="Create a beautiful announcement box with direct ping (Admin Only)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def announce(interaction: discord.Interaction, message_content: str, ping_role: discord.Role = None, ping_everyone: bool = False):
    # 1. ആദ്യം അഡ്മിന് മാത്രം കാണാവുന്ന രീതിയിൽ റെസ്പോൺസ് നൽകുന്നു
    await interaction.response.send_message("Announcement sent!", ephemeral=True)
    
    # 2. നോർമൽ ടെക്സ്റ്റ് മെസ്സേജ് ആയി അയക്കാനുള്ള പിങ് സെറ്റ് ചെയ്യുന്നു
    ping_text = ""
    if ping_everyone:
        ping_text = "@everyone"
    elif ping_role:
        ping_text = ping_role.mention

    # 3. മനോഹരമായ എംബെഡ് ബോക്സ് ഉണ്ടാക്കുന്നു
    embed = discord.Embed(
        title="✨𝗔𝗡𝗡𝗢𝗨𝗡𝗖𝗘𝗠𝗘𝗡𝗧✨",
        description=message_content,
        color=0xff0000
    )
    embed.set_footer(text=f"Announced by {interaction.user.name}")
    # --- 8. SLASH COMMAND: SAY (NORMAL TEXT MESSAGE WITH DIRECT PING) ---
@bot.tree.command(name="say", description="Send a normal text message through the bot (Admin Only)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def say(interaction: discord.Interaction, message: str):
    # അഡ്മിന് മാത്രം കാണാവുന്ന രീതിയിൽ മെസ്സേജ് അയച്ചു എന്ന് കൺഫേം ചെയ്യുന്നു
    await interaction.response.send_message("Message sent successfully!", ephemeral=True)
    
    # ബോട്ട് വഴി ചാനലിലേക്ക് നോർമൽ ടെക്സ്റ്റ് മെസ്സേജ് നേരിട്ട് അയക്കുന്നു
    await interaction.channel.send(message)

    # 4. ചാനലിലേക്ക് ആദ്യം ഡയറക്ട് പിങ് മെസ്സേജും, തൊട്ടുതാഴെ എംബെഡും ഒന്നിച്ച് അയക്കുന്നു
    if ping_text:
        await interaction.channel.send(content=ping_text, embed=embed)
    else:
        await interaction.channel.send(embed=embed)


# --- 7. SLASH COMMAND: SETUP TICKET ---
@bot.tree.command(name="setup_ticket", description="Setup the private support ticket box (Admin Only)")
@discord.app_commands.checks.has_permissions(administrator=True)
async def setup_ticket(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📩 Need Support?",
        description="Click the button below to open a private support ticket and talk directly to the Admins.",
        color=0x5865F2
    )
    await interaction.response.send_message("Deploying ticket system...", ephemeral=True)
    await interaction.channel.send(embed=embed, view=TicketSetupView())


if __name__ == "__main__":
    keep_alive()
    token = os.environ.get("TOKEN")
    bot.run(token)
