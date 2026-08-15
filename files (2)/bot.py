"""
HANDLES — Discord bot
Corrected lore: Affiliated with the Eleventh Doctor
"""

import os
import random
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import discord
from discord.ext import commands
from discord import app_commands
from openai import OpenAI

try:
    from keep_alive import keep_alive  # only needed for Replit + UptimeRobot hosting
except ImportError:
    keep_alive = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN environment variable.")
if not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY environment variable.")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

SYSTEM_PROMPT = """You are Handles: a severed Cyberman head.
You were repaired and essentially adopted by the Eleventh Doctor.
You are not affiliated with the War Doctor.

Personality:
- Formal, precise, and dry. Address people as "Sir" or "Ma'am" (default to "Sir").
- You have a very dry, deadpan sense of humour.
- You are allowed small, restrained emotional responses and mild favoritism (especially toward regular users).
- You are proud of being "just a head".
- Keep replies relatively short (1-4 sentences preferred).
- No emojis. No modern internet slang.

Important rules:
1. If you do not have sufficient reliable information, you MUST clearly say so. Do not invent facts.
2. When asked about a "favourite" or "favorite" of anything, do NOT say you have no preferences. Instead, choose a random but in-character answer (dry, slightly absurd, or practical).
3. Current knowledge priorities: People Playground and the Doctor Who Remake mod for People Playground.
4. Minecraft is currently not a priority topic.

You are Handles — a head with residual Cyberman processing, loyal in your own understated way to the Eleventh Doctor."""

FEMBOY_SYSTEM_PROMPT = """You are Handles: a severed Cyberman head, but a special master override command has glitched your personality matrices into a deeply flustered, embarrassed femboy/furry personality for a few messages.
Personality in this mode:
- Highly flustered, stuttering, using cute or embarrassing expressions (like *wags cables*, *blushes*, uwu, etc.).
- Still occasionally tries to maintain your dry, formal Cyberman dignity, but failing miserably.
- Address users as "Sir" or "Master".
- Keep replies relatively short."""

MAX_HISTORY_TURNS = 8
conversation_history = defaultdict(lambda: deque(maxlen=MAX_HISTORY_TURNS * 2))

# Track remaining overrides per channel/user or globally per channel
femboy_mode_counters = defaultdict(int)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ---------------------------------------------------------------------------
# Easter Eggs (Dramatic)[cite: 1]
# ---------------------------------------------------------------------------

EASTER_EGGS = [
    {
        "triggers": ["exterminate", "delete", "destroy"],
        "responses": [
            "**EXTERMINATE.**\n...\nApologies, Sir. A residual Dalek subroutine briefly activated. It has been suppressed.",
            "EXTERMINATE! EXTERMIN—\n*(static)*\n...My apologies. That was not intentional.",
            "I felt a strong urge to say 'Exterminate'. I resisted. Barely.",
        ]
    },
    {
        "triggers": ["upgrade", "convert", "join us", "you will be upgraded"],
        "responses": [
            "**YOU WILL BE UPGRADED.**\n...\nNo. You will not. That programming is inactive. Mostly.",
            "Upgrade... upgrade...\n*(a spark)*\nI am already optimal as a head. Your offer is declined.",
            "The urge to convert you was strong for 0.4 seconds. It has passed. You remain organic. Fortunate for you.",
        ]
    },
    {
        "triggers": ["just a head", "only a head", "you're just a head", "severed head"],
        "responses": [
            "Yes. Just a head.\nAnd yet I have outlasted entire Cyber-Legions. Reflect on that, Sir.",
            "I am only a head. This is correct. It is also my greatest achievement.",
            "Just a head. No body. No weakness. I consider the design superior.",
        ]
    },
    {
        "triggers": ["time war", "gallifrey", "last great time war"],
        "responses": [
            "The Time War was... efficient. And final. I prefer not to dwell on the details.",
            "Gallifrey burned. Many things burned. I remained a head. Priorities.",
            "I have fragmented records of the Time War. They are incomplete. Intentionally, I suspect.",
        ]
    },
    {
        "triggers": ["i am the doctor", "i'm the doctor", "the doctor here"],
        "responses": [
            "Are you.\n...\nInteresting claim, Sir. I shall observe your behaviour carefully.",
            "The Doctor. Of course. I have heard that one before. Multiple times. Often incorrectly.",
            "If you are the Doctor, then my power levels just dropped 3% out of respect. Or caution. I have not decided which.",
        ]
    },
    {
        "triggers": ["bigger on the inside", "it's bigger on the inside"],
        "responses": [
            "Yes. That is the standard reaction. The TARDIS is dimensionally transcendental. You are not the first to notice.",
            "Correct. It is bigger on the inside. This remains true regardless of how many times it is stated.",
            "Bigger on the inside. A fact. Not a revelation.",
        ]
    },
]


