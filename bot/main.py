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


# ============================================================
# BLOCK 2 — ENV / TOKEN
# ============================================================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")


# ============================================================
# BLOCK 3 — MVP DATABASE
# Тут поки зберігаємо MVP вручну в коді
# cooldown = скільки хвилин MVP точно не буде
# window = скільки хвилин триває вікно респу
# ============================================================

MVP_DATA = {
    1: {
        "name": "Ifrit",
        "cooldown": 12,
        "window": 1,
        "maps": ["thor_v03"],
        "image": "https://file5s.ratemyserver.net/mobs/1832.gif"
    },
    2: {
        "name": "Valkyrie Randgris",
        "cooldown": 120,
        "window": 10,
        "maps": ["odin_tem03"],
        "image": "https://file5s.ratemyserver.net/mobs/1751.gif"
    },
    3: {
    "name": "Tao Gunka",
    "cooldown": 120,
    "window": 10,
    "maps": ["beach_dun", "cmd_fild03"],
    "image": "https://file5s.ratemyserver.net/mobs/1583.gif"
}
}


# ============================================================
# BLOCK 4 — ACTIVE TIMERS STORAGE
# Тимчасове збереження таймерів у пам'яті.
# Після перезапуску бота ці таймери пропадуть.
# Пізніше замінимо на SQLite.
# ============================================================

