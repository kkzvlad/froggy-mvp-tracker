# ============================================================
# BLOCK 1 — IMPORTS
# ============================================================

import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz
import asyncio
from bot.database import init_db, create_or_update_timer, get_active_timers, delete_timer, get_timer_by_name, update_notification_flag


# ============================================================
# BLOCK 2 — ENV / TOKEN
# ============================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV")
DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))
ALERT_CHANNEL_ID = int(os.getenv("ALERT_CHANNEL_ID"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/bot.sqlite")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ============================================================
# BLOCK 3 — MVP DATABASE
# Тут поки зберігаємо MVP вручну в кодіВ
# cooldown = скільки хвилин MVP точно не буде
# window = скільки хвилин триває вікно респу
# ============================================================

MVP_DATA = {
    1832: {
        "name": "Ifrit",
        "cooldown": 660,
        "window": 10,
        "maps": ["thor_v03"],
        "image": "https://file5s.ratemyserver.net/mobs/1832.gif"
    },
    1751: {
        "name": "Valkyrie Randgris",
        "cooldown": 480,
        "window": 10,
        "maps": ["odin_tem03"],
        "image": "https://file5s.ratemyserver.net/mobs/1751.gif"
    },
    1583: {
        "name": "Tao Gunka",
        "cooldown": 300,
        "window": 10,
        "maps": ["beach_dun", "cmd_fild03"],
        "image": "https://file5s.ratemyserver.net/mobs/1583.gif"
    },
    1059: {
        "name": "Mistress",
        "cooldown": 120,
        "window": 10,
        "maps": ["mjolnir_04"],
        "image": "https://file5s.ratemyserver.net/mobs/1059.gif"
    },
    1389: {
        "name": "Dracula",
        "cooldown": 60,
        "window": 10,
        "maps": ["gef_dun01"],
        "image": "https://file5s.ratemyserver.net/mobs/1389.gif"
    },
    1150: {
        "name": "Moonlight Flower",
        "cooldown": 60,
        "window": 10,
        "maps": ["pay_dun04"],
        "image": "https://file5s.ratemyserver.net/mobs/1150.gif"
    },
    1086: {
        "name": "Golden Thief Bug",
        "cooldown": 60,
        "window": 10,
        "maps": ["prt_sewb4"],
        "image": "https://file5s.ratemyserver.net/mobs/1086.gif"
    },
    1272: {
        "name": "Dark Lord",
        "cooldown": 60,
        "window": 10,
        "maps": ["gl_chyard"],
        "image": "https://file5s.ratemyserver.net/mobs/1272.gif"
    },
    1087: {
        "name": "Orc Hero",
        "cooldown": 60,
        "window": 10,
        "maps": ["gef_fild14"],
        "image": "https://file5s.ratemyserver.net/mobs/1087.gif"
    },
    1492: {
        "name": "Incantation Samurai / Samurai Specter",
        "cooldown": 91,
        "window": 10,
        "maps": ["ama_dun03"],
        "image": "https://file5s.ratemyserver.net/mobs/1492.gif"
    },
    1115: {
        "name": "Eddga",
        "cooldown": 120,
        "window": 10,
        "maps": ["pay_fild11"],
        "image": "https://file5s.ratemyserver.net/mobs/1115.gif"
    },
    1159: {
        "name": "Phreeoni",
        "cooldown": 120,
        "window": 10,
        "maps": ["moc_fild17"],
        "image": "https://file5s.ratemyserver.net/mobs/1159.gif"
    },
    1623: {
        "name": "RSX-0806",
        "cooldown": 125,
        "window": 10,
        "maps": ["ein_dun02"],
        "image": "https://file5s.ratemyserver.net/mobs/1623.gif"
    },
    1688: {
        "name": "Lady Tanee",
        "cooldown": 420,
        "window": 10,
        "maps": ["ayo_dun02"],
        "image": "https://file5s.ratemyserver.net/mobs/1688.gif"
    },
    1688: {
        "name": "Lady Tanee",
        "cooldown": 420,
        "window": 10,
        "maps": ["ayo_dun02"],
        "image": "https://file5s.ratemyserver.net/mobs/1688.gif"
    },
    1917: {
        "name": "Wounded Morocc",
        "cooldown": 720,
        "window": 10,
        "maps": ["moc_fild22"],
        "image": "https://file5s.ratemyserver.net/mobs/1917.gif"
    },
    2476: {
        "name": "Amdarais",
        "cooldown": 720,
        "window": 10,
        "maps": ["2@gl_k(1)"],
        "image": "https://file5s.ratemyserver.net/mobs/2476.gif"
    },
    2475: {
        "name": "Corrupted Soul / Root of Corruption",
        "cooldown": 720,
        "window": 10,
        "maps": ["1@gl_k(1)"],
        "image": "https://file5s.ratemyserver.net/mobs/2475.gif"
    },
    1874: {
        "name": "Beelzebub",
        "cooldown": 720,
        "window": 10,
        "maps": ["abbey03"],
        "image": "https://file5s.ratemyserver.net/mobs/1874.gif"
    },
    1641: {
        "name": "Assassin Cross Eremes [MiniBoss]",
        "cooldown": 43,
        "window": 39,
        "maps": ["lhz_dun03"],
        "image": "https://file5s.ratemyserver.net/mobs/1641.gif"
    },
    2018-1: {
        "name": "Duneyrr #1",
        "cooldown": 15,
        "window": 0,
        "maps": ["nyd_dun01"],
        "image": "https://file5s.ratemyserver.net/mobs/2018.gif"
    },
    2018-2: {
        "name": "Duneyrr #2",
        "cooldown": 15,
        "window": 0,
        "maps": ["nyd_dun01"],
        "image": "https://file5s.ratemyserver.net/mobs/2018.gif"
    }
}


# =========================================================
# BLOCK 4 — BACKGROUND TASKS
# =========================================================

notification_task = None

# ============================================================
# BLOCK 5 — AUTOCOMPLETE
# Підказки MVP при вводі команди /mvp_add
# Працює по назві або ID
# ============================================================

async def mvp_autocomplete(interaction: discord.Interaction, current: str):
    results = []

    for mvp_id, mvp in MVP_DATA.items():
        name = mvp["name"]

        if current.lower() in name.lower() or current in str(mvp_id):
            results.append(
                app_commands.Choice(
                    name=f"{name} (ID: {mvp_id})",
                    value=str(mvp_id)
                )
            )

    return results[:25]


# ============================================================
# BLOCK 5.1 — MAP AUTOCOMPLETE
# Підказки мап для параметра map_name
# ============================================================

async def map_autocomplete(interaction: discord.Interaction, current: str):
    results = []

    # Беремо вже вибране значення поля name
    selected_name = interaction.namespace.name

    mvp = None

    if selected_name:
        if str(selected_name).isdigit():
            mvp = MVP_DATA.get(int(selected_name))
        else:
            for data in MVP_DATA.values():
                if data["name"].lower() == str(selected_name).lower():
                    mvp = data
                    break

    if not mvp:
        return []

    for map_name in mvp["maps"]:
        if current.lower() in map_name.lower():
            results.append(
                app_commands.Choice(
                    name=map_name,
                    value=map_name
                )
            )

    return results[:25]


# ============================================================
# BLOCK 6 — BOT INITIALIZATION
# ============================================================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ============================================================
# BLOCK 7 — BOT READY EVENT
# Синхронізує slash-команди при старті бота
# ============================================================

@bot.event
async def on_ready():
    global notification_task

    print(f"Logged in as {bot.user}", flush=True)
    print(f"Environment: {ENVIRONMENT}", flush=True)
    print(f"Alert channel ID: {ALERT_CHANNEL_ID}", flush=True)
    print(f"Database path: {DATABASE_PATH}", flush=True)

    init_db()
    print(f"[{ENVIRONMENT}] Database initialized", flush=True)

    try:
        # Remove old global commands
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()

        # Sync guild commands
        guild = discord.Object(id=DISCORD_GUILD_ID)
        synced = await bot.tree.sync(guild=guild)

        print(
            f"Synced {len(synced)} commands for guild {DISCORD_GUILD_ID}",
            flush=True
        )

    except Exception as e:
        print(e, flush=True)

    if notification_task is None:
        notification_task = bot.loop.create_task(notification_loop())

# ============================================================
# BLOCK 8 — TEST COMMAND
# Команда для перевірки, що бот живий
# ============================================================

@bot.tree.command(
    name="ping",
    description="Test command",
    guild=discord.Object(id=DISCORD_GUILD_ID)
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🐸 Froggy is alive!")


# ============================================================
# BLOCK 9 — MVP ADD COMMAND
# Команда /mvp_add
# Підтримує вибір мапи
# ============================================================

@bot.tree.command(
    name="mvp_add",
    description="Add MVP kill timer",
    guild=discord.Object(id=DISCORD_GUILD_ID)
)
@app_commands.autocomplete(
    name=mvp_autocomplete,
    map_name=map_autocomplete
)
async def mvp_add(
    interaction: discord.Interaction,
    name: str,
    map_name: str = None
):
    await interaction.response.defer()

    # ---------- 9.1 Find MVP ----------
    mvp = None

    if name.isdigit():
        mvp = MVP_DATA.get(int(name))
    else:
        for data in MVP_DATA.values():
            if data["name"].lower() == name.lower():
                mvp = data
                break

    if not mvp:
        await interaction.followup.send(
            f"❌ MVP '{name}' not found",
            ephemeral=True
        )
        return

    # ---------- 9.2 Select map ----------
    available_maps = mvp["maps"]

    if len(available_maps) == 1:
        selected_map = available_maps[0]
    else:
        if not map_name:
            maps_list = ", ".join(available_maps)
            await interaction.followup.send(
                f"❌ This MVP has multiple locations. Please select a map:\n{maps_list}",
                ephemeral=True
            )
            return

        if map_name not in available_maps:
            maps_list = ", ".join(available_maps)
            await interaction.followup.send(
                f"❌ Invalid map.\nAvailable maps: {maps_list}",
                ephemeral=True
            )
            return

        selected_map = map_name

    # ---------- 9.3 Calculate respawn ----------
    now = datetime.now(pytz.timezone("Europe/Kyiv"))

    window_start = now + timedelta(minutes=mvp["cooldown"])
    window_end = window_start + timedelta(minutes=mvp["window"])

    # ---------- 9.4 Create embed ----------
    embed = discord.Embed(
        title=f"🐸 {mvp['name']}",
        description="MVP timer started",
        color=0x00ff88
    )

    embed.add_field(
        name="🕒 Killed",
        value=now.strftime("%H:%M"),
        inline=False
    )

    embed.add_field(
        name="⏳ Respawn Window",
        value=f"{window_start.strftime('%H:%M')} - {window_end.strftime('%H:%M')}",
        inline=False
    )

    embed.add_field(
        name="🗺 Map",
        value=selected_map,
        inline=False
    )

    embed.set_thumbnail(url=mvp["image"])

    # ---------- 9.5 Save timer to SQLite ----------

    timer_id, was_updated = create_or_update_timer(
        guild_id=interaction.guild_id,
        channel_id=interaction.channel_id,
        mvp_name=mvp["name"],
        map_name=selected_map,
        killed_at=now,
        respawn_start=window_start,
        respawn_end=window_end,
        image=mvp["image"]
    )

    if was_updated:
        message = f"🔄 {mvp['name']} ({selected_map}) timer updated"
    else:
        message = f"✅ {mvp['name']} ({selected_map}) timer added"

    # ---------- 9.6 Send ----------

    await interaction.followup.send(
        content=message,
        embed=embed
    )


# ============================================================
# BLOCK 10 — MVP TIMER BUTTONS
# Кнопки під MVP таймерами:
# Kill now — оновлює таймер від поточного часу
# Delete — видаляє таймер
# ============================================================

# ============================================================
# BLOCK 10.1 — SET KILL TIME MODAL
# Вікно для ручного введення часу вбивства MVP
# ============================================================

class SetKillTimeModal(discord.ui.Modal, title="Set MVP kill time"):
    kill_time = discord.ui.TextInput(
        label="Kill time",
        placeholder="Example: 21:35",
        required=True,
        max_length=5
    )

    def __init__(self, mvp_name: str):
        super().__init__()
        self.mvp_name = mvp_name

    async def on_submit(self, interaction: discord.Interaction):
        time_text = str(self.kill_time.value).strip()

        try:
            hour, minute = map(int, time_text.split(":"))

            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError

        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid time format. Use HH:MM, example: 21:35",
                ephemeral=True
            )
            return

        timer = get_timer_by_name(
            guild_id=interaction.guild_id,
            mvp_name=self.mvp_name
        )

        if not timer:
            await interaction.response.send_message(
                f"❌ Timer for {self.mvp_name} not found",
                ephemeral=True
            )
            return

        mvp = None

        for data in MVP_DATA.values():
            if data["name"] == self.mvp_name:
                mvp = data
                break

        if not mvp:
            await interaction.response.send_message(
                f"❌ MVP config for {self.mvp_name} not found",
                ephemeral=True
            )
            return

        kyiv_tz = pytz.timezone("Europe/Kyiv")
        now = datetime.now(kyiv_tz)

        killed_at = now.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        )

        if killed_at > now:
            killed_at = killed_at - timedelta(days=1)

        window_start = killed_at + timedelta(minutes=mvp["cooldown"])
        window_end = window_start + timedelta(minutes=mvp["window"])

        create_or_update_timer(
    guild_id=interaction.guild_id,
    channel_id=interaction.channel_id,
    mvp_name=self.mvp_name,
    map_name=timer["map_name"],
    killed_at=killed_at,
    respawn_start=window_start,
    respawn_end=window_end,
    image=timer["image"]
)

        embed = discord.Embed(
            title=f"🐸 {self.mvp_name}",
            description="Timer updated manually",
            color=0x00ff88
        )

        embed.add_field(name="🕒 Killed", value=killed_at.strftime("%H:%M"), inline=True)
        embed.add_field(
            name="⏳ Respawn Window",
            value=f"{window_start.strftime('%H:%M')} - {window_end.strftime('%H:%M')}",
            inline=True
        )
        embed.add_field(name="🗺 Map", value=timer["map_name"], inline=False)
        embed.set_thumbnail(url=timer["image"])

        await interaction.response.send_message(
            content=f"🕒 {self.mvp_name} kill time set to {killed_at.strftime('%H:%M')}",
            embed=embed
        )
# ============================================================

class MvpTimerView(discord.ui.View):
    def __init__(self, mvp_name: str):
        super().__init__(timeout=300)
        self.mvp_name = mvp_name

    @discord.ui.button(label="Kill now", emoji="⚔️", style=discord.ButtonStyle.success)
    async def kill_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        timer = get_timer_by_name(
            guild_id=interaction.guild_id,
            mvp_name=self.mvp_name
        )

        if not timer:
            await interaction.response.send_message(
                f"❌ Timer for {self.mvp_name} not found",
                ephemeral=True
            )
            return

        mvp = None

        for data in MVP_DATA.values():
            if data["name"] == self.mvp_name:
                mvp = data
                break

        if not mvp:
            await interaction.response.send_message(
                f"❌ MVP config for {self.mvp_name} not found",
                ephemeral=True
            )
            return

        now = datetime.now(pytz.timezone("Europe/Kyiv"))
        window_start = now + timedelta(minutes=mvp["cooldown"])
        window_end = window_start + timedelta(minutes=mvp["window"])

        create_or_update_timer(
            guild_id=interaction.guild_id,
            channel_id=interaction.channel_id,
            mvp_name=self.mvp_name,
            map_name=timer["map_name"],
            killed_at=now,
            respawn_start=window_start,
            respawn_end=window_end,
            image=timer["image"]
        )

        embed = discord.Embed(
            title=f"🐸 {self.mvp_name}",
            description="Timer updated by button",
            color=0x00ff88
        )

        embed.add_field(name="🕒 Killed", value=now.strftime("%H:%M"), inline=True)

        embed.add_field(
            name="⏳ Respawn Window",
            value=f"{window_start.strftime('%H:%M')} - {window_end.strftime('%H:%M')}",
            inline=True
        )

        embed.add_field(name="🗺 Map", value=timer["map_name"], inline=False)
        embed.set_thumbnail(url=timer["image"])

        await interaction.response.send_message(
            content=f"🔄 {self.mvp_name} timer updated",
            embed=embed
        )

    @discord.ui.button(label="Set kill time", emoji="🕒", style=discord.ButtonStyle.primary)
    async def set_kill_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetKillTimeModal(self.mvp_name))

    @discord.ui.button(label="Delete", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def delete_timer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        deleted_count = delete_timer(
            guild_id=interaction.guild_id,
            mvp_name=self.mvp_name
        )

        if deleted_count > 0:
            await interaction.response.send_message(
                f"🗑️ {self.mvp_name} timer deleted"
            )
        else:
            await interaction.response.send_message(
                f"❌ Timer for {self.mvp_name} not found",
                ephemeral=True
            )


# ============================================================
# BLOCK 11 — MVP LIST COMMAND
# Команда /mvp_list
# Показує активні MVP таймери окремими картками з кнопками
# ============================================================

@bot.tree.command(
    name="mvp_list",
    description="Show active MVP timers",
    guild=discord.Object(id=DISCORD_GUILD_ID)
)
async def mvp_list(interaction: discord.Interaction):
    timers = get_active_timers(interaction.guild_id)

    if not timers:
        await interaction.response.send_message("❌ No active MVP timers")
        return

    await interaction.response.send_message("🐸 Active MVP Timers:")

    now = datetime.now(pytz.timezone("Europe/Kyiv"))

    for timer in timers:
        respawn_start = datetime.fromisoformat(timer["respawn_start"])
        respawn_end = datetime.fromisoformat(timer["respawn_end"])
        killed_at = datetime.fromisoformat(timer["killed_at"])

        remaining_seconds = int((respawn_start - now).total_seconds())
        minutes_left = remaining_seconds // 60

        if minutes_left >= 0:
            time_left = f"{minutes_left} min"
        else:
            time_left = f"-{abs(minutes_left)} min"

        embed = discord.Embed(
            title=f"🐸 {timer['mvp_name']}",
            color=0x00ff88
        )

        embed.add_field(
            name="🕒 Killed",
            value=killed_at.strftime("%H:%M"),
            inline=True
        )

        embed.add_field(
            name="⏳ Respawn Window",
            value=(
                f"{respawn_start.strftime('%H:%M')} - "
                f"{respawn_end.strftime('%H:%M')}"
            ),
            inline=True
        )

        embed.add_field(
            name="⌛ Time to respawn",
            value=time_left,
            inline=False
        )

        embed.add_field(
            name="🗺 Map",
            value=timer["map_name"],
            inline=False
        )

        embed.set_thumbnail(url=timer["image"])

        view = MvpTimerView(timer["mvp_name"])

        await interaction.followup.send(
            embed=embed,
            view=view
        )


# ============================================================
# BLOCK 12 — NOTIFICATION LOOP
# Перевірка таймерів і відправка сповіщень
# ============================================================

async def notification_loop():
    await bot.wait_until_ready()

    while not bot.is_closed():
        now = datetime.now(pytz.timezone("Europe/Kyiv"))

        timers = get_active_timers()

        for timer in timers:
            respawn_start = datetime.fromisoformat(timer["respawn_start"])
            seconds_to_spawn = (respawn_start - now).total_seconds()

            channel = bot.get_channel(int(timer["channel_id"]))

            if channel is None:
                print(f"[{ENVIRONMENT}] Alert channel not found: {timer['channel_id']}")
                continue

            # ⏰ 10 хв до респу
            if (
                0 < seconds_to_spawn <= 600
                and int(timer["notified_10min"]) == 0
            ):
                embed = discord.Embed(
                    title=f"⏰ {timer['mvp_name']}",
                    description=(
                        f"Spawns in 10 minutes!\n"
                        f"🗺 Map: **{timer['map_name']}**"
                    ),
                    color=0xFFD700
                )

                embed.set_image(url=timer["image"])

                await channel.send(embed=embed)

                update_notification_flag(
                    timer_id=timer["id"],
                    flag_name="notified_10min"
                )

            # 🔥 початок вікна
            if (
                seconds_to_spawn <= 0
                and int(timer["notified_spawn"]) == 0
            ):
                embed = discord.Embed(
                    title=f"🔥 {timer['mvp_name']}",
                    description=(
                        f"Spawn window is OPEN!\n"
                        f"🗺 Map: **{timer['map_name']}**"
                    ),
                    color=0xFF0000
                )

                embed.set_image(url=timer["image"])

                await channel.send(embed=embed)

                update_notification_flag(
                    timer_id=timer["id"],
                    flag_name="notified_spawn"
                )

        await asyncio.sleep(30)

# ============================================================
# BLOCK 13 — BOT START
# Завжди має бути в самому низу файлу
# ============================================================

bot.run(TOKEN)