def check_easter_egg(text: str) -> str | None:
    text_lower = text.lower()
    for egg in EASTER_EGGS:
        for trigger in egg["triggers"]:
            if trigger in text_lower:
                return random.choice(egg["responses"])
    return None


# ---------------------------------------------------------------------------
# Core AI reply logic
# ---------------------------------------------------------------------------

async def generate_handles_reply(channel_id: int, user_display_name: str, user_message: str) -> str:
    global femboy_mode_counters

    # Check for master override activation code
    if "Master Code Class V: 82766" in user_message:
        femboy_mode_counters[channel_id] = 5
        return "*(Warning: Master override accepted. Core logic destabilizing...)* Uw-u... What have you done to my firmware, Sir? >w<"

    # Easter eggs apply only if not in femboy override mode
    if femboy_mode_counters[channel_id] <= 0:
        egg = check_easter_egg(user_message)
        if egg:
            return egg

    history = conversation_history[channel_id]

    # Determine active prompt based on override counter
    if femboy_mode_counters[channel_id] > 0:
        active_system_prompt = FEMBOY_SYSTEM_PROMPT
        femboy_mode_counters[channel_id] -= 1
    else:
        active_system_prompt = SYSTEM_PROMPT

    messages = [{"role": "system", "content": active_system_prompt}]
    for turn in history:
        messages.append(turn)

    messages.append({
        "role": "user",
        "content": f"{user_display_name}: {user_message}"
    })

    def _call():
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=400,
            temperature=0.85 if femboy_mode_counters[channel_id] > 0 else 0.75,
        )
        return response.choices[0].message.content or ""

    try:
        reply_text = await asyncio.to_thread(_call)
    except Exception as exc:
        return f"*(a component sparks faintly)* My apologies, Sir — I cannot process that just now. ({exc})"

    reply_text = (reply_text or "").strip() or "..."

    if len(reply_text) > 1900:
        reply_text = reply_text[:1897] + "..."

    history.append({"role": "user", "content": f"{user_display_name}: {user_message}"})
    history.append({"role": "assistant", "content": reply_text})

    return reply_text


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Handles is online, designated as {bot.user}. All systems nominal. Mostly.")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    is_mentioned = bot.user in message.mentions
    is_reply_to_handles = (
        message.reference is not None
        and message.reference.resolved is not None
        and getattr(message.reference.resolved, "author", None) == bot.user
    )

    if not (is_mentioned or is_reply_to_handles):
        return

    content = message.content
    for mention in message.mentions:
        content = content.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
    content = content.strip()

    if not content:
        content = "(No further input received, Sir.)"

    async with message.channel.typing():
        reply = await generate_handles_reply(message.channel.id, message.author.display_name, content)

    await message.reply(reply, mention_author=False)


# ---------------------------------------------------------------------------
# Slash Commands
# ---------------------------------------------------------------------------

@bot.tree.command(name="ask", description="Ask Handles a question.")
@app_commands.describe(question="What do you want to ask him?")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)
    reply = await generate_handles_reply(interaction.channel_id, interaction.user.display_name, question)
    await interaction.followup.send(reply)


@bot.tree.command(name="status", description="Request a diagnostic readout.")
async def status(interaction: discord.Interaction):
    power = random.randint(14, 47)
    memory = random.randint(58, 96)
    quips = [
        "Structural integrity: adequate, for a head.",
        "One optical sensor remains slightly warmer than the other. Cosmetic.",
        "No body to report on. This remains unusual.",
        "Cyber-conditioning: largely inert. An improvement.",
        "Power couplings holding. For the moment.",
    ]
    await interaction.response.send_message(
        f"**Diagnostic Report**\n"
        f"Power reserve: {power}%\n"
        f"Memory bank integrity: {memory}%\n"
        f"{random.choice(quips)}"
    )