ACTIVE_TIMERS = []
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

    print(f"Logged in as {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    if notification_task is None:
        notification_task = bot.loop.create_task(notification_loop())

# ============================================================
# BLOCK 8 — TEST COMMAND
# Команда для перевірки, що бот живий
# ============================================================

@bot.tree.command(name="ping", description="Test command")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🐸 Froggy is alive!")


# ============================================================
# BLOCK 9 — MVP ADD COMMAND
# Команда /mvp_add
# Підтримує вибір мапи
# ============================================================

@bot.tree.command(name="mvp_add", description="Add MVP kill timer")
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

    # ---------- 9.5 Check existing timer ----------
    existing_timer = None

    for timer in ACTIVE_TIMERS:
        if timer["name"] == mvp["name"] and timer["map"] == selected_map:
            existing_timer = timer
            break

    # ---------- 9.6 Create new timer ----------
    new_timer = {
        "name": mvp["name"],
        "map": selected_map,
        "killed_at": now,
        "respawn_start": window_start,
        "respawn_end": window_end,
        "image": mvp["image"],
        "notified_10min": False,
        "notified_spawn": False
    }

    # ---------- 9.7 Add / update ----------
    if existing_timer:
        existing_timer["killed_at"] = now
        existing_timer["respawn_start"] = window_start
        existing_timer["respawn_end"] = window_end
        existing_timer["image"] = mvp["image"]

        # reset notification flags
        existing_timer["notified_10min"] = False
        existing_timer["notified_spawn"] = False

        message = f"🔄 {mvp['name']} ({selected_map}) timer updated"
    else:
        ACTIVE_TIMERS.append(new_timer)
        message = f"✅ {mvp['name']} ({selected_map}) timer added"

    # ---------- 9.8 Send ----------
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

        timer = None

        for t in ACTIVE_TIMERS:
            if t["name"] == self.mvp_name:
                timer = t
                break

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

        timer["killed_at"] = killed_at
        timer["respawn_start"] = window_start
        timer["respawn_end"] = window_end
        timer["notified_10min"] = False
        timer["notified_spawn"] = False

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
        embed.add_field(name="🗺 Map", value=timer["map"], inline=False)
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
        timer = None

        for t in ACTIVE_TIMERS:
            if t["name"] == self.mvp_name:
                timer = t
                break

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

        timer["killed_at"] = now
        timer["respawn_start"] = window_start
        timer["respawn_end"] = window_end
        timer["notified_10min"] = False
        timer["notified_spawn"] = False

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
        embed.add_field(name="🗺 Map", value=timer["map"], inline=False)
        embed.set_thumbnail(url=timer["image"])

        await interaction.response.send_message(
            content=f"🔄 {self.mvp_name} timer updated",
            embed=embed
        )

    @discord.ui.button(label="Set kill time", emoji="🕒", style=discord.ButtonStyle.primary)
    async def set_kill_time(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetKillTimeModal(self.mvp_name))

    @discord.ui.button(label="Delete", emoji="🗑️", style=discord.ButtonStyle.danger)
    async def delete_timer(self, interaction: discord.Interaction, button: discord.ui.Button):
        for t in ACTIVE_TIMERS:
            if t["name"] == self.mvp_name:
                ACTIVE_TIMERS.remove(t)

                await interaction.response.send_message(
                    f"🗑️ {self.mvp_name} timer deleted"
                )
                return

        await interaction.response.send_message(
            f"❌ Timer for {self.mvp_name} not found",
            ephemeral=True
        )


# ============================================================
# BLOCK 11 — MVP LIST COMMAND
# Команда /mvp_list
# Показує активні MVP таймери окремими картками з кнопками
# ============================================================

@bot.tree.command(name="mvp_list", description="Show active MVP timers")
async def mvp_list(interaction: discord.Interaction):
    if not ACTIVE_TIMERS:
        await interaction.response.send_message("❌ No active MVP timers")
        return

    await interaction.response.send_message("🐸 Active MVP Timers:")

# Сортування по часу до респу
    now = datetime.now(pytz.timezone("Europe/Kyiv"))

    sorted_timers = sorted(
    ACTIVE_TIMERS,
    key=lambda t: (t["respawn_start"] - now).total_seconds()
)

    for timer in sorted_timers:
        now = datetime.now(pytz.timezone("Europe/Kyiv"))

        remaining_seconds = int((timer["respawn_start"] - now).total_seconds())
        minutes_left = remaining_seconds // 60

        if minutes_left >= 0:
            time_left = f"{minutes_left} min"
        else:
            time_left = f"-{abs(minutes_left)} min"
        embed = discord.Embed(
            title=f"🐸 {timer['name']}",
            color=0x00ff88
        )

        embed.add_field(
            name="🕒 Killed",
            value=timer["killed_at"].strftime("%H:%M"),
            inline=True
        )

        embed.add_field(
            name="⏳ Respawn Window",
            value=(
                f"{timer['respawn_start'].strftime('%H:%M')} - "
                f"{timer['respawn_end'].strftime('%H:%M')}"
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
            value=timer["map"],
            inline=False
        )

        embed.set_thumbnail(url=timer["image"])

        view = MvpTimerView(timer["name"])

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

    channel_id = 1498686931759005696
    channel = bot.get_channel(channel_id)

    while not bot.is_closed():
        now = datetime.now(pytz.timezone("Europe/Kyiv"))

        for timer in ACTIVE_TIMERS:
            seconds_to_spawn = (timer["respawn_start"] - now).total_seconds()

            # ⏰ 10 хв до респу
            if 0 < seconds_to_spawn <= 600 and not timer.get("notified_10min", False):
                embed = discord.Embed(
                    title=f"⏰ {timer['name']}",
                    description=(
                        f"Spawns in 10 minutes!\n"
                        f"🗺 Map: **{timer['map']}**"
                    ),
                    color=0xFFD700
                )

                embed.set_image(url=timer["image"])

                await channel.send(embed=embed)

                timer["notified_10min"] = True

            # 🔥 початок вікна
            if seconds_to_spawn <= 0 and not timer.get("notified_spawn", False):
                embed = discord.Embed(
                    title=f"🔥 {timer['name']}",
                    description=(
                        f"Spawn window is OPEN!\n"
                        f"🗺 Map: **{timer['map']}**"
                    ),
                    color=0xFF0000
                )

                embed.set_image(url=timer["image"])

                await channel.send(embed=embed)

                timer["notified_spawn"] = True

        await asyncio.sleep(30)

# ============================================================
# BLOCK 13 — BOT START
# Завжди має бути в самому низу файлу
# ============================================================

bot.run(TOKEN)