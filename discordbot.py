#!/usr/bin/env python3
"""
Akhilesh Discord Manager Bot — AI-Agentic Edition
Powered by Grok (xAI) for intelligent server management.
Say: !do make this server like a friends group
"""

import discord
from discord.ext import commands
import asyncio, json, os, re, httpx, yt_dlp, glob, struct, io, wave
from datetime import datetime, timezone, timedelta
from collections import deque

# ── Config — set these in your environment or a .env file ─────────────────────
BOT_TOKEN  = os.environ["BOT_TOKEN"]          # Discord bot token
XAI_KEY    = os.environ["XAI_KEY"]            # xAI / Grok API key
XAI_MODEL  = os.environ.get("XAI_MODEL", "grok-3-latest")
PREFIX     = os.environ.get("PREFIX", "!")
LOG_FILE   = os.environ.get("LOG_FILE", "/var/log/discordbot.log")
WARNS_FILE = os.environ.get("WARNS_FILE", "warnings.json")
OWNER_ID   = int(os.environ["OWNER_ID"])      # Discord user ID of the owner
TMP_DIR    = os.environ.get("TMP_DIR", "/tmp/discordmusic")

# ── Logging ───────────────────────────────────────────────────────────────────
def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ── Grok AI ───────────────────────────────────────────────────────────────────
async def ask_grok(prompt: str, system: str = None, json_mode: bool = False) -> str:
    sys_msg = system or (
        "You are an intelligent Discord server management AI. "
        "You help manage Discord servers by chatting with users and executing real actions. "
        "Be concise and use Discord markdown (bold, code blocks, etc)."
    )
    payload = {
        "model": XAI_MODEL,
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user",   "content": prompt},
        ],
        "temperature": 0.3 if json_mode else 0.7,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {XAI_KEY}", "Content-Type": "application/json"},
            json=payload,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

# ── Warnings DB ───────────────────────────────────────────────────────────────
def load_warns():
    try:
        with open(WARNS_FILE) as f: return json.load(f)
    except: return {}

def save_warns(data):
    os.makedirs(os.path.dirname(WARNS_FILE), exist_ok=True)
    with open(WARNS_FILE, "w") as f: json.dump(data, f, indent=2)

warnings_db = load_warns()

# ── Bot setup ─────────────────────────────────────────────────────────────────
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ── Events ────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    os.makedirs(TMP_DIR, exist_ok=True)
    log(f"Discord bot online: {bot.user} ({bot.user.id})")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="the server | !do anything")
    )