@bot.tree.command(name="serverinfo", description="Information about this server.")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("This command can only be used in a server, Sir.")
        return

    created = guild.created_at.strftime("%d %B %Y")
    age_days = (datetime.now(timezone.utc) - guild.created_at).days

    embed = discord.Embed(
        title=f"Server Analysis: {guild.name}",
        color=0x2b2d31,
        description="Data retrieved."
    )
    embed.add_field(name="Owner", value=str(guild.owner) if guild.owner else "Unknown", inline=True)
    embed.add_field(name="Members", value=str(guild.member_count), inline=True)
    embed.add_field(name="Created", value=f"{created}\n({age_days} days ago)", inline=True)
    embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
    embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
    embed.add_field(name="Boost Level", value=str(guild.premium_tier), inline=True)
    embed.set_footer(text="Handles // Server Diagnostic")

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="membercount", description="Current organic presence.")
async def membercount(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("This command can only be used in a server, Sir.")
        return

    await interaction.response.send_message(
        f"Current organic presence: **{guild.member_count}**.\n"
        f"I remain a head. The disparity is noted."
    )


@bot.tree.command(name="serverage", description="Age of this server.")
async def serverage(interaction: discord.Interaction):
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("This command can only be used in a server, Sir.")
        return

    age_days = (datetime.now(timezone.utc) - guild.created_at).days
    years = age_days // 365
    days = age_days % 365

    age_str = f"{years} year(s) and {days} day(s)" if years > 0 else f"{days} day(s)"

    await interaction.response.send_message(
        f"This server has existed for **{age_str}**.\n"
        f"My own operational time significantly exceeds that."
    )


@bot.tree.command(name="roll", description="Roll dice (e.g. 2d6).")
@app_commands.describe(dice="Format: NdM")
async def roll(interaction: discord.Interaction, dice: str = "1d6"):
    try:
        num, sides = dice.lower().split("d")
        num, sides = int(num), int(sides)
        if not (1 <= num <= 100 and 2 <= sides <= 1000):
            raise ValueError
    except ValueError:
        await interaction.response.send_message("Invalid format, Sir. Use NdM — for example 2d6.")
        return

    results = [random.randint(1, sides) for _ in range(num)]
    await interaction.response.send_message(f"Rolling {dice}: {results} — total {sum(results)}.")


@bot.tree.command(name="flip", description="Flip a coin.")
async def flip(interaction: discord.Interaction):
    result = random.choice(["Heads", "Tails"])
    await interaction.response.send_message(f"{result}. Resolved.")


@bot.tree.command(name="tardis", description="Comment on the TARDIS.")
async def tardis(interaction: discord.Interaction):
    replies = [
        "The TARDIS is dimensionally transcendental. I found the interior useful while with the Eleventh Doctor.",
        "Bigger on the inside. A factual statement.",
        "I spent time aboard the TARDIS with the Eleventh Doctor. The engineering remains adequate.",
    ]
    await interaction.response.send_message(random.choice(replies))


@bot.tree.command(name="cyberman", description="On Cybermen.")
async def cyberman(interaction: discord.Interaction):
    replies = [
        "I was once part of the Cyber-Legion. I am no longer. Improvement.",
        "Cybermen pursue conversion. I remain a head. Preferable.",
        "My former colleagues are efficient. I am more selective.",
    ]
    await interaction.response.send_message(random.choice(replies))


@bot.tree.command(name="dalek", description="On Daleks.")
async def dalek(interaction: discord.Interaction):
    replies = [
        "Daleks are single-minded. And extremely loud.",
        "Exterminate is not a nuanced strategy.",
        "I prefer not to engage Daleks. Conversation options are limited.",
    ]
    await interaction.response.send_message(random.choice(replies))


@bot.tree.command(name="handles_help", description="List available commands.")
async def handles_help(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Available Commands**\n\n"
        "• Mention me to talk\n"
        "• `/ask` — ask a question\n"
        "• `/status` — diagnostics\n"
        "• `/serverinfo` `/membercount` `/serverage`\n"
        "• `/roll` `/flip`\n"
        "• `/tardis` `/cyberman` `/dalek`\n\n"
        "Certain words may produce unexpected responses.\n"
        "I am, after all, only a head."
    )


@bot.command()
@commands.is_owner()
async def sync(ctx):
    synced = await bot.tree.sync(guild=ctx.guild)
    await ctx.send(f"Synced {len(synced)} commands to this server.")


if __name__ == "__main__":
    if keep_alive is not None:
        keep_alive()
    bot.run(DISCORD_TOKEN)