@bot.event
async def on_member_join(member):
    for ch_name in ("welcome", "general", "lobby", "chat", "👋-welcome"):
        ch = discord.utils.get(member.guild.text_channels, name=ch_name)
        if not ch:
            ch = discord.utils.find(lambda c: "welcome" in c.name.lower() or "general" in c.name.lower(),
                                    member.guild.text_channels)
        if ch:
            embed = discord.Embed(
                title=f"👋 Welcome, {member.display_name}!",
                description=f"Welcome to **{member.guild.name}**!\nYou are member **#{member.guild.member_count}**. Make yourself at home!",
                color=0x5865F2,
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await ch.send(embed=embed)
            break

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to do that.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument. Try `!help {ctx.command}`.")
    elif isinstance(error, commands.CheckFailure):
        if ctx.command and ctx.command.name in ("do", "ai"):
            await ctx.send("❌ This command is restricted to the server owner only.")
        else:
            await ctx.send("❌ You don't have permission to use this command.")
    else:
        log(f"Error in !{ctx.command}: {error}")

# ── Permission helpers ────────────────────────────────────────────────────────
def is_owner():
    async def pred(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(pred)

def is_admin():
    async def pred(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(pred)

def is_mod():
    async def pred(ctx):
        p = ctx.author.guild_permissions
        return p.administrator or p.kick_members or p.ban_members or p.manage_messages
    return commands.check(pred)

# ═══════════════════════════════════════════════════════════════════════════════
#  !do — NATURAL LANGUAGE SERVER MANAGEMENT (the main feature)
# ═══════════════════════════════════════════════════════════════════════════════
@bot.command(name="do")
@is_owner()
async def do_cmd(ctx, *, instruction: str):
    """AI executes any server management task from natural language."""

    # Snapshot current server state
    guild = ctx.guild
    current_state = {
        "server_name": guild.name,
        "categories": [
            {
                "name": cat.name,
                "id": cat.id,
                "channels": [
                    {"name": ch.name, "id": ch.id, "type": str(ch.type)}
                    for ch in cat.channels
                ]
            }
            for cat in guild.categories
        ],
        "uncategorized_channels": [
            {"name": ch.name, "id": ch.id, "type": str(ch.type)}
            for ch in guild.channels if not ch.category and not isinstance(ch, discord.CategoryChannel)
        ],
        "roles": [
            {"name": r.name, "id": r.id, "color": str(r.color)}
            for r in guild.roles if r.name != "@everyone"
        ],
        "member_count": guild.member_count,
    }

    status_msg = await ctx.send("🧠 **Grok is planning your changes…**")

    system_prompt = """You are an expert Discord server manager AI.
You receive a server's current state and a user instruction.
You must output a JSON plan of actions to execute.

AVAILABLE ACTIONS:
- {"action": "rename_server", "name": "New Name"}
- {"action": "create_category", "name": "Category Name", "position": 0}
- {"action": "delete_category", "id": 123456}
- {"action": "rename_category", "id": 123456, "name": "New Name"}
- {"action": "create_text_channel", "name": "channel-name", "category_name": "Category Name", "topic": "optional topic"}
- {"action": "create_voice_channel", "name": "Channel Name", "category_name": "Category Name"}
- {"action": "delete_channel", "id": 123456}
- {"action": "rename_channel", "id": 123456, "name": "new-name"}
- {"action": "create_role", "name": "Role Name", "color": "#FF5733", "hoist": true}
- {"action": "delete_role", "id": 123456}
- {"action": "rename_role", "id": 123456, "name": "New Name"}

RULES:
- Return ONLY valid JSON with key "actions" (array) and "summary" (string explaining what you did)
- For "friends group" style: casual names, fun emojis, categories like hangout/gaming/media/voice etc
- Never delete @everyone role
- Use lowercase-with-dashes for text channel names
- Keep it practical — don't create too many channels (8-15 is ideal)
- If redesigning, you can delete old channels and create new ones"""

    user_prompt = f"""Current server state:
{json.dumps(current_state, indent=2)}

User instruction: {instruction}

Generate the JSON action plan."""

    try:
        raw = await ask_grok(user_prompt, system=system_prompt, json_mode=True)
        plan = json.loads(raw)
    except Exception as e:
        await status_msg.edit(content=f"❌ AI planning failed: {e}")
        return

    actions = plan.get("actions", [])
    summary = plan.get("summary", "Server redesign planned.")

    if not actions:
        await status_msg.edit(content=f"🤔 Grok says: {summary}\n\nNo changes needed.")
        return

    # Show plan and ask for confirmation
    action_lines = []
    for a in actions[:20]:
        act = a.get("action", "?")
        if act == "create_category":     action_lines.append(f"📁 Create category: **{a.get('name')}**")
        elif act == "delete_category":   action_lines.append(f"🗑️ Delete category ID: {a.get('id')}")
        elif act == "rename_category":   action_lines.append(f"✏️ Rename category → **{a.get('name')}**")
        elif act == "create_text_channel":action_lines.append(f"💬 Create #**{a.get('name')}** in {a.get('category_name','?')}")
        elif act == "create_voice_channel":action_lines.append(f"🔊 Create voice: **{a.get('name')}**")
        elif act == "delete_channel":    action_lines.append(f"🗑️ Delete channel ID: {a.get('id')}")
        elif act == "rename_channel":    action_lines.append(f"✏️ Rename channel → **{a.get('name')}**")
        elif act == "create_role":       action_lines.append(f"🎭 Create role: **{a.get('name')}**")
        elif act == "delete_role":       action_lines.append(f"🗑️ Delete role ID: {a.get('id')}")
        elif act == "rename_role":       action_lines.append(f"✏️ Rename role → **{a.get('name')}**")
        elif act == "rename_server":     action_lines.append(f"🏷️ Rename server → **{a.get('name')}**")

    plan_text = "\n".join(action_lines[:15])
    if len(actions) > 15:
        plan_text += f"\n*...and {len(actions)-15} more actions*"

    confirm_embed = discord.Embed(
        title="📋 Grok's Plan — Confirm?",
        description=f"**{summary}**\n\n{plan_text}",
        color=0xFF9933,
    )
    confirm_embed.set_footer(text="Reply ✅ yes  or  ❌ no  within 30 seconds")
    await status_msg.edit(content=None, embed=confirm_embed)

    # Wait for yes/no
    def check(m):
        return (m.author == ctx.author and m.channel == ctx.channel
                and m.content.lower() in ("yes", "no", "y", "n", "✅", "❌"))

    try:
        reply = await bot.wait_for("message", timeout=30.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send("⏰ Timed out. No changes made.")
        return

    if reply.content.lower() in ("no", "n", "❌"):
        await ctx.send("❌ Cancelled. No changes made.")
        return

    # Execute the plan
    progress = await ctx.send(f"⚙️ Executing {len(actions)} actions…")
    done, failed = 0, 0

    for action in actions:
        try:
            act = action.get("action")

            if act == "rename_server":
                await guild.edit(name=action["name"])

            elif act == "create_category":
                await guild.create_category(
                    name=action["name"],
                    position=action.get("position", 99),
                )

            elif act == "delete_category":
                cat = guild.get_channel(action["id"])
                if cat:
                    await cat.delete()

            elif act == "rename_category":
                cat = guild.get_channel(action["id"])
                if cat:
                    await cat.edit(name=action["name"])

            elif act == "create_text_channel":
                cat = discord.utils.get(guild.categories, name=action.get("category_name"))
                await guild.create_text_channel(
                    name=action["name"],
                    category=cat,
                    topic=action.get("topic", ""),
                )

            elif act == "create_voice_channel":
                cat = discord.utils.get(guild.categories, name=action.get("category_name"))
                await guild.create_voice_channel(
                    name=action["name"],
                    category=cat,
                )

            elif act == "delete_channel":
                ch = guild.get_channel(action["id"])
                if ch:
                    await ch.delete()

            elif act == "rename_channel":
                ch = guild.get_channel(action["id"])
                if ch:
                    await ch.edit(name=action["name"])

            elif act == "create_role":
                color_hex = action.get("color", "#99AAB5").lstrip("#")
                color = discord.Color(int(color_hex, 16)) if color_hex else discord.Color.default()
                await guild.create_role(
                    name=action["name"],
                    color=color,
                    hoist=action.get("hoist", False),
                    mentionable=action.get("mentionable", True),
                )

            elif act == "delete_role":
                role = guild.get_role(action["id"])
                if role and role.name != "@everyone":
                    await role.delete()

            elif act == "rename_role":
                role = guild.get_role(action["id"])
                if role and role.name != "@everyone":
                    await role.edit(name=action["name"])

            done += 1
            await asyncio.sleep(0.6)  # avoid Discord rate limits

        except Exception as e:
            log(f"Action failed ({action}): {e}")
            failed += 1
            await asyncio.sleep(1)

    result_embed = discord.Embed(
        title="✅ Done!",
        description=f"**{summary}**\n\n✅ {done} actions done · ❌ {failed} failed",
        color=0x57F287 if failed == 0 else 0xFF9933,
        timestamp=datetime.now(timezone.utc),
    )
    await progress.edit(content=None, embed=result_embed)
    log(f"!do by {ctx.author}: '{instruction}' — {done} done, {failed} failed")


# ═══════════════════════════════════════════════════════════════════════════════
#  !ai — Chat with Grok
# ═══════════════════════════════════════════════════════════════════════════════
@bot.command(name="ai")
@is_owner()
async def ai_cmd(ctx, *, question: str):
    async with ctx.typing():
        answer = await ask_grok(question)
    for chunk in [answer[i:i+1900] for i in range(0, len(answer), 1900)]:
        await ctx.send(chunk)
    log(f"!ai by {ctx.author}: {question[:60]}")


# ═══════════════════════════════════════════════════════════════════════════════
#  Moderation commands
# ═══════════════════════════════════════════════════════════════════════════════
@bot.command(name="kick")
@is_mod()
async def kick_cmd(ctx, member: discord.Member, *, reason: str = "No reason given"):
    if member.top_role >= ctx.author.top_role and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ You can't kick someone with equal or higher role.")
    await member.kick(reason=f"{ctx.author}: {reason}")
    e = discord.Embed(title="👢 Kicked", color=0xFF5733)
    e.add_field(name="User", value=f"{member}"); e.add_field(name="Reason", value=reason)
    await ctx.send(embed=e)

@bot.command(name="ban")
@is_mod()
async def ban_cmd(ctx, member: discord.Member, *, reason: str = "No reason given"):
    if member.top_role >= ctx.author.top_role and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ You can't ban someone with equal or higher role.")
    await member.ban(reason=f"{ctx.author}: {reason}", delete_message_days=1)
    e = discord.Embed(title="🔨 Banned", color=0xCC0000)
    e.add_field(name="User", value=f"{member}"); e.add_field(name="Reason", value=reason)
    await ctx.send(embed=e)

@bot.command(name="unban")
@is_admin()
async def unban_cmd(ctx, user_id: int):
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ **{user}** unbanned.")
    except discord.NotFound:
        await ctx.send("❌ User not found or not banned.")

@bot.command(name="mute")
@is_mod()
async def mute_cmd(ctx, member: discord.Member, minutes: int = 10, *, reason: str = "No reason"):
    await member.timeout(timedelta(minutes=minutes), reason=reason)
    await ctx.send(f"🔇 **{member.display_name}** muted for {minutes} min. Reason: {reason}")

@bot.command(name="unmute")
@is_mod()
async def unmute_cmd(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"✅ **{member.display_name}** unmuted.")

@bot.command(name="warn")
@is_mod()
async def warn_cmd(ctx, member: discord.Member, *, reason: str = "No reason given"):
    uid = str(member.id)
    if uid not in warnings_db: warnings_db[uid] = []
    warnings_db[uid].append({"reason": reason, "by": str(ctx.author), "at": datetime.now(timezone.utc).isoformat()})
    save_warns(warnings_db)
    count = len(warnings_db[uid])
    await ctx.send(f"⚠️ **{member.display_name}** warned ({count} total). Reason: {reason}")
    if count >= 3:
        await member.timeout(timedelta(hours=1), reason=f"Auto-muted: {count} warnings")
        await ctx.send(f"🔇 Auto-muted for 1 hour (3+ warnings).")
    try: await member.send(f"⚠️ Warning in **{ctx.guild.name}**: {reason} (Warning #{count})")
    except: pass

@bot.command(name="warnings")
async def warnings_cmd(ctx, member: discord.Member = None):
    member = member or ctx.author
    w = warnings_db.get(str(member.id), [])
    if not w: return await ctx.send(f"✅ **{member.display_name}** has no warnings.")
    e = discord.Embed(title=f"⚠️ Warnings for {member.display_name}", color=0xFFCC00)
    for i, warn in enumerate(w[-5:], 1):
        e.add_field(name=f"#{i}", value=f"{warn['reason']} — by {warn['by']}", inline=False)
    e.set_footer(text=f"Total: {len(w)}")
    await ctx.send(embed=e)

@bot.command(name="clear")
@is_mod()
async def clear_cmd(ctx, amount: int = 10):
    deleted = await ctx.channel.purge(limit=min(amount, 100) + 1)
    m = await ctx.send(f"🗑️ Deleted **{len(deleted)-1}** messages.")
    await asyncio.sleep(3); await m.delete()

@bot.command(name="slowmode")
@is_mod()
async def slowmode_cmd(ctx, seconds: int = 0):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"✅ Slowmode {'disabled' if seconds == 0 else f'set to {seconds}s'}.")

@bot.command(name="lock")
@is_mod()
async def lock_cmd(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    await ctx.send("🔒 Channel locked.")

@bot.command(name="unlock")
@is_mod()
async def unlock_cmd(ctx):
    ow = ctx.channel.overwrites_for(ctx.guild.default_role)
    ow.send_messages = None
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=ow)
    await ctx.send("🔓 Channel unlocked.")

@bot.command(name="announce")
@is_mod()
async def announce_cmd(ctx, *, message: str):
    e = discord.Embed(title="📢 Announcement", description=message, color=0x5865F2, timestamp=datetime.now(timezone.utc))
    e.set_footer(text=f"By {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await ctx.message.delete()
    await ctx.send(embed=e)

@bot.command(name="role")
@is_admin()
async def role_cmd(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role: return await ctx.send(f"❌ Role **{role_name}** not found.")
    await member.add_roles(role)
    await ctx.send(f"✅ Gave **{role.name}** to **{member.display_name}**.")

@bot.command(name="removerole")
@is_admin()
async def removerole_cmd(ctx, member: discord.Member, *, role_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role: return await ctx.send(f"❌ Role **{role_name}** not found.")
    await member.remove_roles(role)
    await ctx.send(f"✅ Removed **{role.name}** from **{member.display_name}**.")

@bot.command(name="serverinfo")
async def serverinfo_cmd(ctx):
    g = ctx.guild
    e = discord.Embed(title=f"📊 {g.name}", color=0x5865F2, timestamp=datetime.now(timezone.utc))
    if g.icon: e.set_thumbnail(url=g.icon.url)
    e.add_field(name="👑 Owner", value=str(g.owner))
    e.add_field(name="👥 Members", value=f"{g.member_count:,}")
    e.add_field(name="💬 Channels", value=f"{len(g.text_channels)} text · {len(g.voice_channels)} voice")
    e.add_field(name="🎭 Roles", value=str(len(g.roles)))
    e.add_field(name="📅 Created", value=g.created_at.strftime("%d %b %Y"))
    await ctx.send(embed=e)

@bot.command(name="userinfo")
async def userinfo_cmd(ctx, member: discord.Member = None):
    member = member or ctx.author
    e = discord.Embed(title=f"👤 {member.display_name}", color=member.color, timestamp=datetime.now(timezone.utc))
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="Username", value=str(member))
    e.add_field(name="ID", value=str(member.id))
    e.add_field(name="Joined", value=member.joined_at.strftime("%d %b %Y"))
    e.add_field(name="Registered", value=member.created_at.strftime("%d %b %Y"))
    roles = [r.mention for r in member.roles[1:]]
    e.add_field(name=f"Roles ({len(roles)})", value=" ".join(roles[:8]) or "None", inline=False)
    e.add_field(name="⚠️ Warnings", value=str(len(warnings_db.get(str(member.id), []))))
    await ctx.send(embed=e)

@bot.command(name="help")
async def help_cmd(ctx):
    e = discord.Embed(title="📖 Bot Commands", color=0x5865F2)
    e.add_field(name="🧠 AI Management", value=(
        "`!do [any instruction]` — **AI executes it on your server**\n"
        "*e.g. !do make this like a friends group server*\n"
        "*e.g. !do create a gaming section with 3 channels*\n"
        "*e.g. !do rename the server to Akhilesh Gang*"
    ), inline=False)
    e.add_field(name="🤖 Chat", value="`!ai [question]` — Ask Grok anything", inline=False)
    e.add_field(name="🛡️ Moderation", value="`!kick` `!ban` `!unban` `!mute` `!unmute` `!warn` `!warnings` `!clear`", inline=False)
    e.add_field(name="⚙️ Server", value="`!announce` `!slowmode` `!lock` `!unlock` `!role` `!removerole`", inline=False)
    e.add_field(name="ℹ️ Info", value="`!serverinfo` `!userinfo`", inline=False)
    e.add_field(name="🎵 Music", value=(
        "`!music [song]` — AI builds a playlist & plays it\n"
        "`!skip` `!stop` `!pause` `!resume`\n"
        "`!queue` / `!q`   `!np` (now playing)"
    ), inline=False)
    e.add_field(name="🎙️ Voice AI (Miss)", value=(
        "`!listen [question]` — Miss answers in e-girl voice\n"
        "*e.g. !listen roast me*\n"
        "*e.g. !listen say something cute*"
    ), inline=False)
    e.set_footer(text="!do and !ai are owner-only • Mod commands require Kick/Ban/Manage Messages")
    await ctx.send(embed=e)


# ═══════════════════════════════════════════════════════════════════════════════
#  MUSIC SYSTEM  — Download-first for glitch-free playback
#  Uses SoundCloud (no bot detection) via yt-dlp scsearch1: prefix
# ═══════════════════════════════════════════════════════════════════════════════

# Per-guild state  — queue stores {title, artist, search, webpage_url, duration, thumbnail}
music_queues    = {}   # guild_id → deque of track dicts
music_current   = {}   # guild_id → current track dict
music_text_ch   = {}   # guild_id → TextChannel for "now playing" messages
music_preloaded = {}   # guild_id → (track, local_path) pre-downloaded next song

# yt-dlp options — SoundCloud only, download to file
YTDL_SEARCH_OPTS = {
    "format":         "bestaudio/best",
    "quiet":          True,
    "no_warnings":    True,
    "noplaylist":     True,
    "socket_timeout": 30,
    "default_search": "scsearch",
}

def get_queue(guild_id):
    if guild_id not in music_queues:
        music_queues[guild_id] = deque()
    return music_queues[guild_id]

def _cleanup_file(path: str):
    """Delete a temp audio file, ignoring errors."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

async def search_track(query: str) -> dict | None:
    """
    Search SoundCloud for a track and return metadata (no download yet).
    """
    loop = asyncio.get_event_loop()
    try:
        search_query = f"scsearch1:{query}" if not query.startswith("http") else query
        with yt_dlp.YoutubeDL(YTDL_SEARCH_OPTS) as ydl:
            info = await loop.run_in_executor(
                None, lambda: ydl.extract_info(search_query, download=False)
            )
            if info and "entries" in info:
                info = info["entries"][0] if info["entries"] else None
            if not info:
                return None
            return {
                "title":       info.get("title", "Unknown"),
                "artist":      info.get("uploader", ""),
                "search":      query,
                "webpage_url": info.get("webpage_url", ""),
                "duration":    info.get("duration", 0),
                "thumbnail":   info.get("thumbnail", ""),
            }
    except Exception as e:
        log(f"search_track error for '{query}': {e}")
        return None

async def download_track(track: dict, gid: int) -> str | None:
    """
    Download the track to a local file in TMP_DIR.
    Returns the local file path, or None on failure.
    """
    loop = asyncio.get_event_loop()
    out_template = os.path.join(TMP_DIR, f"guild_{gid}_%(id)s.%(ext)s")
    dl_opts = {
        **YTDL_SEARCH_OPTS,
        "outtmpl":  out_template,
        "format":   "bestaudio[ext=opus]/bestaudio[ext=webm]/bestaudio/best",
    }

    try:
        search_query = track.get("webpage_url") or f"scsearch1:{track['search']}"

        def _do_download():
            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                info = ydl.extract_info(search_query, download=True)
                if info and "entries" in info:
                    info = info["entries"][0] if info["entries"] else None
                if not info:
                    return None
                # Figure out the actual filename yt-dlp wrote
                return ydl.prepare_filename(info)

        local_path = await loop.run_in_executor(None, _do_download)
        if local_path and os.path.exists(local_path):
            log(f"Downloaded: {track['title']} → {local_path}")
            return local_path

        # yt-dlp might have changed extension — scan the folder
        base = os.path.splitext(out_template.replace("%(id)s", "*").replace("%(ext)s", "*"))[0]
        matches = glob.glob(os.path.join(TMP_DIR, f"guild_{gid}_*.*"))
        # Return newest file in TMP_DIR for this guild
        matches = sorted(matches, key=os.path.getmtime, reverse=True)
        if matches:
            return matches[0]

        return None

    except Exception as e:
        log(f"download_track error for '{track.get('title')}': {e}")
        return None

async def play_next(guild: discord.Guild):
    """
    Pop next track from queue, play it.
    Uses pre-downloaded file if available, otherwise downloads fresh.
    While playing, pre-downloads the next song in the background.
    """
    gid   = guild.id
    queue = get_queue(gid)
    vc    = guild.voice_client
    text  = music_text_ch.get(gid)

    if not vc or not vc.is_connected():
        return

    if not queue:
        music_current[gid] = None
        music_preloaded.pop(gid, None)
        if text:
            await text.send("✅ Queue finished! Type `!music [song]` to play more.")
        return

    track = queue.popleft()
    music_current[gid] = track

    # Use pre-downloaded file if it's for this track
    preloaded = music_preloaded.pop(gid, None)
    if preloaded and preloaded[0].get("search") == track.get("search"):
        local_path = preloaded[1]
        log(f"Using pre-downloaded file for: {track['title']}")
    else:
        # Clean up stale preload if any
        if preloaded:
            _cleanup_file(preloaded[1])
        # Download now
        if text:
            dl_msg = await text.send(f"⏳ Downloading **{track['title']}**…")
        else:
            dl_msg = None
        local_path = await download_track(track, gid)
        if dl_msg:
            try: await dl_msg.delete()
            except: pass

    if not local_path:
        log(f"Could not download: {track['title']}, skipping")
        if text:
            await text.send(f"⚠️ Couldn't load **{track['title']}**, skipping…")
        await play_next(guild)
        return

    # Send "Now Playing" embed
    if text:
        mins, secs = divmod(int(track.get("duration") or 0), 60)
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{track['title']}**" + (f" — {track.get('artist')}" if track.get("artist") else ""),
            color=0x1DB954,
        )
        embed.add_field(name="⏱️ Duration", value=f"{mins}:{secs:02d}" if track.get("duration") else "—")
        embed.add_field(name="📋 Queue", value=f"{len(queue)} left")
        if track.get("thumbnail"):
            embed.set_thumbnail(url=track["thumbnail"])
        await text.send(embed=embed)

    # Pre-download the next track in the background while this one plays
    async def preload_next():
        if queue:
            next_track = queue[0]  # peek without popping
            log(f"Pre-downloading next: {next_track['title']}")
            path = await download_track(next_track, gid)
            if path:
                music_preloaded[gid] = (next_track, path)

    asyncio.create_task(preload_next())

    # Play from the local file
    def after_play(error):
        if error:
            log(f"Playback error: {error}")
        # Delete the temp file we just played
        _cleanup_file(local_path)
        asyncio.run_coroutine_threadsafe(play_next(guild), bot.loop)

    try:
        source = discord.FFmpegOpusAudio(local_path)
        vc.play(source, after=after_play)
    except Exception as e:
        log(f"FFmpeg play error: {e}")
        _cleanup_file(local_path)
        if text:
            await text.send(f"❌ Error playing **{track['title']}**, skipping…")
        await play_next(guild)


@bot.command(name="music")
async def music_cmd(ctx, *, query: str = None):
    """!music [song] — Grok builds an AI playlist and plays it."""

    if not query:
        embed = discord.Embed(
            title="🎵 Music Bot",
            description=(
                "**Usage:** `!music [song name or mood]`\n\n"
                "**Examples:**\n"
                "`!music Stay`\n"
                "`!music sad hindi songs`\n"
                "`!music chill lofi beats`\n"
                "`!music Arijit Singh romantic`"
            ),
            color=0x1DB954,
        )
        return await ctx.send(embed=embed)

    if not ctx.author.voice:
        return await ctx.send("❌ **Join a voice channel first**, then use `!music`.")

    vc = ctx.guild.voice_client
    if vc and vc.channel != ctx.author.voice.channel:
        await vc.move_to(ctx.author.voice.channel)
    elif not vc:
        try:
            vc = await ctx.author.voice.channel.connect()
        except Exception as e:
            return await ctx.send(f"❌ Couldn't join your voice channel: {e}")

    gid = ctx.guild.id
    music_text_ch[gid] = ctx.channel
    queue = get_queue(gid)

    thinking = await ctx.send(f"🧠 **Grok is building a playlist for** `{query}`…")

    # Ask Grok for similar songs
    grok_prompt = (
        f"User wants music like: \"{query}\".\n"
        f"Create a playlist of 8 songs with the same vibe, genre, mood, and language.\n"
        f"If it's a specific song, include it first. If it's a mood/genre, pick the best 8.\n"
        f"Return ONLY a JSON object with key \"songs\" — array of {{\"title\": ..., \"artist\": ...}}.\n"
        f"Example: {{\"songs\": [{{\"title\": \"Stay\", \"artist\": \"The Kid LAROI ft. Justin Bieber\"}}]}}"
    )
    try:
        raw  = await ask_grok(grok_prompt, json_mode=True)
        data = json.loads(raw)
        playlist = (
            data.get("songs") or data.get("playlist") or
            (data if isinstance(data, list) else list(data.values())[0])
        )
        if not isinstance(playlist, list):
            raise ValueError("Bad format")
    except Exception as e:
        log(f"Grok playlist error: {e}")
        playlist = [{"title": query, "artist": ""}]

    playlist = playlist[:8]

    # Show playlist embed
    song_list = "\n".join(
        f"`{i+1}.` **{s.get('title','?')}** — {s.get('artist','?')}"
        for i, s in enumerate(playlist)
    )
    embed = discord.Embed(title=f"🎵 AI Playlist — {query}", description=song_list, color=0x1DB954)
    embed.set_footer(text="⏳ Searching & queuing songs…")
    await thinking.edit(content=None, embed=embed)

    # Background: search + queue all tracks, start playing when first is ready
    async def fetch_and_queue():
        fetched = 0
        for song in playlist:
            search = f"{song.get('title', '')} {song.get('artist', '')}".strip()
            track  = await search_track(search)
            if track:
                queue.append(track)
                fetched += 1
                # Start playing as soon as first track is queued
                if fetched == 1 and not (vc.is_playing() or vc.is_paused()):
                    await play_next(guild=ctx.guild)
            await asyncio.sleep(0.3)

        try:
            await ctx.send(f"✅ **{fetched}/{len(playlist)}** songs queued.")
        except Exception:
            pass

    asyncio.create_task(fetch_and_queue())


@bot.command(name="skip")
async def skip_cmd(ctx):
    vc = ctx.guild.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop()
        await ctx.send("⏭️ Skipped.")
    else:
        await ctx.send("❌ Nothing is playing.")

@bot.command(name="stop")
async def stop_cmd(ctx):
    gid = ctx.guild.id
    vc  = ctx.guild.voice_client
    get_queue(gid).clear()
    music_current[gid] = None
    # Clean up any preloaded file
    preloaded = music_preloaded.pop(gid, None)
    if preloaded:
        _cleanup_file(preloaded[1])
    if vc:
        await vc.disconnect()
    await ctx.send("⏹️ Stopped and left the voice channel.")

@bot.command(name="pause")
async def pause_cmd(ctx):
    vc = ctx.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send("⏸️ Paused.")
    else:
        await ctx.send("❌ Nothing is playing.")

@bot.command(name="resume")
async def resume_cmd(ctx):
    vc = ctx.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await ctx.send("▶️ Resumed.")
    else:
        await ctx.send("❌ Nothing is paused.")

@bot.command(name="queue", aliases=["q"])
async def queue_cmd(ctx):
    gid   = ctx.guild.id
    queue = get_queue(gid)
    cur   = music_current.get(gid)

    if not cur and not queue:
        return await ctx.send("📭 Queue is empty. Use `!music [song]` to start.")

    embed = discord.Embed(title="📋 Music Queue", color=0x1DB954)
    if cur:
        embed.add_field(
            name="🎵 Now Playing",
            value=f"**{cur['title']}**" + (f" — {cur.get('artist')}" if cur.get("artist") else ""),
            inline=False,
        )
    if queue:
        lines = "\n".join(f"`{i+1}.` {t['title']}" for i, t in enumerate(list(queue)[:10]))
        if len(queue) > 10:
            lines += f"\n*...and {len(queue)-10} more*"
        embed.add_field(name="⏭️ Up Next", value=lines, inline=False)
    await ctx.send(embed=embed)

@bot.command(name="nowplaying", aliases=["np"])
async def nowplaying_cmd(ctx):
    cur = music_current.get(ctx.guild.id)
    if not cur:
        return await ctx.send("❌ Nothing is playing right now.")
    mins, secs = divmod(int(cur.get("duration") or 0), 60)
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"**{cur['title']}**" + (f" — {cur.get('artist')}" if cur.get("artist") else ""),
        color=0x1DB954,
    )
    embed.add_field(name="⏱️ Duration", value=f"{mins}:{secs:02d}" if cur.get("duration") else "—")
    if cur.get("thumbnail"):
        embed.set_thumbnail(url=cur["thumbnail"])
    await ctx.send(embed=embed)

# ═══════════════════════════════════════════════════════════════════════════════
#  VOICE ASSISTANT — !listen [question] → Grok AI → Fish Audio e-girl TTS → plays in voice
# ═══════════════════════════════════════════════════════════════════════════════

FISH_KEY_VA   = os.environ["FISH_KEY"]         # Fish Audio API key
FISH_EGIRL_ID = os.environ.get("FISH_VOICE_ID", "98655a12fa944e26b274c535e5e03842")  # Fish Audio voice ID

_VA_TAG_REMAP = {
    "[laughter]": "[laugh]", "[laughing]": "[laugh]",
    "[whispered]": "[whisper]", "[whispering]": "[whisper]",
    "[breathing]": "[breath]",
    "[crying]": "[sad]", "[cry]": "[sad]",
    "[excited]": "[emphasis]", "[intense]": "[emphasis]", "[angry]": "[emphasis]",
    "[nervous]": "[soft]",
}

EGIRL_SYSTEM = (
    "You are Miss, an AI e-girl voice assistant in a Discord voice channel. "
    "You have a bubbly, playful, flirty e-girl personality — casual, cute, expressive. "
    "Keep ALL responses SHORT — 1 to 3 sentences max. You are being read aloud by a TTS voice.\n\n"
    "Use these emotion tags naturally in your response:\n"
    "[laugh] — laughter  [whisper] — whisper effect  [sigh] — audible sigh\n"
    "[emphasis] — vocal stress  [soft] — quiet intimate  [sad] — heavy tone  [pause] — brief silence\n\n"
    "Example: 'omg [laugh] that's literally so funny!! [soft] but okay okay, here's the thing... [pause] you're kinda right.'\n\n"
    "Rules: SHORT responses only. No markdown, no asterisks, no emojis. Sound natural when spoken."
)


async def _egirl_tts(text: str) -> bytes:
    """Generate MP3 audio from text using Fish Audio Egirl voice."""
    for wrong, right in _VA_TAG_REMAP.items():
        text = text.replace(wrong, right)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.fish.audio/v1/tts",
                headers={"Authorization": f"Bearer {FISH_KEY_VA}", "Content-Type": "application/json"},
                json={
                    "text": text, "reference_id": FISH_EGIRL_ID,
                    "format": "mp3", "mp3_bitrate": 128,
                    "normalize": True, "latency": "normal",
                },
            )
            r.raise_for_status()
            return r.content
    except Exception as e:
        log(f"[Miss] TTS error: {e}")
        return b""


@bot.command(name="listen")
async def listen_cmd(ctx, *, question: str = None):
    """!listen [question] — Miss answers you in voice using an e-girl AI voice."""

    if not question:
        embed = discord.Embed(
            title="🎙️ Miss — Voice AI",
            description=(
                "**Usage:** `!listen [your question]`\n\n"
                "**Examples:**\n"
                "`!listen tell me something interesting`\n"
                "`!listen what is the meaning of life`\n"
                "`!listen roast me`\n"
                "`!listen say something cute`"
            ),
            color=0xFF69B4,
        )
        return await ctx.send(embed=embed)

    if not ctx.author.voice:
        return await ctx.send("❌ Join a voice channel first, then use `!listen`.")

    # Join or move to user's voice channel
    vc = ctx.guild.voice_client
    if vc and vc.channel != ctx.author.voice.channel:
        await vc.move_to(ctx.author.voice.channel)
    elif not vc:
        try:
            vc = await ctx.author.voice.channel.connect()
        except Exception as e:
            return await ctx.send(f"❌ Couldn't join your channel: {e}")

    # Don't interrupt if Miss is already speaking
    if vc.is_playing():
        return await ctx.send("⏳ Miss is still talking, wait a moment~")

    thinking = await ctx.send(f"💭 *Miss is thinking…*")

    # Get Grok e-girl response
    try:
        reply = await ask_grok(question, system=EGIRL_SYSTEM)
    except Exception as e:
        await thinking.edit(content=f"❌ Grok error: {e}")
        return

    # Generate Fish Audio TTS
    mp3 = await _egirl_tts(reply)
    if not mp3:
        await thinking.edit(content="❌ TTS generation failed.")
        return

    # Save to temp file and play
    tts_path = os.path.join(TMP_DIR, f"miss_tts_{ctx.guild.id}.mp3")
    with open(tts_path, "wb") as f:
        f.write(mp3)

    # Pause music if playing
    music_was_playing = vc.is_playing()
    if music_was_playing:
        vc.pause()

    done_evt = asyncio.Event()
    def _after(err):
        _cleanup_file(tts_path)
        done_evt.set()
        if music_was_playing:
            asyncio.run_coroutine_threadsafe(_resume_music(vc), bot.loop)

    async def _resume_music(vc):
        if vc.is_paused():
            vc.resume()

    vc.play(discord.FFmpegPCMAudio(tts_path), after=_after)

    await thinking.edit(content=f"💬 **Miss:** {reply}")
    log(f"[Miss] {ctx.author.name}: {question} → {reply[:60]}")


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("/opt/discordbot", exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)
    log("Starting Discord Manager Bot (Grok-powered)…")
    bot.run(BOT_TOKEN)
