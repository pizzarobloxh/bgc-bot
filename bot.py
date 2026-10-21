# bot.py — v5.0.0 (public edition)
# ============================================================
# BGC Bot — Discord recruitment background checker
#
# Public, sanitized edition. All personal identifiers, API keys,
# Discord channel IDs, brand-specific text and one-off configuration
# have been stripped out. Fill in your own values in the CONFIG
# section below before running.
#
# Original author: Pizzarobloxh (github.com/Pizzarobloxh)
#
# ============================================================
# REQUIREMENTS
#   pip install discord.py aiohttp aiosqlite
#   pip install aiodns pycares   # optional, enables non-blocking DNS
# ============================================================
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp, aiosqlite, asyncio, re, json, time, traceback, signal, logging
import logging.handlers
from collections import defaultdict
from datetime import datetime, timezone, date, timedelta
from enum import Enum
from typing import Optional

try:
    import aiodns
    _AIODNS_AVAILABLE = True
except ImportError:
    aiodns = None
    _AIODNS_AVAILABLE = False

# ==================== CONFIG ====================
# ─── Required ───
DISCORD_BOT_TOKEN      = "PASTE_YOUR_BOT_TOKEN"

# ─── Optional API keys (checks that need these will SKIP if missing) ───
XTRACKER_API_KEY       = "PASTE_YOUR_XTRACKER_KEY"          # xtracker.xyz
RW_API_KEY             = "PASTE_YOUR_ROBLOXWATCHER_KEY"     # robloxwatcher.com (RW_...)
EW_API_KEY             = "PASTE_YOUR_EXPLOITWATCHER_KEY"    # robloxwatcher.com (EW_...)
SIMMER_API_KEY         = "PASTE_YOUR_SIMMER_KEY"            # simmer.icu
BLOXLINK_API_KEY       = "PASTE_YOUR_BLOXLINK_SERVER_KEY"   # blox.link (server API key)

# ─── Branding (all optional — leave empty for defaults) ───
LOGO_EMOJI             = ""    # custom Discord emoji, e.g. "<:LOGO:123456789012345678>"
BRAND_NAME             = ""    # e.g. "My Clan"
BRAND_GROUP_URL        = ""    # e.g. "https://www.roblox.com/communities/1234567/..."
AUTO_ROLE_ID           = 0     # Discord role ID to assign on pass (0 = disabled)
OWNER_ID               = 0     # your Discord user ID (0 = /reset disabled)
DEFAULT_RECRUITMENT_CHANNEL_ID = 0  # fallback channel if /setup hasn't been run

# ─── Acceptance DM ───
ACCEPTANCE_DM_ENABLED  = True
# Leave empty to auto-generate from BRAND_NAME / BRAND_GROUP_URL above.
ACCEPTANCE_DM_TEMPLATE = ""
if not ACCEPTANCE_DM_TEMPLATE:
    _dm_parts = ["# Acceptance Notice", "", "Congratulations"]
    if BRAND_NAME:
        _dm_parts[2] += f", welcome to **{BRAND_NAME}**"
    _dm_parts[2] += "!"
    _dm_parts.append("")
    if BRAND_GROUP_URL:
        _dm_parts.append(f"Please join our Roblox group:\n{BRAND_GROUP_URL}")
        _dm_parts.append("")
    _dm_parts.append("Check the server for next steps.")
    ACCEPTANCE_DM_TEMPLATE = "\n".join(_dm_parts)

# ─── Bloxlink behaviour ───
BLOXLINK_ENABLED       = True
BLOXLINK_TIMEOUT       = 5.0

# ─── Your own blacklist (optional) ───
# A Google Sheet where column B is a Roblox group ID (group blacklist tab)
# or column B is a Discord user ID (user blacklist tab).
# Leave BLACKLIST_SHEET_ID empty to disable these checks.
BLACKLIST_SHEET_ID     = ""
GROUP_BLACKLIST_GID    = "0"           # gid of the group blacklist tab
USER_BLACKLIST_GID     = "0"           # gid of the user blacklist tab

# ─── Snow Core (optional) ───
# Another community's punishment sheet. Columns are expected to match
# the standard Snow Core layout. Leave empty to disable.
SNOW_CORE_SHEET_ID     = ""
SNOW_CORE_GID          = "0"

# ─── External databases (optional) ───
# Add any number of {key, sheet_id, gid, name} entries. Each is searched
# for the applicant's Roblox ID / usernames and Discord ID / usernames.
# Leave empty to skip this check entirely.
EXTERNAL_DATABASES = [
    # {"key": "my_alliance", "sheet_id": "1AbCdEf...", "gid": "0", "name": "My Alliance Blacklist"},
]

# ─── Rate limits ───
XTRACKER_RATE_LIMIT       = 1.0    # seconds between Xtracker calls (60/min baseline)
BLOXLINK_RATE_LIMIT       = 1.1    # seconds between Bloxlink calls (official limit ~60/min)
BLOXLINK_HARD_TIMEOUT_MS  = 1500   # cap Bloxlink wait; falls back to typed username on timeout
BLOXLINK_LATE_TTL         = 300    # seconds to keep a late Bloxlink result cached
EXPLOIT_WATCHER_INFORMATIONAL = True  # Exploit Watcher flags are logged, not failing
MISMATCHED_ALT_FAILS      = True   # treat typed-vs-Bloxlink mismatch as an alt to check

# ─── Check thresholds ───
MIN_DISCORD_AGE_DAYS     = 7
DISCORD_AGE_FAIL_IN_LIEU = False    # don't fail underage Discord accounts, just note it
MULTI_ACCOUNT_FAIL       = False    # multi-account detections are informational

# ─── Progress bar ───
PROGRESS_BAR_LEN         = 16
PROGRESS_FILLED          = "▓"
PROGRESS_EMPTY           = "░"
PROGRESS_MIN_DWELL       = 0.05
MAX_PROGRESS_PER_CHANNEL = 2

# ─── Timing / concurrency ───
EDIT_DEBOUNCE_SEC        = 1.0
AUTOCOMPLETE_TIMEOUT     = 1.5
MAX_CONCURRENT_BGC       = 5
PARSE_FAILURE_THRESHOLD  = 10
KEEPALIVE_INTERVAL_SEC   = 15
RACE_TIMEOUT_SEC         = 10.0
DLY_REACTION_SEC         = 0.4

# ─── Cache TTLs ───
BLACKLIST_TTL            = 900
BLACKLIST_DEBOUNCE       = 0.5
EXTERNAL_DB_TTL          = 1800
EXTERNAL_DB_DEBOUNCE     = 0.5
KEYSTONE_TTL             = 1800
KEYSTONE_DEBOUNCE        = 0.5
RECRUITMENT_CACHE_TTL    = 60

# Three-tier preemptive cache
IDENTITY_TTL_DAYS        = 7   # Bloxlink link, user info, username history
XTRACKER_CACHE_TTL_DAYS  = 3   # Xtracker results (expensive, rarely change)
FRESHNESS_TTL_MIN        = 30  # Roblox groups, Simmer RAB (mutable)
PREEMPTIVE_CLEANUP_DAYS  = 30

# ─── BGC stages (progress display) ───
BGC_STAGES = ["Parsing application", "Resolving account", "Verifying account",
              "Cross-referencing records", "Running integrity checks", "Finalizing"]
BGC_STAGE_EMOJI = ["🔍", "🔎", "📅", "🔗", "🛡️", "⚙️"]

# ─── System ───
DB_PATH                = "bgc.db"
LOG_FILE               = "bgc.log"
HEALTH_TEST_ROBLOX_ID  = None   # optional: for /health timeline
HEALTH_TEST_DISCORD_ID = None   # optional: for /health timeline

KEYSTONE_API_URL       = "https://api.keystone-swords.com/api/cases"
KEYSTONE_FAIL_CLOSED   = False
SIMMER_API_URL         = "https://api.simmer.icu"

BOT_VERSION            = "5.0.0"
CHECKS_VERSION         = 20
# ================================================

# ── Made by Pizzarobloxh ──
# Attribution kept in the user-agent string and log output.
BOT_AUTHOR             = "Pizzarobloxh"
BOT_AUTHOR_URL         = "https://github.com/Pizzarobloxh"

logger = logging.getLogger("bgc"); logger.setLevel(logging.INFO)
if not logger.handlers:
    _fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _s = logging.StreamHandler(); _s.setFormatter(_fmt); logger.addHandler(_s)
    try:
        _f = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=10_000_000, backupCount=5)
        _f.setFormatter(_fmt); logger.addHandler(_f)
    except Exception: pass

# ==================== MODULE-LEVEL CACHES ====================
_roblox_name_to_id            = {}
_roblox_info_cache            = {}
_roblox_hist_cache            = {}
_roblox_groups_cache          = {}
_simmer_cache                 = {}
_guild_log_cache              = {}
_recruitment_channel_cache    = {}
_race_winners                 = {}
_external_db_etags            = {}
_bloxlink_late_cache          = {}

ROBLOX_LOOKUP_TTL = 1800
ROBLOX_INFO_TTL   = 600
ROBLOX_HIST_TTL   = 1800
ROBLOX_GROUPS_TTL = 600
SIMMER_TTL        = 600
GUILD_LOG_TTL     = 60
RACE_WINNERS_TTL  = 600

_pending_preemptive = set()

_TOKEN_BLOCKLIST = {
    "sent","permanent","available","unavailable","evidence","none","null",
    "yes","no","true","false","n/a","na","tbd","unknown","pending","approved",
    "denied","expired","lifted","active","inactive","banned","clean",
}


def _record_race_winner(key, domain):
    _race_winners[key] = (domain, time.time())
    if len(_race_winners) > 500:
        now = time.time()
        for k in list(_race_winners.keys()):
            if now - _race_winners[k][1] > RACE_WINNERS_TTL:
                _race_winners.pop(k, None)


def _resolved(value, err=""):
    fut = asyncio.get_event_loop().create_future()
    fut.set_result((value, err))
    return fut


def _resolved_direct(value):
    fut = asyncio.get_event_loop().create_future()
    fut.set_result(value)
    return fut


def _store_late_bloxlink(did, gid, rid, status):
    now = time.time()
    _bloxlink_late_cache[(did, gid)] = (rid, status, now)
    if len(_bloxlink_late_cache) > 200:
        for k in list(_bloxlink_late_cache.keys()):
            if now - _bloxlink_late_cache[k][2] > BLOXLINK_LATE_TTL:
                _bloxlink_late_cache.pop(k, None)


class T:
    BRAND   = discord.Color.from_rgb(99, 102, 241)
    SUCCESS = discord.Color.from_rgb(34, 197, 94)
    DANGER  = discord.Color.from_rgb(239, 68, 68)
    WARN    = discord.Color.from_rgb(245, 158, 11)
    INFO    = discord.Color.from_rgb(59, 130, 246)
    MUTED   = discord.Color.from_rgb(107, 114, 128)
    EMOJI = {"PASS": "🟢", "HIT": "🔴", "SKIPPED": "🟡", "ERROR": "🟠",
             "roblox": "🎮", "discord": "💬", "calendar": "📅",
             "shield": "🛡️", "search": "🔍", "warn": "⚠️",
             "ok": "✅", "fail": "❌", "clock": "🕒", "link": "🔗"}
    STAGE_COLORS = [discord.Color.from_rgb(88, 101, 242), discord.Color.from_rgb(87, 148, 242),
                    discord.Color.from_rgb(87, 187, 242), discord.Color.from_rgb(87, 216, 214),
                    discord.Color.from_rgb(87, 227, 155), discord.Color.from_rgb(87, 242, 108)]
    @staticmethod
    def roblox_avatar(uid, size=420):
        return f"https://www.roblox.com/headshot-thumbnail/image?userId={uid}&width={size}&height={size}&format=png"
    @staticmethod
    def roblox_profile(uid):
        return f"https://www.roblox.com/users/{uid}/profile"


def branded(text: str) -> str:
    if not text: return LOGO_EMOJI or ""
    if not LOGO_EMOJI: return text
    return f"{LOGO_EMOJI} | {text}"

def ts_tag(dt, style="R"):
    return f"<t:{int(dt.timestamp())}:{style}>"

def _cell_str(c):
    if not c: return ""
    f = c.get("f")
    if f is not None and str(f).strip(): return str(f).strip()
    v = c.get("v")
    return "" if v is None else str(v).strip()

def _is_true(c):
    if not c: return False
    v = c.get("v")
    if v is True or v == 1: return True
    return _cell_str(c).strip().lower() in ("true","yes","1","y","active","banned")

def _spawn(coro, *, name=None, timings=None):
    start = time.perf_counter() if timings is not None else 0.0
    async def _wrapper():
        try:
            return await coro
        finally:
            if timings is not None:
                timings.append({"name": name or "unnamed",
                                "start": start,
                                "end": time.perf_counter()})
    t = asyncio.create_task(_wrapper())
    def _consume(task):
        if not task.cancelled():
            try: task.exception()
            except Exception: pass
    t.add_done_callback(_consume)
    return t


class CheckStatus(str, Enum):
    PASS = "PASS"; HIT = "HIT"; SKIPPED = "SKIPPED"; ERROR = "ERROR"


class RateLimiter:
    def __init__(self, interval_sec):
        self.interval = interval_sec; self.last = 0.0; self.lock = asyncio.Lock()
    async def acquire(self):
        async with self.lock:
            now = time.monotonic(); wait = self.interval - (now - self.last)
            if wait > 0: await asyncio.sleep(wait)
            self.last = time.monotonic()


class AdaptiveRateLimiter:
    def __init__(self, base_interval, max_multiplier=4.0, decay_sec=60.0):
        self.base = base_interval
        self.interval = base_interval
        self.max_multiplier = max_multiplier
        self.decay_sec = decay_sec
        self.last = 0.0
        self.lock = asyncio.Lock()
        self._consecutive_429s = 0
        self._last_429_ts = 0.0

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            wait = self.interval - (now - self.last)
            if wait > 0:
                await asyncio.sleep(wait)
            self.last = time.monotonic()

    def report_429(self):
        self._consecutive_429s += 1
        self._last_429_ts = time.monotonic()
        mult = min(2 ** self._consecutive_429s, self.max_multiplier)
        new_interval = self.base * mult
        if new_interval != self.interval:
            logger.warning(f"Xtracker 429 → limiter bumped {self.interval:.2f}s → {new_interval:.2f}s "
                           f"({self._consecutive_429s} consecutive, {mult:.1f}x)")
            self.interval = new_interval

    def report_ok(self):
        if self._consecutive_429s > 0 and (time.monotonic() - self._last_429_ts) > self.decay_sec:
            self._consecutive_429s = max(0, self._consecutive_429s - 1)
            mult = min(2 ** self._consecutive_429s, self.max_multiplier)
            new_interval = self.base * mult
            if new_interval != self.interval:
                logger.info(f"Xtracker limiter decayed {self.interval:.2f}s → {new_interval:.2f}s")
                self.interval = new_interval


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.guild_typing = True


class BGCBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.session = None; self.db = None
        self.db_lock = asyncio.Lock()
        self.bgc_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BGC)
        self.group_blacklist_lock = asyncio.Lock()
        self.user_blacklist_lock = asyncio.Lock()
        self.keystone_lock = asyncio.Lock()
        self.snow_core_lock = asyncio.Lock()
        self.external_db_lock = asyncio.Lock()
        self.xtracker_limiter = AdaptiveRateLimiter(XTRACKER_RATE_LIMIT, max_multiplier=4.0, decay_sec=60.0)
        self.bloxlink_limiter = RateLimiter(BLOXLINK_RATE_LIMIT)
        self._shutdown_started = False
        self._online_logged = False
        self._domain_dead_until = defaultdict(float)
        self._domain_error_count = defaultdict(int)
        self._metrics_preemptive_hits = 0
        self._metrics_preemptive_misses = 0
        self._metrics_bloxlink_timeouts = 0
        self._reset_caches()

    def _reset_caches(self):
        self.group_blacklist_cache = (None, 0.0)
        self.user_blacklist_cache = (None, 0.0)
        self.keystone_cache = (None, 0.0)
        self.snow_core_cache = (None, 0.0)
        self.external_db_cache = {}
        self._active_progress_per_channel = defaultdict(int)
        self.consecutive_parse_failures = 0
        self.parse_failure_notified = False
        self._domain_dead_until.clear()
        self._domain_error_count.clear()
        _roblox_name_to_id.clear()
        _roblox_info_cache.clear()
        _roblox_hist_cache.clear()
        _roblox_groups_cache.clear()
        _simmer_cache.clear()
        _guild_log_cache.clear()
        _recruitment_channel_cache.clear()
        _race_winners.clear()
        _external_db_etags.clear()
        _bloxlink_late_cache.clear()
        _pending_preemptive.clear()

    def _mark_domain_error(self, domain):
        self._domain_error_count[domain] += 1
        if self._domain_error_count[domain] >= 3:
            self._domain_dead_until[domain] = time.monotonic() + 60
            self._domain_error_count[domain] = 0

    def _mark_domain_ok(self, domain):
        self._domain_error_count[domain] = 0
        self._domain_dead_until[domain] = 0.0

    def _filter_healthy(self, domains):
        now = time.monotonic()
        healthy = [d for d in domains if self._domain_dead_until[d] <= now]
        return healthy or list(domains)

    async def setup_hook(self):
        self._reset_caches()
        connector_kwargs = dict(
            limit=200, limit_per_host=40, ttl_dns_cache=3600,
            keepalive_timeout=90, enable_cleanup_closed=True,
        )
        if _AIODNS_AVAILABLE:
            logger.info("aiodns installed — aiohttp will use it for non-blocking DNS")
        else:
            logger.info("aiodns not installed — using stdlib resolver (blocking)")
        connector = aiohttp.TCPConnector(**connector_kwargs)
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=connector,
            headers={
                "Accept-Encoding": "gzip, deflate, br",
                # ── Made by Pizzarobloxh ──
                "User-Agent": f"BGC-Bot/{BOT_VERSION} (made-by-{BOT_AUTHOR.lower()}; +discord-bot)",
            },
        )
        self.db = await aiosqlite.connect(DB_PATH)
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.execute("PRAGMA synchronous=NORMAL")
        await self.db.execute("PRAGMA cache_size=-20000")
        await self._init_db()
        now_mono = time.monotonic()
        self.xtracker_limiter.last = now_mono - self.xtracker_limiter.interval
        self.bloxlink_limiter.last = now_mono - self.bloxlink_limiter.interval
        try: await self.tree.sync()
        except Exception as e: logger.error(f"Command sync failed: {e}")
        asyncio.create_task(_warm_dns())
        asyncio.create_task(_warm_caches())
        asyncio.create_task(_cache_keep_warm_loop())
        asyncio.create_task(_keep_connections_warm_loop())
        logger.info(f"Setup complete (aiodns={'on' if _AIODNS_AVAILABLE else 'off'})")

    async def _init_db(self):
        await self.db.executescript("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY, pass_log_channel INTEGER, fail_log_channel INTEGER,
            bot_log_channel INTEGER, recruitment_channel INTEGER);
        CREATE TABLE IF NOT EXISTS bgc_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, message_id INTEGER, guild_id INTEGER,
            discord_id INTEGER, roblox_id INTEGER, roblox_username TEXT, passed INTEGER,
            reason TEXT, raw_responses TEXT, bot_version TEXT, checks_version INTEGER,
            checked_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS check_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, bgc_id INTEGER,
            check_name TEXT, status TEXT, details TEXT);
        CREATE INDEX IF NOT EXISTS idx_bgc_message ON bgc_checks(message_id);
        CREATE INDEX IF NOT EXISTS idx_bgc_discord ON bgc_checks(discord_id, guild_id);
        CREATE INDEX IF NOT EXISTS idx_bgc_roblox ON bgc_checks(roblox_id, guild_id);
        CREATE TABLE IF NOT EXISTS preemptive_scans (
            discord_id INTEGER NOT NULL,
            guild_id INTEGER NOT NULL,
            bloxlink_roblox_id INTEGER,
            bloxlink_status TEXT,
            roblox_info TEXT,
            username_history TEXT,
            user_groups TEXT,
            xtracker_by_id TEXT,
            simmer_rab TEXT,
            identity_scanned_at TEXT,
            xtracker_scanned_at TEXT,
            freshness_scanned_at TEXT,
            PRIMARY KEY (discord_id, guild_id)
        );
        """)
        await self.db.commit()
        await self._ensure_column("bgc_checks", "bot_version", "TEXT")
        await self._ensure_column("bgc_checks", "checks_version", "INTEGER")
        await self._ensure_column("guild_settings", "recruitment_channel", "INTEGER")
        await self._ensure_column("preemptive_scans", "xtracker_by_id", "TEXT")
        await self._ensure_column("preemptive_scans", "xtracker_scanned_at", "TEXT")

    async def _ensure_column(self, table, column, coltype):
        async with self.db.execute(f"PRAGMA table_info({table})") as cur:
            cols = [r[1] for r in await cur.fetchall()]
        if column not in cols:
            await self.db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
            await self.db.commit()

    async def close(self):
        if self._shutdown_started: return
        self._shutdown_started = True
        for guild in self.guilds:
            try: await bot_log(guild.id, "🔴 Bot Offline", "Shutdown.", T.DANGER)
            except Exception: pass
        if self.session and not self.session.closed: await self.session.close()
        if self.db: await self.db.close()
        await super().close()


bot = BGCBot(); tree = bot.tree
_pending_edits = {}


async def db_execute(sql, params=()):
    async with bot.db_lock:
        await bot.db.execute(sql, params); await bot.db.commit()

async def db_fetchone(sql, params=()):
    async with bot.db_lock:
        async with bot.db.execute(sql, params) as cur:
            return await cur.fetchone()

async def db_fetchall(sql, params=()):
    async with bot.db_lock:
        async with bot.db.execute(sql, params) as cur:
            return await cur.fetchall()

async def get_log_channels(gid):
    now = time.time()
    hit = _guild_log_cache.get(gid)
    if hit and now - hit[3] < GUILD_LOG_TTL:
        return hit[0], hit[1], hit[2]
    row = await db_fetchone("SELECT pass_log_channel, fail_log_channel, bot_log_channel FROM guild_settings WHERE guild_id=?", (gid,))
    result = row if row else (None, None, None)
    _guild_log_cache[gid] = (result[0], result[1], result[2], time.time())
    return result

async def set_log_channels(gid, p, f, b):
    await db_execute("""INSERT INTO guild_settings (guild_id, pass_log_channel, fail_log_channel, bot_log_channel)
        VALUES (?, ?, ?, ?) ON CONFLICT(guild_id) DO UPDATE SET pass_log_channel=excluded.pass_log_channel,
        fail_log_channel=excluded.fail_log_channel, bot_log_channel=excluded.bot_log_channel""", (gid, p, f, b))
    _guild_log_cache.pop(gid, None)

async def get_recruitment_channel(gid):
    now = time.time()
    hit = _recruitment_channel_cache.get(gid)
    if hit and now - hit[1] < RECRUITMENT_CACHE_TTL:
        return hit[0]
    row = await db_fetchone("SELECT recruitment_channel FROM guild_settings WHERE guild_id=?", (gid,))
    result = row[0] if (row and row[0]) else DEFAULT_RECRUITMENT_CHANNEL_ID
    _recruitment_channel_cache[gid] = (result, time.time())
    return result

async def set_recruitment_channel(gid, cid):
    await db_execute("""INSERT INTO guild_settings (guild_id, recruitment_channel) VALUES (?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET recruitment_channel=excluded.recruitment_channel""", (gid, cid))
    _recruitment_channel_cache.pop(gid, None)

async def is_already_checked(mid):
    row = await db_fetchone("SELECT 1 FROM bgc_checks WHERE message_id=?", (mid,))
    return row is not None

async def get_all_roblox_history(did, gid):
    rows = await db_fetchall("SELECT DISTINCT roblox_id, roblox_username FROM bgc_checks "
                             "WHERE discord_id=? AND guild_id=? AND roblox_id IS NOT NULL", (did, gid))
    return [(r[0], r[1]) for r in rows if r[0]]


async def bot_log(gid, title="", description="", color=None, fields=None, embed=None, brand=True):
    if not gid: return
    try:
        _, _, bid = await get_log_channels(gid)
        if not bid: return
        ch = bot.get_channel(bid)
        if ch is None: return
        if embed is None:
            ft = branded(title) if (brand and title) else title
            embed = discord.Embed(title=ft, description=description or None,
                                  color=color or T.BRAND, timestamp=datetime.now(timezone.utc))
            if fields:
                for n, v, inl in fields:
                    embed.add_field(name=n, value=str(v)[:1024] or "—", inline=inl)
        await ch.send(embed=embed)
    except Exception:
        logger.warning(f"bot_log failed for {gid}", exc_info=True)


def is_privileged_member(m):
    if not isinstance(m, discord.Member): return False
    p = m.guild_permissions
    return p.administrator or p.manage_guild


def _caches_hot() -> bool:
    if bot.group_blacklist_cache[0] is None: return False
    if bot.user_blacklist_cache[0] is None: return False
    if bot.keystone_cache[0] is None: return False
    if bot.snow_core_cache[0] is None: return False
    for cfg in EXTERNAL_DATABASES:
        if cfg["key"] not in bot.external_db_cache: return False
    return True


# ==================== PREEMPTIVE SCAN ====================
async def _preemptive_lookup(discord_id, guild_id):
    if not discord_id or not guild_id: return None
    row = await db_fetchone(
        "SELECT bloxlink_roblox_id, bloxlink_status, roblox_info, username_history, "
        "user_groups, xtracker_by_id, xtracker_scanned_at, simmer_rab, "
        "identity_scanned_at, freshness_scanned_at "
        "FROM preemptive_scans WHERE discord_id=? AND guild_id=?",
        (discord_id, guild_id))
    if not row: return None
    now = datetime.now(timezone.utc)
    id_time = parse_iso(row[8]) if row[8] else None
    xt_time = parse_iso(row[6]) if row[6] else None
    fresh_time = parse_iso(row[9]) if row[9] else None
    id_fresh = bool(id_time and (now - id_time).days < IDENTITY_TTL_DAYS)
    xtracker_fresh = bool(xt_time and (now - xt_time).days < XTRACKER_CACHE_TTL_DAYS)
    fresh_fresh = bool(fresh_time and (now - fresh_time).total_seconds() < FRESHNESS_TTL_MIN * 60)
    if not (id_fresh or xtracker_fresh or fresh_fresh):
        return None
    xt_by_id = {}
    if xtracker_fresh and row[5]:
        try: xt_by_id = json.loads(row[5])
        except: xt_by_id = {}
    return {
        "blox_id": row[0],
        "blox_status": row[1],
        "info": json.loads(row[2]) if row[2] and id_fresh else None,
        "hist": json.loads(row[3]) if row[3] and id_fresh else None,
        "groups": json.loads(row[4]) if row[4] and fresh_fresh else None,
        "xtracker_by_id": xt_by_id,
        "xtracker_scanned_at": row[6] if xtracker_fresh else None,
        "simmer": json.loads(row[7]) if row[7] and fresh_fresh else None,
        "id_fresh": id_fresh,
        "xtracker_fresh": xtracker_fresh,
        "fresh_fresh": fresh_fresh,
    }


async def _preemptive_scan(user, guild, key):
    """Fired on typing. Bloxlink + nickname in parallel, then multi-ID Xtracker.
    Saves identity the moment it resolves; saves xtracker+freshness after."""
    session = bot.session
    try:
        now = datetime.now(timezone.utc)
        row = await db_fetchone(
            "SELECT bloxlink_roblox_id, identity_scanned_at, xtracker_scanned_at, freshness_scanned_at "
            "FROM preemptive_scans WHERE discord_id=? AND guild_id=?",
            (user.id, guild.id))
        cached_rid = row[0] if row else None
        id_scanned = parse_iso(row[1]) if row and row[1] else None
        xt_scanned = parse_iso(row[2]) if row and row[2] else None
        fresh_scanned = parse_iso(row[3]) if row and row[3] else None

        need_identity = not (id_scanned and (now - id_scanned).days < IDENTITY_TTL_DAYS)
        need_xtracker = not (xt_scanned and (now - xt_scanned).days < XTRACKER_CACHE_TTL_DAYS)
        need_freshness = not (fresh_scanned and (now - fresh_scanned).total_seconds() < FRESHNESS_TTL_MIN * 60)

        if not (need_identity or need_xtracker or need_freshness):
            return  # everything fresh — silent

        needs = []
        if need_identity: needs.append("identity")
        if need_xtracker: needs.append("xtracker")
        if need_freshness: needs.append("freshness")
        await bot_log(guild.id, "🧠 Preemptive scan started",
                      f"{user.mention} (`{user.id}`)\nRefreshing: **{', '.join(needs)}**",
                      color=T.INFO)

        bloxlink_task = None
        if need_identity and BLOXLINK_ENABLED:
            bloxlink_task = asyncio.create_task(bloxlink_discord_to_roblox(session, guild.id, user.id))

        nickname_task = None
        nickname = (getattr(user, "nick", None) or "").strip().lstrip("@")
        if nickname and re.fullmatch(r'[A-Za-z0-9_]{3,20}', nickname):
            nickname_task = asyncio.create_task(roblox_user_lookup(session, nickname))

        blox_id, blox_status, nickname_id = None, None, None
        pending = [t for t in (bloxlink_task, nickname_task) if t is not None]
        if pending:
            results = await asyncio.gather(*pending, return_exceptions=True)
            for task, result in zip(pending, results):
                if isinstance(result, Exception):
                    logger.debug(f"Preemptive lookup raised: {type(result).__name__}: {result}")
                    continue
                if task is bloxlink_task:
                    blox_id, blox_status = result
                elif task is nickname_task:
                    nick_res, _ = result
                    if nick_res: nickname_id = nick_res["id"]

        primary = blox_id or nickname_id or cached_rid

        info, hist = None, None
        identity_ts = None
        if need_identity and primary:
            info_result, hist_result = await asyncio.gather(
                roblox_user_info(session, primary),
                roblox_username_history(session, primary),
                return_exceptions=True)
            if isinstance(info_result, tuple): info = info_result[0]
            if isinstance(hist_result, tuple): hist = hist_result[0]
            if blox_status in ("ok", "not_linked", None):
                identity_ts = now.isoformat()

        if identity_ts:
            async with bot.db_lock:
                await bot.db.execute("""
                    INSERT INTO preemptive_scans
                        (discord_id, guild_id, bloxlink_roblox_id, bloxlink_status,
                         roblox_info, username_history, identity_scanned_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(discord_id, guild_id) DO UPDATE SET
                        bloxlink_roblox_id=COALESCE(excluded.bloxlink_roblox_id, preemptive_scans.bloxlink_roblox_id),
                        bloxlink_status=COALESCE(excluded.bloxlink_status, preemptive_scans.bloxlink_status),
                        roblox_info=COALESCE(excluded.roblox_info, preemptive_scans.roblox_info),
                        username_history=COALESCE(excluded.username_history, preemptive_scans.username_history),
                        identity_scanned_at=excluded.identity_scanned_at
                """, (user.id, guild.id, blox_id or cached_rid, blox_status,
                       json.dumps(info) if info else None,
                       json.dumps(hist) if hist else None,
                       identity_ts))
                await bot.db.commit()
            await bot_log(guild.id, "🧠 Identity cached",
                          f"{user.mention} — bloxlink: `{blox_id or 'none'}` (`{blox_status}`) · "
                          f"nickname: `{nickname_id or 'none'}`",
                          color=T.SUCCESS)

        all_ids = set()
        if blox_id: all_ids.add(int(blox_id))
        if nickname_id: all_ids.add(int(nickname_id))
        if cached_rid: all_ids.add(int(cached_rid))
        try:
            hist_db = await get_all_roblox_history(user.id, guild.id)
            for hid, _ in hist_db:
                if hid: all_ids.add(int(hid))
        except Exception: pass

        xt_tasks = {}
        if need_xtracker and all_ids and XTRACKER_API_KEY and not XTRACKER_API_KEY.startswith("PASTE"):
            for rid in all_ids:
                xt_tasks[f"reg_{rid}"] = asyncio.create_task(xtracker_check(session, "registry/user", rid))
                xt_tasks[f"own_{rid}"] = asyncio.create_task(xtracker_check(session, "ownership/user", rid))

        groups_task = None
        simmer_task = None
        if need_freshness and primary:
            groups_task = asyncio.create_task(roblox_user_groups(session, primary))
            if SIMMER_API_KEY and not SIMMER_API_KEY.startswith("PASTE"):
                simmer_task = asyncio.create_task(simmer_rab_check(session, primary))

        xt_by_id = {}
        if xt_tasks:
            xt_results = await asyncio.gather(*xt_tasks.values(), return_exceptions=True)
            for (k, _t), res in zip(xt_tasks.items(), xt_results):
                if isinstance(res, Exception): continue
                if k.startswith("reg_"):
                    rid = int(k[4:])
                    xt_by_id.setdefault(rid, {})["reg"] = res
                elif k.startswith("own_"):
                    rid = int(k[4:])
                    xt_by_id.setdefault(rid, {})["own"] = res

        groups = None
        simmer = None
        fresh_ts = None
        if groups_task:
            if simmer_task:
                gr, sr = await asyncio.gather(groups_task, simmer_task, return_exceptions=True)
                if isinstance(gr, tuple): groups = gr[0]
                if isinstance(sr, dict): simmer = sr
            else:
                gr = await groups_task
                if isinstance(gr, tuple): groups = gr[0]
            fresh_ts = now.isoformat()

        if need_xtracker and xt_by_id:
            async with bot.db_lock:
                await bot.db.execute("""
                    UPDATE preemptive_scans SET
                        xtracker_by_id=?, xtracker_scanned_at=?
                    WHERE discord_id=? AND guild_id=?
                """, (json.dumps({str(k): v for k, v in xt_by_id.items()}),
                       now.isoformat(), user.id, guild.id))
                await bot.db.commit()

        if fresh_ts:
            async with bot.db_lock:
                await bot.db.execute("""
                    UPDATE preemptive_scans SET
                        user_groups=?, simmer_rab=?, freshness_scanned_at=?
                    WHERE discord_id=? AND guild_id=?
                """, (json.dumps(groups) if groups is not None else None,
                       json.dumps(simmer) if simmer else None,
                       fresh_ts, user.id, guild.id))
                await bot.db.commit()

        xt_summary_lines = []
        for rid in sorted(xt_by_id.keys()):
            data = xt_by_id[rid]
            reg = data.get("reg", {})
            own = data.get("own", {})
            reg_st = reg.get("status", "?") if isinstance(reg, dict) else "?"
            own_st = own.get("status", "?") if isinstance(own, dict) else "?"
            flag = "🔴" if (reg_st == CheckStatus.HIT or own_st == CheckStatus.HIT) else "🟢"
            xt_summary_lines.append(f"{flag} `{rid}`: reg={reg_st} own={own_st}")

        simmer_st = simmer.get("status", "skipped") if simmer else "skipped"
        groups_st = "checked" if groups is not None else "skipped"
        await bot_log(guild.id, "🧠 Preemptive scan complete",
                      f"{user.mention} (`{user.id}`)\n"
                      f"**IDs:** {', '.join(f'`{i}`' for i in sorted(all_ids)) or 'none'}\n"
                      f"**Xtracker:**\n" + ("\n".join(xt_summary_lines) if xt_summary_lines else "_(skipped)_") + "\n"
                      f"**Groups:** {groups_st} · **Simmer:** {simmer_st}",
                      color=T.SUCCESS)

    except Exception as e:
        logger.warning(f"Preemptive scan failed for {user.id}: {e}", exc_info=True)
        try:
            await bot_log(guild.id, "🔴 Preemptive scan failed",
                          f"{user.mention} — `{type(e).__name__}: {str(e)[:200]}`",
                          color=T.DANGER)
        except: pass
    finally:
        _pending_preemptive.discard(key)


@bot.event
async def on_typing(channel, user, when):
    if bot.db is None: return
    if not isinstance(channel, discord.TextChannel): return
    if not isinstance(user, discord.Member): return
    if user.bot or is_privileged_member(user): return
    if channel.guild is None: return
    try:
        rc = await get_recruitment_channel(channel.guild.id)
    except Exception:
        return
    if not rc or channel.id != rc: return
    key = (user.id, channel.guild.id)
    if key in _pending_preemptive: return
    _pending_preemptive.add(key)
    logger.debug(f"on_typing → firing preemptive scan for {user.id}")
    asyncio.create_task(_preemptive_scan(user, channel.guild, key))


# ==================== RACE HELPER ====================
async def _race_200(session, domains, path, *, timeout=RACE_TIMEOUT_SEC):
    domains = bot._filter_healthy(domains)
    errors = []
    got_404 = False

    async def _try(domain):
        nonlocal got_404
        try:
            async with session.get(
                f"https://{domain}{path}",
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as r:
                if r.status == 200:
                    bot._mark_domain_ok(domain)
                    return ("ok", await r.json(), domain, None)
                if r.status == 404:
                    got_404 = True
                else:
                    bot._mark_domain_error(domain)
                return ("err", None, None, f"{domain}: HTTP {r.status}")
        except asyncio.TimeoutError:
            bot._mark_domain_error(domain); return ("err", None, None, f"{domain}: timeout")
        except aiohttp.ClientConnectorError:
            bot._mark_domain_error(domain); return ("err", None, None, f"{domain}: conn")
        except Exception as e:
            bot._mark_domain_error(domain); return ("err", None, None, f"{domain}: {type(e).__name__}")

    tasks = [asyncio.create_task(_try(d)) for d in domains]
    try:
        for fut in asyncio.as_completed(tasks):
            kind, val, domain, err = await fut
            if kind == "ok":
                for t in tasks:
                    if not t.done(): t.cancel()
                return val, None, domain, False
            errors.append(err)
        return None, " | ".join(errors), None, got_404
    finally:
        for t in tasks:
            if not t.done(): t.cancel()


# ==================== BLOXLINK ====================
async def bloxlink_discord_to_roblox(session, gid, did):
    if not BLOXLINK_ENABLED: return None, "disabled"
    if not BLOXLINK_API_KEY or BLOXLINK_API_KEY.startswith("PASTE"): return None, "disabled"
    if not gid or not did: return None, "missing_ids"
    await bot.bloxlink_limiter.acquire()
    url = f"https://api.blox.link/v4/public/guilds/{gid}/discord-to-roblox/{did}"
    try:
        async with session.get(url, headers={"Authorization": BLOXLINK_API_KEY},
                                timeout=aiohttp.ClientTimeout(total=BLOXLINK_TIMEOUT)) as r:
            text = await r.text()
            if r.status == 200:
                try: data = json.loads(text)
                except: return None, "non_json"
                rid = data.get("robloxID") or data.get("robloxId")
                if rid is None: return None, "empty"
                try: return int(rid), "ok"
                except: return None, "bad_id"
            if r.status == 404: return None, "not_linked"
            if r.status == 401: return None, "invalid_key"
            if r.status == 429: return None, "rate_limited"
            low = text.lower()
            if "not linked" in low: return None, "not_linked"
            if "ratelimited" in low or "rate limit" in low: return None, "rate_limited"
            return None, f"HTTP {r.status}"
    except asyncio.TimeoutError: return None, "timeout"
    except aiohttp.ClientConnectorError: return None, "connection_failed"
    except Exception as e: return None, type(e).__name__


# ==================== EXTERNAL DB INDEX ====================
def build_external_index(records):
    idx = {}
    for rec in records:
        for ci, cell in rec["cells"].items():
            disp = cell.get("f") if cell.get("f") is not None else cell.get("v")
            if disp is None: continue
            for tok in re.split(r'[\s,|]+', str(disp)):
                tok = tok.strip().strip('()<>[]"\'').lstrip("@").rstrip(".,;:")
                if not tok: continue
                if tok.lower() in _TOKEN_BLOCKLIST: continue
                idx.setdefault(tok.lower(), []).append((rec, ci, tok))
    return idx


def search_external_index(idx, col_types, rbx_ids, rbx_names, discord_ids, discord_names):
    found = {}
    pairs = ([(t, "discord_id") for t in discord_ids] +
             [(t, "rbx_id") for t in rbx_ids] +
             [(t.lower(), "rbx_username") for t in rbx_names] +
             [(t.lower(), "discord_username") for t in discord_names])
    for token, mtype in pairs:
        for (rec, ci, orig_tok) in idx.get(token.lower(), ()):
            ct = col_types.get(ci, "other")
            if ct != "other" and ct != mtype:
                continue
            key = id(rec)
            entry = found.setdefault(key, {"record": rec, "matches": []})
            if not any(m["col_idx"] == ci for m in entry["matches"]):
                entry["matches"].append({"col_idx": ci, "cell": orig_tok,
                                          "token": orig_tok, "match_type": mtype})
    return found


def detect_column_types(records, col_labels):
    if not records: return {}
    max_col = 0
    for r in records[:100]:
        for ci in r["cells"]: max_col = max(max_col, ci + 1)

    def header_type(h):
        if not h: return None
        h = h.lower().strip()
        if not h: return None
        if "discord" in h and "id" in h: return "discord_id"
        if "discord" in h and any(k in h for k in ("username","user","name","tag","handle")): return "discord_username"
        if h in ("discord","discord tag","discord handle","alt discord","main discord","dc"): return "discord_username"
        if ("roblox" in h or "rbx" in h) and "id" in h: return "rbx_id"
        if ("roblox" in h or "rbx" in h) and any(k in h for k in ("username","user","name")): return "rbx_username"
        if h in ("user id","userid","id","playerid"): return "rbx_id"
        if h in ("roblox","roblox user","rbx user","main account","alt account","account","main","alt"): return "rbx_username"
        if any(k in h for k in ("reason","punish","duration","date","evidence","note","additional",
                                "criteria","category","administrator","status","issued",
                                "sent","appeal","profile","link","ban","flag",
                                "available","unavailable","restricted","delivered")):
            return "other"
        return None

    result = {}
    for ci in range(max_col):
        if ci < len(col_labels):
            ht = header_type(col_labels[ci])
            if ht: result[ci] = ht; continue
        samples = []
        for r in records[:100]:
            if ci in r["cells"]:
                v = r["cells"][ci].get("v")
                if v is not None:
                    s = str(v).strip()
                    if s and s.lower() not in ("n/a","null","none","-"): samples.append(s)
        if not samples: result[ci] = "other"; continue
        cnt = {"discord_id": 0, "rbx_id": 0, "rbx_username": 0, "discord_username": 0, "other": 0}
        for s in samples:
            if re.fullmatch(r'\d{17,22}', s): cnt["discord_id"] += 1
            elif re.fullmatch(r'\d{5,16}', s): cnt["rbx_id"] += 1
            elif re.fullmatch(r'[A-Za-z0-9_]{3,20}', s) and not s.isdigit(): cnt["rbx_username"] += 1
            elif re.fullmatch(r'[a-z0-9._-]{2,32}', s.lower()): cnt["discord_username"] += 1
            else: cnt["other"] += 1
        best = max(cnt, key=cnt.get)
        result[ci] = best if cnt[best] / max(1, len(samples)) >= 0.7 else "other"
    return result


def strip_gviz_wrapper(text):
    s = text.find("("); e = text.rfind(")")
    return None if (s == -1 or e <= s) else text[s+1:e]


async def fetch_external_db(session, cfg, force_refresh=False):
    key = cfg["key"]; now = time.time()
    async with bot.external_db_lock:
        cached, ts = bot.external_db_cache.get(key, (None, 0.0))
        if cached is not None:
            if not force_refresh and now - ts < EXTERNAL_DB_TTL: return cached, None
            if force_refresh and now - ts < EXTERNAL_DB_DEBOUNCE: return cached, None

    base_url = f"https://docs.google.com/spreadsheets/d/{cfg['sheet_id']}/gviz/tq?tqx=out%3Ajson&gid={cfg['gid']}&tq=select%20*"
    headers = {}
    if force_refresh:
        ts_ms = int(time.time() * 1000)
        url = f"{base_url}&_nocache={ts_ms}"
        headers["Cache-Control"] = "no-cache"
    else:
        url = base_url
        headers["Cache-Control"] = "no-cache"
        etag = _external_db_etags.get(key)
        if etag:
            headers["If-None-Match"] = etag

    try:
        async with session.get(url, headers=headers,
                                timeout=aiohttp.ClientTimeout(total=25)) as r:
            if r.status == 304 and cached is not None:
                async with bot.external_db_lock:
                    bot.external_db_cache[key] = (cached, time.time())
                return cached, None
            if r.status != 200: return None, f"HTTP {r.status}"
            new_etag = r.headers.get("ETag") or r.headers.get("etag")
            if new_etag:
                _external_db_etags[key] = new_etag
            js = strip_gviz_wrapper(await r.text())
            if js is None: return None, "no wrapper"
            try: data = json.loads(js)
            except json.JSONDecodeError as e: return None, f"parse: {e}"
            table = data.get("table", {})
            cols = table.get("cols", []); rows = table.get("rows", [])
            col_labels = [(c.get("label") or "").strip() for c in cols]
            records = []
            for ri, row in enumerate(rows):
                cells = row.get("c", []) or []
                rec_cells = {}; has_content = False
                for ci, cell in enumerate(cells):
                    if cell is None: continue
                    v = cell.get("v"); f = cell.get("f")
                    if v is None and f is None: continue
                    rec_cells[ci] = {"v": v, "f": f}; has_content = True
                if has_content: records.append({"row_index": ri, "cells": rec_cells})
            types = detect_column_types(records, col_labels)
            payload = {"records": records, "col_labels": col_labels, "col_types": types,
                       "cfg": cfg, "index": build_external_index(records)}
            async with bot.external_db_lock:
                bot.external_db_cache[key] = (payload, time.time())
            return payload, None
    except asyncio.TimeoutError: return None, "timeout"
    except Exception as e: return None, f"{type(e).__name__}: {str(e)[:60]}"


async def search_external_dbs(session, identities, force_refresh=False):
    if not EXTERNAL_DATABASES:
        return {"matches_by_db": {}, "errors": []}
    rbx_ids = {str(x) for x in identities.get("rbx_ids", set()) if str(x).isdigit() and len(str(x)) >= 4}
    rbx_names = {str(u).lower() for u in identities.get("rbx_usernames", set()) if u}
    discord_ids = {str(x) for x in identities.get("discord_ids", set()) if str(x).isdigit()}
    discord_names = {str(u).lower() for u in identities.get("discord_usernames", set()) if u}
    if not (rbx_ids or rbx_names or discord_ids or discord_names):
        return {"matches_by_db": {}, "errors": []}
    tasks = [fetch_external_db(session, cfg, force_refresh) for cfg in EXTERNAL_DATABASES]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    matches_by_db = {}; errors = []
    for cfg, res in zip(EXTERNAL_DATABASES, results):
        if isinstance(res, Exception):
            errors.append((cfg["key"], str(res))); continue
        payload, err = res
        if payload is None:
            errors.append((cfg["key"], err or "fetch failed")); continue
        found = search_external_index(payload["index"], payload["col_types"],
                                       rbx_ids, rbx_names, discord_ids, discord_names)
        if found:
            matches_by_db[cfg["key"]] = [
                {**entry, "cfg": cfg, "col_labels": payload["col_labels"]}
                for entry in found.values()]
    return {"matches_by_db": matches_by_db, "errors": errors}


# ==================== EXPIRY HELPERS ====================
def extract_expiry_date(record, col_labels):
    for ci, lbl in enumerate(col_labels):
        ll = lbl.lower()
        if any(k in ll for k in ("end date","enddate","expiry","expires","until","lifted","releases","released")):
            cell = record["cells"].get(ci)
            if not cell: continue
            v = cell.get("f") or cell.get("v")
            if not v: continue
            s = str(v).strip()
            for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d","%m/%d/%Y","%d-%m-%Y","%Y/%m/%d"):
                try: return datetime.strptime(s, fmt).date()
                except: pass
    return None


def extract_status_inactive(record, col_labels):
    for ci, lbl in enumerate(col_labels):
        ll = lbl.lower()
        if "status" in ll or "state" in ll:
            cell = record["cells"].get(ci)
            if not cell: continue
            s = _cell_str(cell).lower()
            if any(k in s for k in ("expired","lifted","appealed","revoked","inactive","overturned","reversed")):
                return True
    return False


# ==================== YES/NO + PARSER ====================
YES_TOKENS = {"yes","yeah","yea","ye","yep","yup","ya","yah","ok","okay","sure",
              "certainly","definitely","absolutely","ofc","correct","true","affirmative","alright","alrighty"}
NO_TOKENS = {"no","nah","nope","never","false","negative"}

def parse_yes_no(text):
    if not text: return None
    low = str(text).lower()
    if re.search(r'\byes\s*/\s*no\b', low) or re.search(r'\byes\s+or\s+no\b', low): return None
    tokens = re.findall(r'\b[a-z]+\b', low)
    y = [i for i,t in enumerate(tokens) if t in YES_TOKENS]
    n = [i for i,t in enumerate(tokens) if t in NO_TOKENS]
    if y and n: return "yes" if y[-1] > n[-1] else "no"
    if y: return "yes"
    if n: return "no"
    return None


def parse_clanning(text):
    low = (text or "").lower()
    m = re.search(r'clans?\s*[-:]\s*(\w+)', low)
    if m:
        v = parse_yes_no(m.group(1))
        if v: return v
    return parse_yes_no(low)


def parse_iso(s):
    if not s: return None
    try:
        cleaned = re.sub(r'\.\d+', '', s.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except: return None


def parse_dmy(s):
    if not s: return None
    s = str(s).strip()
    for fmt in ("%d/%m/%Y","%d/%m/%y","%Y-%m-%d","%m/%d/%Y","%Y/%m/%d","%d-%m-%Y"):
        try: return datetime.strptime(s, fmt).date()
        except: pass
    return None


def parse_discord_target(t):
    if not t: return None
    m = re.fullmatch(r'<@!?(\d+)>', t.strip())
    if m: return int(m.group(1))
    if re.fullmatch(r'\d{15,22}', t.strip()): return int(t.strip())
    return None


def parse_group_id(v):
    if v is None: return None
    s = str(v).strip()
    if not s: return None
    try: return int(float(s))
    except: pass
    m = re.search(r'roblox\.com/(?:groups|communities)/(\d+)', s, re.IGNORECASE)
    return int(m.group(1)) if m else None


def parse_group_id_from_cell(c):
    if not c: return None
    for k in ("v","f"):
        v = c.get(k)
        if v is None: continue
        g = parse_group_id(v)
        if g is not None: return g
    return None


def discord_account_age_days(did):
    try:
        created = discord.utils.snowflake_time(did)
        return (datetime.now(timezone.utc) - created).days
    except: return None


async def check_discord_age(did):
    if not did: return {"name": "DiscordAccountAge", "status": CheckStatus.SKIPPED, "details": "no Discord ID"}
    age = discord_account_age_days(did)
    if age is None: return {"name": "DiscordAccountAge", "status": CheckStatus.SKIPPED, "details": "unparseable"}
    if age < MIN_DISCORD_AGE_DAYS:
        st = CheckStatus.HIT if DISCORD_AGE_FAIL_IN_LIEU else CheckStatus.SKIPPED
        return {"name": "DiscordAccountAge", "status": st, "details": f"{age}d (<{MIN_DISCORD_AGE_DAYS})"}
    return {"name": "DiscordAccountAge", "status": CheckStatus.PASS, "details": f"{age}d"}


async def detect_multi_account(gid, did, rid):
    if not did or not rid:
        return {"name": "MultiAccount", "status": CheckStatus.SKIPPED, "details": "missing ids"}
    o_rbx = await db_fetchall("SELECT DISTINCT roblox_id, roblox_username FROM bgc_checks "
                              "WHERE discord_id=? AND guild_id=? AND roblox_id IS NOT NULL AND roblox_id != ?",
                              (did, gid, rid))
    o_dc = await db_fetchall("SELECT DISTINCT discord_id FROM bgc_checks "
                             "WHERE roblox_id=? AND guild_id=? AND discord_id IS NOT NULL AND discord_id != ?",
                             (rid, gid, did))
    if not o_rbx and not o_dc:
        return {"name": "MultiAccount", "status": CheckStatus.PASS, "details": "no patterns"}
    parts = []
    if o_rbx:
        alt_infos = await asyncio.gather(
            *[roblox_user_info(bot.session, hid) for hid, _ in o_rbx],
            return_exceptions=True)
        names = [i[0]["name"] for i in alt_infos if isinstance(i, tuple) and i[0] and i[0].get("name")]
        if names: detail = ", ".join(f"`{n}`" for n in names[:3])
        else: detail = ", ".join(f"`{u or '?'}`" for _, u in o_rbx[:3])
        parts.append(f"{len(o_rbx)} other RBX under this Discord ({detail})")
    if o_dc:
        s = ", ".join(f"<@{d}>" for (d,) in o_dc[:3])
        parts.append(f"{len(o_dc)} other Discord for this RBX ({s})")
    return {"name": "MultiAccount",
            "status": CheckStatus.HIT if MULTI_ACCOUNT_FAIL else CheckStatus.SKIPPED,
            "details": "; ".join(parts)}


# ==================== KEYSTONE ====================
def split_ks(v): return [] if not v else [t for t in re.split(r"[|,\s]+", str(v)) if t]

def strip_ks(s):
    if not s: return ""
    s = re.sub(r':[a-z_]+:', '', str(s)).replace("'","").replace('"','')
    return s.replace("\u200b","").replace("\u200c","").replace("\u200d","").strip().lower()

def classify_ks(s):
    x = strip_ks(s)
    if "inactive" in x or "archived" in x: return "dead"
    if "final review" in x or "pending" in x: return "pending"
    if "active" in x or x == "published": return "active"
    return "unknown"

def ks_search(cases, ids):
    if not ids: return [], [], [], []
    a, d, p, u = [], [], [], []
    for c in cases:
        tk = split_ks(c.get("user_ids")) + split_ks(c.get("usernames"))
        if not tk: continue
        ts = {t.lower().lstrip('@') for t in tk}
        if not (ids & ts): continue
        e = {"source": c.get("source","?"), "case_id": c.get("case_id","?"),
             "status_raw": c.get("status","?"), "category": c.get("category","?"),
             "strike": c.get("strike",0), "notes": (c.get("notes") or "")[:300],
             "updated": c.get("updated","")}
        b = classify_ks(c.get("status"))
        (a if b=="active" else d if b=="dead" else p if b=="pending" else u).append(e)
    for b in (a,d,p,u): b.sort(key=lambda x: x.get("updated") or "", reverse=True)
    return a, d, p, u

async def get_keystone_cases(session, force_refresh=False):
    now = time.time()
    async with bot.keystone_lock:
        cached, ts = bot.keystone_cache
        if cached is not None:
            if not force_refresh and now-ts < KEYSTONE_TTL: return cached, None
            if force_refresh and now-ts < KEYSTONE_DEBOUNCE: return cached, None
    try:
        async with session.get(KEYSTONE_API_URL, timeout=aiohttp.ClientTimeout(total=30)) as r:
            if r.status != 200: return None, f"HTTP {r.status}"
            data = await r.json()
            cases = data.get("cases", [])
            if not isinstance(cases, list): return None, "no cases array"
            async with bot.keystone_lock: bot.keystone_cache = (cases, time.time())
            return cases, None
    except asyncio.TimeoutError: return None, "timeout"
    except Exception as e: return None, str(e)[:80]

async def keystone_check(session, ids, force_refresh=False):
    cases, err = await get_keystone_cases(session, force_refresh)
    if cases is None:
        if KEYSTONE_FAIL_CLOSED: return {"status": CheckStatus.HIT, "details": f"down (fail-closed) — {err}"}
        return {"status": CheckStatus.ERROR, "details": f"Keystone — {err}"}
    a, d, p, u = ks_search(cases, ids)
    if a:
        refs = ", ".join(f"{c['source']} #{c['case_id']}" for c in a[:3])
        return {"status": CheckStatus.HIT, "details": f"LISTED — {len(a)} active: {refs}"}
    if p:
        refs = ", ".join(f"{c['source']} #{c['case_id']}" for c in p[:3])
        return {"status": CheckStatus.HIT, "details": f"PENDING — {len(p)}: {refs}"}
    if d:
        refs = ", ".join(f"{c['source']} #{c['case_id']}" for c in d[:3])
        return {"status": CheckStatus.PASS, "details": f"archived ({len(d)}): {refs}"}
    if u: return {"status": CheckStatus.SKIPPED, "details": f"{len(u)} unknown"}
    return {"status": CheckStatus.PASS, "details": "not in Keystone"}


# ==================== SIMMER / SNOW CORE ====================
async def simmer_rab_check(session, rid):
    if not SIMMER_API_KEY or SIMMER_API_KEY.startswith("PASTE"):
        return {"status": CheckStatus.SKIPPED, "details": "no key"}
    now = time.time()
    hit = _simmer_cache.get(rid)
    if hit and now - hit[1] < SIMMER_TTL:
        return hit[0]
    result = await _simmer_fetch(session, rid)
    if result["status"] in (CheckStatus.PASS, CheckStatus.HIT):
        _simmer_cache[rid] = (result, time.time())
    return result


async def _simmer_fetch(session, rid):
    try:
        async with session.get(f"{SIMMER_API_URL}/checkuser/rab/{rid}",
                                headers={"Authorization": f"Bearer {SIMMER_API_KEY}"},
                                timeout=aiohttp.ClientTimeout(total=10)) as r:
            text = await r.text()
            if r.status == 401: return {"status": CheckStatus.SKIPPED, "details": "auth"}
            if r.status == 403: return {"status": CheckStatus.SKIPPED, "details": "no perm"}
            if r.status == 429: return {"status": CheckStatus.SKIPPED, "details": "rate limit"}
            if r.status != 200: return {"status": CheckStatus.SKIPPED, "details": f"HTTP {r.status}"}
            try: data = await r.json()
            except: return {"status": CheckStatus.SKIPPED, "details": "non-JSON"}
            if not data.get("success"): return {"status": CheckStatus.SKIPPED, "details": "success=false"}
            d = data.get("data") or {}
            flag = d.get("flagType", 0)
            if flag == 0: return {"status": CheckStatus.PASS, "details": "not in RAB"}
            st = d.get("stats") or {}
            try: cs = f"{float(d.get('confidence',0))*100:.0f}%"
            except: cs = str(d.get('confidence'))
            return {"status": CheckStatus.HIT,
                    "details": f"flagType={flag} conf={cs} · {st.get('totalSessions',0)} sessions · {st.get('messages',0)} msgs · {st.get('totalPlaytime','?')}"}
    except asyncio.TimeoutError: return {"status": CheckStatus.SKIPPED, "details": "timeout"}
    except Exception as e: return {"status": CheckStatus.SKIPPED, "details": str(e)[:80]}


async def get_snow_core(session, force_refresh=False):
    if not SNOW_CORE_SHEET_ID:
        return {}, None  # no sheet configured — empty dict means "no active bans"
    now = time.time()
    async with bot.snow_core_lock:
        cached, ts = bot.snow_core_cache
        if cached is not None:
            if not force_refresh and now-ts < BLACKLIST_TTL: return cached, None
            if force_refresh and now-ts < BLACKLIST_DEBOUNCE: return cached, None
    ts_ms = int(time.time()*1000)
    url = f"https://docs.google.com/spreadsheets/d/{SNOW_CORE_SHEET_ID}/gviz/tq?tqx=out:json&gid={SNOW_CORE_GID}&_nocache={ts_ms}"
    try:
        async with session.get(url, headers={"Cache-Control": "no-cache"}) as r:
            if r.status != 200: return None, f"HTTP {r.status}"
            text = await r.text()
            s, e = text.find("{"), text.rfind("}")+1
            if s == -1 or e == 0: return None, "no JSON"
            data = json.loads(text[s:e])
            rows = data.get("table", {}).get("rows", [])
            active = {}
            for row in rows:
                cells = row.get("c", [])
                if len(cells) < 10: continue
                if not cells[3]: continue
                try: rid = int(float(cells[3].get("v")))
                except: continue
                if not _is_true(cells[9] if len(cells) > 9 else None): continue
                uname = _cell_str(cells[1]) if len(cells)>1 else ""
                reason = _cell_str(cells[4]) if len(cells)>4 else ""
                active[rid] = (uname, reason)
            async with bot.snow_core_lock: bot.snow_core_cache = (active, time.time())
            return active, None
    except asyncio.TimeoutError: return None, "timeout"
    except Exception as e: return None, str(e)[:60]


async def snow_core_check(session, rid, force_refresh=False):
    active, err = await get_snow_core(session, force_refresh)
    if active is None: return {"status": CheckStatus.ERROR, "details": f"Snow Core — {err}"}
    if rid in active:
        u, r = active[rid]
        return {"status": CheckStatus.HIT, "details": f"active ban — {r or 'on list'} (user `{u or rid}`)"}
    return {"status": CheckStatus.PASS, "details": f"not banned ({len(active)} active)"}


# ==================== SANITIZE ====================
def sanitize_public_reason(result):
    if result.get("internal_error"): return "Verification temporarily unavailable, please try again shortly."
    r = result.get("reason") or ""
    rl = r.lower()
    if r == "User is blacklisted" or "user blacklist" in rl: return "User is blacklisted"
    if "discord account" in rl and "days old" in rl:
        return "Your Discord account does not meet the minimum age requirement."
    if "less than 2 weeks" in rl or "less than 2 weeks old" in rl:
        return "Your Roblox account is too new to be accepted."
    if "not willing to join" in rl:
        return "You indicated you are not willing to join the group."
    if "roblox account is banned" in rl:
        return "Your Roblox account is banned."
    if "multi-account" in rl: return "Your account is associated with other accounts in our system."
    if any(k in rl for k in ("roblox watcher","exploit watcher","xtracker","keystone","simmer","rab",
                              "snow core","external database","facility ban","external db")):
        return "You have been flagged by our screening system."
    if "blacklisted roblox group" in rl: return "You are a member of a Roblox group that is not permitted here."
    if "bloxlink mismatch" in rl: return "Your typed username does not match your Bloxlink account."
    return r


def format_missing_message(missing):
    if not missing: return "Please follow the format."
    return "Please follow the format. You are missing:\n" + "\n".join(f"- {m}" for m in missing)


def is_format_template(c):
    if not c: return False
    low = c.lower()
    hp = ("( yes/no )" in low or "(yes/no)" in low or "w/out explanation" in low)
    hd = bool(re.search(r'^\s*\**\s*format\s*\**\s*$', low, re.MULTILINE))
    br = bd = False
    for line in c.splitlines():
        l = line.lower().strip()
        if re.fullmatch(r'[-*\s]*roblox user\s*[:\-]?\s*\**\s*', l): br = True
        if re.fullmatch(r'[-*\s]*discord user\s*[:\-]?\s*\**\s*', l): bd = True
    if br and bd: return True
    if hd and (br or bd or hp): return True
    if hp and (br or bd): return True
    return False


def looks_like_application(c):
    if not c or is_format_template(c): return False
    low = c.lower()
    if any(k in low for k in ("roblox user","discord user","clanning","x-tracker","xtracker","willing to join")): return True
    return len([l for l in c.splitlines() if l.strip()]) >= 4


def parse_recruitment_message(c):
    r = {"roblox_username": None, "discord_username": None, "clanning_experience": None,
         "xtracker_self": None, "willing_to_join": None}
    lines = [l.strip() for l in c.splitlines() if l.strip()]
    def clean(v):
        v = re.sub(r'^[\-\*`:.\s]+', '', v); v = re.sub(r'[\*`.,;]+$', '', v)
        return re.sub(r'^\(|\)$', '', v).strip()
    def is_noise(line):
        if re.fullmatch(r'(?:<@!?\d+>\s*)+', line): return True
        if re.fullmatch(r'(?:@[\w.]+\s*)+', line): return True
        if line.startswith('-#') or line.startswith('>#'): return True
        return False
    def after(line, kw):
        i = line.lower().find(kw)
        return None if i == -1 else clean(line[i+len(kw):])
    lbl = ("roblox user","discord user","clanning","x-tracker","xtracker","x tracker","willing to join","tag/mention")
    for line in lines:
        low = line.lower()
        if "roblox user" in low and r["roblox_username"] is None:
            v = after(line, "roblox user"); r["roblox_username"] = v.lstrip('@').strip() if v else None
        if "discord user" in low and r["discord_username"] is None:
            v = after(line, "discord user"); r["discord_username"] = v if v else None
        if "clanning experience" in low and r["clanning_experience"] is None:
            r["clanning_experience"] = parse_clanning(low)
        if ("x-tracker" in low or "xtracker" in low or "x tracker" in low) and r["xtracker_self"] is None:
            r["xtracker_self"] = parse_yes_no(low)
        if "willing to join" in low and r["willing_to_join"] is None:
            r["willing_to_join"] = parse_yes_no(low)
    if not r["roblox_username"]:
        cands = [l for l in lines if not is_noise(l) and not any(k in l.lower() for k in lbl)]
        if cands:
            first = clean(cands[0])
            if first and " " not in first: r["roblox_username"] = first.lstrip('@').strip()
        if len(cands) > 1:
            s = clean(cands[1])
            if s and " " not in s: r["discord_username"] = s
        yn = [l for l in cands[2:10] if parse_yes_no(l)]
        if len(yn) >= 1 and r["clanning_experience"] is None: r["clanning_experience"] = parse_clanning(yn[0])
        if len(yn) >= 3:
            if r["xtracker_self"] is None: r["xtracker_self"] = parse_yes_no(yn[1])
            if r["willing_to_join"] is None: r["willing_to_join"] = parse_yes_no(yn[2])
        elif len(yn) >= 2:
            if r["willing_to_join"] is None: r["willing_to_join"] = parse_yes_no(yn[1])
    return r


def missing_format_fields(p):
    m = []
    if not p.get("roblox_username"): m.append("Roblox username")
    if not p.get("discord_username"): m.append("Discord username")
    if not p.get("clanning_experience"): m.append("Clanning experience answer")
    if not p.get("willing_to_join"): m.append("Willing to join answer")
    return m


# ==================== ROBLOX HTTP ====================
USER_DOMAINS  = ("users.rotunnel.com", "users.roproxy.com", "users.roblox.com")
GROUP_DOMAINS = ("groups.rotunnel.com", "groups.roproxy.com", "groups.roblox.com")


async def roblox_user_lookup(session, username):
    u = (username or "").lstrip('@').strip()
    if not u: return None, "not_found"
    key = u.lower()
    now = time.time()
    cached = _roblox_name_to_id.get(key)
    if cached and now - cached[2] < ROBLOX_LOOKUP_TTL:
        _record_race_winner(f"lookup:{key}", "(cached)")
        return {"id": cached[0], "name": cached[1], "displayName": cached[1]}, ""

    payload = {"usernames": [u], "excludeBannedUsers": False}
    domains = bot._filter_healthy(USER_DOMAINS)

    async def _try(domain):
        try:
            async with session.post(
                f"https://{domain}/v1/usernames/users", json=payload,
                timeout=aiohttp.ClientTimeout(total=RACE_TIMEOUT_SEC),
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("data"):
                        bot._mark_domain_ok(domain)
                        return data["data"][0], "", domain
                    return None, "not_found", None
                if r.status == 404: return None, "not_found", None
                bot._mark_domain_error(domain)
                return None, f"{domain}: HTTP {r.status}", None
        except asyncio.TimeoutError:
            bot._mark_domain_error(domain); return None, f"{domain}: timeout", None
        except aiohttp.ClientConnectorError:
            bot._mark_domain_error(domain); return None, f"{domain}: conn", None
        except Exception as e:
            bot._mark_domain_error(domain); return None, f"{domain}: {type(e).__name__}", None

    tasks = [asyncio.create_task(_try(d)) for d in domains]
    errors = []; nf = 0
    try:
        for fut in asyncio.as_completed(tasks):
            result, err, winner = await fut
            if result is not None:
                for t in tasks:
                    if not t.done(): t.cancel()
                _roblox_name_to_id[key] = (result["id"], result["name"], time.time())
                _record_race_winner(f"lookup:{key}", winner or "(unknown)")
                return result, ""
            if err == "not_found": nf += 1
            else: errors.append(err)
        if nf > 0: return None, "not_found"
        return None, "lookup_failed: " + " | ".join(errors)
    finally:
        for t in tasks:
            if not t.done(): t.cancel()


async def roblox_user_info(session, uid):
    now = time.time()
    hit = _roblox_info_cache.get(uid)
    if hit and now - hit[1] < ROBLOX_INFO_TTL:
        _record_race_winner(f"info:{uid}", "(cached)")
        return hit[0], ""
    body, err, winner, _ = await _race_200(session, USER_DOMAINS, f"/v1/users/{uid}")
    if body is not None:
        _roblox_info_cache[uid] = (body, time.time())
        _record_race_winner(f"info:{uid}", winner or "(unknown)")
        return body, ""
    return None, err or "no response"


async def roblox_user_groups(session, uid):
    now = time.time()
    hit = _roblox_groups_cache.get(uid)
    if hit and now - hit[1] < ROBLOX_GROUPS_TTL:
        _record_race_winner(f"groups:{uid}", "(cached)")
        return hit[0], ""
    body, err, winner, _ = await _race_200(session, GROUP_DOMAINS, f"/v1/users/{uid}/groups/roles")
    if body is not None:
        data = body.get("data", []) if isinstance(body, dict) else []
        _roblox_groups_cache[uid] = (data, time.time())
        _record_race_winner(f"groups:{uid}", winner or "(unknown)")
        return data, ""
    return None, err or "no response"


async def roblox_username_history(session, uid):
    now = time.time()
    hit = _roblox_hist_cache.get(uid)
    if hit and now - hit[1] < ROBLOX_HIST_TTL:
        _record_race_winner(f"hist:{uid}", "(cached)")
        return hit[0], ""
    body, err, winner, got_404 = await _race_200(
        session, USER_DOMAINS,
        f"/v1/users/{uid}/username-history?limit=50&sortOrder=Desc")
    if body is not None:
        data = body.get("data", []) if isinstance(body, dict) else []
        _roblox_hist_cache[uid] = (data, time.time())
        _record_race_winner(f"hist:{uid}", winner or "(unknown)")
        return data, ""
    if got_404:
        _roblox_hist_cache[uid] = ([], time.time())
        _record_race_winner(f"hist:{uid}", "(404)")
        return [], ""
    return None, err or "no response"


async def _fetch_gviz(session, gid, sid=None):
    _sid = sid or BLACKLIST_SHEET_ID
    if not _sid: return None, "no sheet configured"
    ts = int(time.time()*1000)
    url = f"https://docs.google.com/spreadsheets/d/{_sid}/gviz/tq?tqx=out:json&gid={gid}&_nocache={ts}"
    try:
        async with session.get(url, headers={"Cache-Control": "no-cache"}) as r:
            if r.status != 200: return None, f"HTTP {r.status}"
            text = await r.text()
            s, e = text.find("{"), text.rfind("}")+1
            if s == -1 or e == 0: return None, "no JSON"
            return json.loads(text[s:e]), None
    except asyncio.TimeoutError: return None, "timeout"
    except Exception as e: return None, type(e).__name__


async def get_group_blacklist(session, force_refresh=False):
    if not BLACKLIST_SHEET_ID:
        return [], None
    now = time.time()
    async with bot.group_blacklist_lock:
        cached, ts = bot.group_blacklist_cache
        if cached is not None:
            if not force_refresh and now-ts < BLACKLIST_TTL: return cached, None
            if force_refresh and now-ts < BLACKLIST_DEBOUNCE: return cached, None
    data, err = await _fetch_gviz(session, GROUP_BLACKLIST_GID)
    if data is None: return None, err
    ids = []
    for row in data.get("table", {}).get("rows", []):
        cells = row.get("c", [])
        if len(cells) < 2 or not cells[1]: continue
        g = parse_group_id_from_cell(cells[1])
        if g: ids.append(g)
    async with bot.group_blacklist_lock: bot.group_blacklist_cache = (ids, time.time())
    return ids, None


async def get_user_blacklist(session, force_refresh=False):
    if not BLACKLIST_SHEET_ID:
        return [], None
    now = time.time()
    async with bot.user_blacklist_lock:
        cached, ts = bot.user_blacklist_cache
        if cached is not None:
            if not force_refresh and now-ts < BLACKLIST_TTL: return cached, None
            if force_refresh and now-ts < BLACKLIST_DEBOUNCE: return cached, None
    data, err = await _fetch_gviz(session, USER_BLACKLIST_GID)
    if data is None: return None, err
    entries = []
    for row in data.get("table", {}).get("rows", []):
        cells = row.get("c", [])
        def g(i): return "" if i >= len(cells) else _cell_str(cells[i])
        uname, raw = g(0), g(1)
        if uname.lower() == "username" or (not uname and not raw): continue
        did = re.sub(r'\D', '', raw)
        entries.append({"username": uname, "discord_id": did, "reason": g(2),
                        "date_applied": g(3), "end_date": g(4), "appealed": g(5)})
    async with bot.user_blacklist_lock: bot.user_blacklist_cache = (entries, time.time())
    return entries, None


def is_ubl_active(entry, today):
    ap = (entry.get("appealed") or "").strip().lower()
    if ap == "yes": return False
    er = (entry.get("end_date") or "").strip().lower()
    if er in ("", "n/a", "na", "none", "-"): return True
    ed = parse_dmy(entry["end_date"])
    return True if ed is None else today <= ed


def find_user_blacklist_match(entries, did, rbx_un, past_names=None):
    if not entries: return None, None
    ds = str(did).strip() if did else ""
    if ds:
        for e in entries:
            if e["discord_id"] and e["discord_id"] == ds: return e, "discord_id"
    names = []
    if rbx_un: names.append((rbx_un.lower(), "current username"))
    for pn in (past_names or []):
        if pn: names.append((pn.lower(), f"past username '{pn}'"))
    for needle, label in names:
        for e in entries:
            if e["username"] and e["username"].lower() == needle: return e, label
    return None, None


async def xtracker_check(session, endpoint, uid):
    if not XTRACKER_API_KEY or XTRACKER_API_KEY.startswith("PASTE"):
        return {"status": CheckStatus.SKIPPED, "details": "no key"}
    await bot.xtracker_limiter.acquire()
    url = f"https://api.xtracker.xyz/api/{endpoint}?id={uid}"
    try:
        async with session.get(url, headers={"Authorization": XTRACKER_API_KEY}) as r:
            text = await r.text()
            if r.status == 404:
                low = text.lower()
                if "not found" in low or "notfound" in low:
                    bot.xtracker_limiter.report_ok()
                    return {"status": CheckStatus.PASS, "details": "not in DB"}
                return {"status": CheckStatus.SKIPPED, "details": "HTTP 404"}
            if r.status in (401, 403): return {"status": CheckStatus.SKIPPED, "details": f"HTTP {r.status} auth"}
            if r.status == 429:
                bot.xtracker_limiter.report_429()
                logger.warning(f"Xtracker 429 on {endpoint}/{uid} — limiter now {bot.xtracker_limiter.interval:.2f}s")
                return {"status": CheckStatus.SKIPPED, "details": "rate limited"}
            if r.status != 200: return {"status": CheckStatus.SKIPPED, "details": f"HTTP {r.status}"}
            bot.xtracker_limiter.report_ok()
            try: data = json.loads(text)
            except: return {"status": CheckStatus.HIT, "details": text[:300]}
            if data is None or data == "" or data == "null": return {"status": CheckStatus.PASS, "details": "null"}
            if isinstance(data, dict):
                if data.get("error") and len(data) <= 2:
                    if "not found" in str(data.get("error","")).lower(): return {"status": CheckStatus.PASS, "details": "not in DB"}
                    return {"status": CheckStatus.SKIPPED, "details": "API error"}
                il = data.get("isListed")
                if il is False or il == 0: return {"status": CheckStatus.PASS, "details": "not listed"}
                if il is True or il == 1: return {"status": CheckStatus.HIT, "details": json.dumps(data)[:500]}
                for k in ("alts","evidence","strikes","strike","cases","user","data"):
                    if data.get(k): return {"status": CheckStatus.HIT, "details": json.dumps(data)[:500]}
                if not data: return {"status": CheckStatus.PASS, "details": "empty"}
                return {"status": CheckStatus.HIT, "details": f"unrecognised: {json.dumps(data)[:400]}"}
            if isinstance(data, list):
                return {"status": CheckStatus.HIT if data else CheckStatus.PASS,
                        "details": json.dumps(data)[:500] if data else "empty"}
            return {"status": CheckStatus.PASS, "details": "unrecognised"}
    except asyncio.TimeoutError: return {"status": CheckStatus.SKIPPED, "details": "timeout"}
    except Exception as e: return {"status": CheckStatus.SKIPPED, "details": str(e)[:80]}


async def watcher_check(session, did, key, product):
    if not key or key.startswith("PASTE"):
        return {"status": CheckStatus.SKIPPED, "details": "no key"}
    url = f"https://api.robloxwatcher.com/api/v1/{product}/search/{did}"
    try:
        async with session.get(url, headers={"Authorization": f"Bearer {key}"}) as r:
            if r.status != 200: return {"status": CheckStatus.SKIPPED, "details": f"HTTP {r.status}"}
            data = await r.json()
            if data.get("flagged"):
                return {"status": CheckStatus.HIT, "details": f"flagged in {len(data.get('guilds', []))} server(s)"}
            return {"status": CheckStatus.PASS, "details": "clean"}
    except asyncio.TimeoutError: return {"status": CheckStatus.SKIPPED, "details": "timeout"}
    except Exception as e: return {"status": CheckStatus.SKIPPED, "details": str(e)[:80]}


# ==================== PROGRESS ====================
def _render_bar(p):
    f = int(round(max(0, min(1, p)) * PROGRESS_BAR_LEN))
    return PROGRESS_FILLED * f + PROGRESS_EMPTY * (PROGRESS_BAR_LEN - f)


class ProgressReporter:
    def __init__(self, ch, user):
        self.channel = ch; self.user = user; self.msg = None; self._last = 0.0
    def _embed(self, idx):
        lines = []
        for i, st in enumerate(BGC_STAGES):
            if i < idx: lines.append(f"~~{BGC_STAGE_EMOJI[i]} {st}~~ ✅")
            elif i == idx: lines.append(f"**{BGC_STAGE_EMOJI[i]} {st}…**")
            else: lines.append(f"⚪ {st}")
        pct = int((idx+1)/len(BGC_STAGES)*100)
        bar = _render_bar((idx+1)/len(BGC_STAGES))
        e = discord.Embed(title=branded(f"🔍 Verifying {self.user.display_name}"),
                          description=f"{self.user.mention}\n\n" + "\n".join(lines) + f"\n\n`{bar}` **{pct}%**",
                          color=T.STAGE_COLORS[min(idx, len(T.STAGE_COLORS)-1)])
        e.set_thumbnail(url=self.user.display_avatar.url)
        e.set_footer(text=f"Step {idx+1} of {len(BGC_STAGES)} · do not edit your message")
        return e
    async def start(self):
        try:
            self.msg = await self.channel.send(embed=self._embed(0))
            self._last = time.monotonic()
        except: self.msg = None
    async def advance(self, idx):
        if self.msg is None: return
        wait = PROGRESS_MIN_DWELL - (time.monotonic() - self._last)
        if wait > 0: await asyncio.sleep(wait)
        try:
            await self.msg.edit(embed=self._embed(idx))
            self._last = time.monotonic()
        except: pass
    async def finish(self):
        if self.msg is None: return
        wait = PROGRESS_MIN_DWELL - (time.monotonic() - self._last)
        if wait > 0: await asyncio.sleep(wait)
        try: await self.msg.delete()
        except:
            try: await self.msg.edit(content="*Verification complete.*", embed=None)
            except: pass


# ==================== WARM CACHE ====================
async def _warm_dns():
    await bot.wait_until_ready()
    import socket
    domains = [
        "users.rotunnel.com", "users.roproxy.com", "users.roblox.com",
        "groups.rotunnel.com", "groups.roproxy.com", "groups.roblox.com",
        "api.blox.link", "api.xtracker.xyz", "api.robloxwatcher.com",
        "api.keystone-swords.com", "api.simmer.icu",
        "docs.google.com",
    ]
    loop = asyncio.get_running_loop()
    for d in domains:
        try:
            await loop.run_in_executor(None, socket.gethostbyname, d)
        except Exception:
            pass
    logger.info("DNS pre-resolve complete")


async def _warm_caches():
    await bot.wait_until_ready()
    logger.info("Cache pre-warm starting")
    t0 = time.perf_counter()
    try:
        await asyncio.gather(
            get_group_blacklist(bot.session, force_refresh=True),
            get_user_blacklist(bot.session, force_refresh=True),
            get_keystone_cases(bot.session, force_refresh=True),
            get_snow_core(bot.session, force_refresh=True),
            *[fetch_external_db(bot.session, cfg, force_refresh=True)
              for cfg in EXTERNAL_DATABASES],
            return_exceptions=True,
        )
        await asyncio.gather(
            _health_endpoint(bot.session, "users.rotunnel.com", "/v1/users/1"),
            _health_endpoint(bot.session, "groups.rotunnel.com", "/v1/users/1/groups/roles"),
            _health_endpoint(bot.session, "users.roproxy.com", "/v1/users/1"),
            _health_endpoint(bot.session, "groups.roproxy.com", "/v1/users/1/groups/roles"),
            return_exceptions=True,
        )
        logger.info(f"Cache pre-warm complete in {int((time.perf_counter()-t0)*1000)}ms")
    except Exception:
        logger.warning("Cache pre-warm failed", exc_info=True)


async def _cache_keep_warm_loop():
    await bot.wait_until_ready()
    shortest = min(BLACKLIST_TTL, EXTERNAL_DB_TTL, KEYSTONE_TTL)
    await asyncio.sleep(shortest - 30)
    while not bot.is_closed():
        try:
            t0 = time.perf_counter()
            await asyncio.gather(
                get_group_blacklist(bot.session, force_refresh=True),
                get_user_blacklist(bot.session, force_refresh=True),
                get_keystone_cases(bot.session, force_refresh=True),
                get_snow_core(bot.session, force_refresh=True),
                *[fetch_external_db(bot.session, cfg, force_refresh=True)
                  for cfg in EXTERNAL_DATABASES],
                return_exceptions=True,
            )
            logger.info(f"Cache keep-warm in {int((time.perf_counter()-t0)*1000)}ms")
            cutoff = (datetime.now(timezone.utc) - timedelta(days=PREEMPTIVE_CLEANUP_DAYS)).isoformat()
            async with bot.db_lock:
                await bot.db.execute(
                    "DELETE FROM preemptive_scans WHERE "
                    "(identity_scanned_at IS NULL OR identity_scanned_at < ?) AND "
                    "(xtracker_scanned_at IS NULL OR xtracker_scanned_at < ?) AND "
                    "(freshness_scanned_at IS NULL OR freshness_scanned_at < ?)",
                    (cutoff, cutoff, cutoff))
                await bot.db.commit()
        except Exception:
            logger.warning("Cache keep-warm failed", exc_info=True)
        await asyncio.sleep(shortest - 30)


async def _keep_connections_warm_loop():
    await bot.wait_until_ready()
    endpoints = [
        ("users.rotunnel.com",  "/v1/users/1"),
        ("users.roproxy.com",   "/v1/users/1"),
        ("groups.rotunnel.com", "/v1/users/1/groups/roles"),
        ("groups.roproxy.com",  "/v1/users/1/groups/roles"),
    ]
    while not bot.is_closed():
        try:
            await asyncio.gather(
                *[_health_endpoint(bot.session, d, p) for d, p in endpoints],
                return_exceptions=True)
        except Exception:
            pass
        await asyncio.sleep(KEEPALIVE_INTERVAL_SEC)


# ==================== HEALTH ENDPOINT HELPER ====================
async def _health_endpoint(session, domain, path):
    try:
        async with session.get(
            f"https://{domain}{path}",
            timeout=aiohttp.ClientTimeout(total=2.0),
        ) as r:
            return {"ok": r.status == 200, "error": None if r.status == 200 else f"HTTP {r.status}"}
    except asyncio.TimeoutError: return {"ok": False, "error": "timeout"}
    except aiohttp.ClientConnectorError: return {"ok": False, "error": "conn failed"}
    except Exception as e: return {"ok": False, "error": type(e).__name__}


# ==================== COMPONENTS ====================
class Paginator(discord.ui.View):
    def __init__(self, pages, author_id, timeout=180):
        super().__init__(timeout=timeout)
        self.pages = pages; self.page = 0; self.author_id = author_id; self._message = None
        self._sync()
    def _sync(self):
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= len(self.pages)-1
        self.count_btn.label = f"{self.page+1} / {len(self.pages)}"
    async def interaction_check(self, i): return i.user.id == self.author_id
    async def on_timeout(self):
        for c in self.children: c.disabled = True
        if self._message is not None:
            try: await self._message.edit(view=self)
            except: pass
    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, i, b):
        self.page -= 1; self._sync(); await i.response.edit_message(embed=self.pages[self.page], view=self)
    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True)
    async def count_btn(self, i, b): pass
    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, i, b):
        self.page += 1; self._sync(); await i.response.edit_message(embed=self.pages[self.page], view=self)


class ConfirmResetView(discord.ui.View):
    def __init__(self, aid):
        super().__init__(timeout=45); self.author_id = aid; self.confirmed = False; self._message = None
    async def interaction_check(self, i): return i.user.id == self.author_id
    async def on_timeout(self):
        for c in self.children: c.disabled = True
        if self._message is not None:
            try: await self._message.edit(view=self)
            except: pass
    @discord.ui.button(label="Wipe settings", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def ok(self, i, b):
        self.confirmed = True; self.stop()
        await i.response.edit_message(content=branded("🟢 Wiping…"), embed=None, view=None)
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def no(self, i, b):
        self.confirmed = False; self.stop()
        await i.response.edit_message(content=branded("Cancelled."), embed=None, view=None)


class ConfirmWipeView(discord.ui.View):
    def __init__(self, aid, target_display):
        super().__init__(timeout=60); self.author_id = aid; self.target_display = target_display
        self.confirmed = False; self._message = None
    async def interaction_check(self, i): return i.user.id == self.author_id
    async def on_timeout(self):
        for c in self.children: c.disabled = True
        if self._message is not None:
            try: await self._message.edit(view=self)
            except: pass
    @discord.ui.button(label="Wipe user", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def ok(self, i, b):
        self.confirmed = True; self.stop()
        await i.response.edit_message(content=branded(f"Wiping `{self.target_display}`…"), embed=None, view=None)
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def no(self, i, b):
        self.confirmed = False; self.stop()
        await i.response.edit_message(content=branded("Cancelled."), embed=None, view=None)


async def _rerun_bgc(result, gid):
    p = result.get("profile", {})
    did = p.get("discord_id"); un = p.get("roblox_username")
    async with bot.bgc_semaphore:
        if un and did:
            return await run_bgc_core(un, did, gid, message_id=None, parsed_self_report=None,
                                       force_blacklist_refresh=True, skip_preemptive=True)
        if un: return await run_bgc_by_username(un, gid, force_blacklist_refresh=True)
        if did: return await run_bgc_by_discord_id(did, gid, force_blacklist_refresh=True)
    return None


class BGCResultView(discord.ui.View):
    def __init__(self, result, gid, aid):
        super().__init__(timeout=300); self.result = result; self.guild_id = gid; self.author_id = aid
    async def interaction_check(self, i): return i.user.id == self.author_id
    @discord.ui.button(label="Copy Roblox ID", style=discord.ButtonStyle.secondary, emoji="📋")
    async def copy_id(self, i, b):
        rid = self.result["profile"].get("roblox_id")
        await i.response.send_message(f"`{rid}`" if rid else "No Roblox ID", ephemeral=True)
    @discord.ui.button(label="Re-run (dry)", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def rerun(self, i, b):
        await i.response.defer(ephemeral=True)
        new = await _rerun_bgc(self.result, self.guild_id)
        if new is None:
            await i.followup.send(branded("No usable identity."), ephemeral=True); return
        await i.followup.send(embed=build_result_embed(new, "Re-run (dry)", runner=i.user), ephemeral=True)


class _DebugRerunView(discord.ui.View):
    def __init__(self, result, gid):
        super().__init__(timeout=300); self.result = result; self.guild_id = gid
    @discord.ui.button(label="Re-run (dry)", style=discord.ButtonStyle.secondary, emoji="🔄")
    async def rerun(self, i, b):
        await i.response.defer(ephemeral=True)
        new = await _rerun_bgc(self.result, self.guild_id)
        if new is None:
            await i.followup.send(branded("No usable identity."), ephemeral=True); return
        await i.followup.send(embed=build_result_embed(new, "Re-run (dry)", runner=i.user), ephemeral=True)


# ==================== PERSIST ====================
async def _persist_check_logs(bgc_id, checks):
    try:
        async with bot.db_lock:
            await bot.db.executemany(
                "INSERT INTO check_logs (bgc_id, check_name, status, details) VALUES (?,?,?,?)",
                [(bgc_id, c["name"], c["status"], c.get("details", "")) for c in checks])
            await bot.db.commit()
    except Exception:
        logger.warning(f"Persist check_logs failed for bgc {bgc_id}", exc_info=True)


# ==================== BGC CORE ====================
async def run_bgc_core(username, discord_id, guild_id, message_id=None,
                       parsed_self_report=None, force_blacklist_refresh=True,
                       check_banned=False, progress=None, member=None, timings=None,
                       skip_db_history=False, skip_preemptive=False):
    async def _adv(idx):
        if progress:
            try: await progress(idx)
            except: pass

    def _s(coro, name):
        return _spawn(coro, name=name, timings=timings)

    checks, profile, reason, passed = [], {}, None, True
    session = bot.session
    today = datetime.now(timezone.utc).date()

    # ── Preemptive lookup ──
    preemptive = None
    if discord_id and guild_id and not skip_preemptive:
        preemptive = await _preemptive_lookup(discord_id, guild_id)
    have_preemptive_id = bool(
        preemptive and preemptive.get("blox_id") and preemptive.get("id_fresh"))
    blox_known_not_linked = bool(
        preemptive and preemptive.get("id_fresh")
        and preemptive.get("blox_status") == "not_linked")

    late_cache_hit = None
    if not (have_preemptive_id or blox_known_not_linked) and discord_id and guild_id:
        late = _bloxlink_late_cache.get((discord_id, guild_id))
        if late and time.time() - late[2] < BLOXLINK_LATE_TTL:
            late_cache_hit = late

    if preemptive:
        if have_preemptive_id:
            bot._metrics_preemptive_hits += 1
        else:
            bot._metrics_preemptive_misses += 1
    else:
        bot._metrics_preemptive_misses += 1

    # ── TIER 0 ──
    t0 = {}
    if discord_id:
        t0["ubl"] = _s(get_user_blacklist(session, force_refresh=force_blacklist_refresh), "user_blacklist")
        t0["dcage"] = _s(check_discord_age(discord_id), "discord_age")
        t0["rw"] = _s(watcher_check(session, discord_id, RW_API_KEY, "robloxwatcher"), "roblox_watcher")
        t0["ew"] = _s(watcher_check(session, discord_id, EW_API_KEY, "exploitwatcher"), "exploit_watcher")
    t0["gbl"] = _s(get_group_blacklist(session, force_refresh=force_blacklist_refresh), "group_blacklist")
    if (BLOXLINK_ENABLED and discord_id and guild_id
            and not (have_preemptive_id or blox_known_not_linked or late_cache_hit)):
        t0["blox"] = _s(bloxlink_discord_to_roblox(session, guild_id, discord_id), "bloxlink")
    if username:
        t0["typed"] = _s(roblox_user_lookup(session, username), "typed_lookup")
    if member:
        nickname = (getattr(member, "nick", None) or "").strip().lstrip("@")
        if (nickname and re.fullmatch(r'[A-Za-z0-9_]{3,20}', nickname)
                and nickname.lower() != (username or "").lower()):
            t0["nickname"] = _s(roblox_user_lookup(session, nickname), "nickname_lookup")

    # ── TIER 1 ──
    t1 = {}
    def _fire_t1_for(rid, cached=None):
        if rid is None or f"info_{rid}" in t1: return
        cached = cached or {}
        if cached.get("info"):
            t1[f"info_{rid}"] = _resolved(cached["info"], "")
        else:
            t1[f"info_{rid}"] = _s(roblox_user_info(session, rid), f"user_info_{rid}")
        if cached.get("hist") is not None:
            t1[f"hist_{rid}"] = _resolved(cached["hist"], "")
        else:
            t1[f"hist_{rid}"] = _s(roblox_username_history(session, rid), f"username_history_{rid}")
        if cached.get("groups") is not None:
            t1[f"groups_{rid}"] = _resolved(cached["groups"], "")
        else:
            t1[f"groups_{rid}"] = _s(roblox_user_groups(session, rid), f"user_groups_{rid}")
        if cached.get("xt_reg"):
            t1[f"xtracker_reg_{rid}"] = _resolved_direct(cached["xt_reg"])
        else:
            t1[f"xtracker_reg_{rid}"] = _s(xtracker_check(session, "registry/user", rid), f"xtracker_reg_{rid}")
        if cached.get("xt_own"):
            t1[f"xtracker_own_{rid}"] = _resolved_direct(cached["xt_own"])
        else:
            t1[f"xtracker_own_{rid}"] = _s(xtracker_check(session, "ownership/user", rid), f"xtracker_own_{rid}")
        if cached.get("simmer"):
            t1[f"simmer_rab_{rid}"] = _resolved_direct(cached["simmer"])
        else:
            t1[f"simmer_rab_{rid}"] = _s(simmer_rab_check(session, rid), f"simmer_{rid}")
        t1[f"snow_{rid}"] = _s(snow_core_check(session, rid, force_refresh=force_blacklist_refresh), f"snow_{rid}")

    if parsed_self_report:
        if parsed_self_report.get("willing_to_join") == "no":
            passed = False; reason = reason or "User said they are not willing to join"
            checks.append({"name": "WillingToJoin", "status": CheckStatus.HIT, "details": "answered 'no'"})
        elif parsed_self_report.get("willing_to_join") == "yes":
            checks.append({"name": "WillingToJoin", "status": CheckStatus.PASS, "details": "yes"})

    await _adv(1)

    all_discord_ids = {discord_id} if discord_id else set()
    dc_names = set()
    if member:
        if getattr(member, "name", None): dc_names.add(member.name)
        if getattr(member, "display_name", None): dc_names.add(member.display_name)
    if parsed_self_report and parsed_self_report.get("discord_username"):
        dc_names.add(parsed_self_report["discord_username"])

    db_history = []
    if not skip_db_history and discord_id:
        db_history = await get_all_roblox_history(discord_id, guild_id)
        if db_history:
            _fire_t1_for(db_history[0][0])
        for hid, _ in db_history[1:]:
            if hid and f"hist_{hid}" not in t1:
                t1[f"hist_{hid}"] = _s(roblox_username_history(session, hid), f"hist_hist_{hid}")

    # ── Fire T1 from preemptive cache (primary ID + historical cached IDs) ──
    if have_preemptive_id:
        xt_by_id = preemptive.get("xtracker_by_id") or {}
        primary_rid = preemptive["blox_id"]
        primary_xt = xt_by_id.get(str(primary_rid), {})
        _fire_t1_for(primary_rid, cached={
            "info": preemptive["info"],
            "hist": preemptive["hist"],
            "groups": preemptive["groups"],
            "xt_reg": primary_xt.get("reg"),
            "xt_own": primary_xt.get("own"),
            "simmer": preemptive["simmer"],
        })
        for rid_str, xt_data in xt_by_id.items():
            try: rid_int = int(rid_str)
            except: continue
            if rid_int == primary_rid: continue
            _fire_t1_for(rid_int, cached={
                "xt_reg": xt_data.get("reg"),
                "xt_own": xt_data.get("own"),
            })
        profile["preemptive_hit"] = True
        profile["bloxlink_status"] = preemptive.get("blox_status") or "preemptive"
        if preemptive.get("info"):
            profile["preemptive_name"] = preemptive["info"].get("name")
        if timings is not None:
            now_ts = time.perf_counter()
            timings.append({"name": "preemptive (cached)", "start": now_ts, "end": now_ts})

    # ── Race typed vs nickname ──
    typed_user, typed_err = (None, "not_found")
    nick_user = None
    fired_ids = {preemptive["blox_id"]} if have_preemptive_id else set()
    identity_pending = []
    if "typed" in t0: identity_pending.append(("typed", t0["typed"]))
    if "nickname" in t0: identity_pending.append(("nickname", t0["nickname"]))

    if identity_pending:
        fut_to_name = {asyncio.ensure_future(t): n for n, t in identity_pending}
        done, pending_set = await asyncio.wait(fut_to_name.keys(), return_when=asyncio.FIRST_COMPLETED)
        for fut in done:
            try: result, err = fut.result()
            except Exception: result, err = None, "error"
            name = fut_to_name[fut]
            if name == "typed": typed_user, typed_err = result, err
            elif name == "nickname": nick_user = result
            if result and result["id"] not in fired_ids:
                _fire_t1_for(result["id"]); fired_ids.add(result["id"])
        for fut in pending_set:
            try: result, err = await fut
            except Exception: result, err = None, "error"
            name = fut_to_name[fut]
            if name == "typed":
                typed_user, typed_err = result, err
                if result and result["id"] not in fired_ids:
                    _fire_t1_for(result["id"]); fired_ids.add(result["id"])
            elif name == "nickname":
                nick_user = result

    if not typed_user and nick_user:
        typed_user = nick_user
        typed_err = "nickname_fallback"
        profile["resolved_via_nickname"] = nick_user["name"]

    # ── T2 waves ──
    t2 = {}
    _multi_fired = set()
    fast_ids = set()
    fast_names = set()

    def _fire_t2(ids, names, tag, primary_rid=None):
        ids = set(ids); names = set(names)
        if not ids and not names: return
        ks = {str(x) for x in ids} | {n.lower().lstrip('@') for n in names}
        if ks:
            t2[f"keystone_{tag}"] = _s(keystone_check(session, ks, force_refresh=force_blacklist_refresh), f"keystone_{tag}")
        t2[f"ext_{tag}"] = _s(search_external_dbs(session, {
            "rbx_ids": ids, "rbx_usernames": names,
            "discord_ids": all_discord_ids, "discord_usernames": dc_names,
        }, force_refresh=force_blacklist_refresh), f"external_dbs_{tag}")
        if primary_rid is not None and primary_rid not in _multi_fired:
            _multi_fired.add(primary_rid)
            t2[f"multi_{primary_rid}"] = _s(detect_multi_account(guild_id, discord_id, primary_rid), f"multi_{primary_rid}")

    if have_preemptive_id:
        fast_ids.add(preemptive["blox_id"])
        if preemptive.get("info") and preemptive["info"].get("name"):
            fast_names.add(preemptive["info"]["name"])
        for h in (preemptive.get("hist") or []):
            if h.get("name"): fast_names.add(h["name"])
        _fire_t2(fast_ids, fast_names, "fast", primary_rid=preemptive["blox_id"])
    elif typed_user:
        info_t, _ = await t1[f"info_{typed_user['id']}"]
        hist_t, _ = await t1[f"hist_{typed_user['id']}"]
        if info_t and info_t.get("name"):
            fast_ids.add(typed_user["id"])
            fast_names.add(info_t["name"])
        for h in (hist_t or []):
            if h.get("name"): fast_names.add(h["name"])
        for hid, hname in db_history:
            if hid: fast_ids.add(hid)
            if hname: fast_names.add(hname)
        _fire_t2(fast_ids, fast_names, "fast", primary_rid=typed_user["id"])

    # ── Bloxlink with shield + late cache ──
    bloxlink_id = None
    bloxlink_status = "disabled"
    if "blox" in t0:
        blox_task = t0["blox"]
        try:
            bloxlink_id, bloxlink_status = await asyncio.wait_for(
                asyncio.shield(blox_task), timeout=BLOXLINK_HARD_TIMEOUT_MS / 1000.0)
        except asyncio.TimeoutError:
            bloxlink_id, bloxlink_status = None, "hard_timeout"
            bot._metrics_bloxlink_timeouts += 1
            logger.debug(f"Bloxlink hard timeout — shielding for late cache")
            def _cache_late(task, did=discord_id, gid=guild_id):
                if task.cancelled(): return
                try: rid, status = task.result()
                except Exception: return
                if rid and status == "ok":
                    _store_late_bloxlink(did, gid, rid, status)
            blox_task.add_done_callback(_cache_late)
    elif have_preemptive_id:
        bloxlink_id = preemptive["blox_id"]
        bloxlink_status = preemptive.get("blox_status") or "preemptive"
    elif blox_known_not_linked:
        bloxlink_status = "not_linked"
    elif late_cache_hit:
        bloxlink_id = late_cache_hit[0]
        bloxlink_status = (late_cache_hit[1] or "ok") + "_late"
        profile["bloxlink_late_cache"] = True

    if bloxlink_id and not have_preemptive_id:
        _fire_t1_for(bloxlink_id)

    blox_delta_names = set()
    if bloxlink_id and not have_preemptive_id:
        blox_info, _ = await t1[f"info_{bloxlink_id}"]
        blox_hist, _ = await t1[f"hist_{bloxlink_id}"]
        delta_ids = {bloxlink_id} - fast_ids
        if blox_info and blox_info.get("name") and blox_info["name"] not in fast_names:
            blox_delta_names.add(blox_info["name"])
        for h in (blox_hist or []):
            if h.get("name") and h["name"] not in fast_names:
                blox_delta_names.add(h["name"])
        if delta_ids or blox_delta_names:
            _fire_t2(delta_ids, blox_delta_names, "blox", primary_rid=bloxlink_id)

    # ── Resolve identity ──
    pre_info = None
    roblox_id = roblox_name = roblox_display = None

    if bloxlink_id:
        pre_info, _ = await t1[f"info_{bloxlink_id}"]
        if pre_info and pre_info.get("name"):
            roblox_id = bloxlink_id
            roblox_name = pre_info["name"]
            roblox_display = pre_info.get("displayName", roblox_name)
            profile["resolved_via"] = "bloxlink_preemptive" if have_preemptive_id else "bloxlink"
            profile["bloxlink_id"] = bloxlink_id
        else:
            bloxlink_id = None
            if typed_user:
                roblox_id = typed_user["id"]
                roblox_name = typed_user["name"]
                roblox_display = typed_user.get("displayName", roblox_name)
                profile["resolved_via"] = "username"
    elif typed_user:
        roblox_id = typed_user["id"]
        roblox_name = typed_user["name"]
        roblox_display = typed_user.get("displayName", roblox_name)
        profile["resolved_via"] = "username"

    if bloxlink_id and typed_user and typed_user["id"] != bloxlink_id:
        mm = f"typed `{typed_user['name']}` (`{typed_user['id']}`) ≠ Bloxlink `{roblox_name}` (`{bloxlink_id}`)"
        checks.append({"name": "BloxlinkMismatch", "status": CheckStatus.SKIPPED, "details": mm})
        profile.setdefault("notes", []).append(f"⚠️ **Bloxlink mismatch:** {mm}")
    elif bloxlink_id and not typed_user:
        checks.append({"name": "BloxlinkMismatch", "status": CheckStatus.PASS,
                       "details": "Bloxlink resolved; no valid typed username"})
    elif bloxlink_id and typed_user:
        checks.append({"name": "BloxlinkMismatch", "status": CheckStatus.PASS, "details": "typed matches Bloxlink"})

    if not roblox_id:
        user_bl_entries, ub_err = (await t0["ubl"]) if "ubl" in t0 else (None, "no discord_id")
        if user_bl_entries is None:
            checks.append({"name": "UserBlacklist", "status": CheckStatus.ERROR, "details": ub_err})
        elif discord_id:
            dm, _ = find_user_blacklist_match(user_bl_entries, discord_id, None)
            if dm and is_ubl_active(dm, today):
                passed = False; reason = reason or "User is blacklisted"
                checks.append({"name": "UserBlacklist", "status": CheckStatus.HIT, "details": f"discord ID — {dm['reason']}"})
            elif dm:
                checks.append({"name": "UserBlacklist", "status": CheckStatus.PASS, "details": "appealed/past end"})
            else:
                checks.append({"name": "UserBlacklist", "status": CheckStatus.PASS, "details": "not on list"})
        if "dcage" in t0:
            da = await t0["dcage"]; checks.append(da)
            if da["status"] == CheckStatus.HIT:
                passed = False; reason = reason or f"Discord < {MIN_DISCORD_AGE_DAYS}d"
        for nm in ("Keystone","XtrackerRegistry","XtrackerOwnership","SimmerRAB","ExternalDatabase","ExternalDBs"):
            checks.append({"name": nm, "status": CheckStatus.SKIPPED, "details": "no RBX identity"})
        if typed_err == "not_found":
            return {"passed": False, "reason": "Please follow the format I cannot find your Roblox username",
                    "checks": checks + [{"name": "RobloxLookup", "status": CheckStatus.ERROR,
                                         "details": f"user '{username}' not found"}],
                    "profile": {"attempted_username": username, "bloxlink_status": bloxlink_status},
                    "parse_failed": True}
        return {"passed": False, "reason": "Verification temporarily unavailable, please try again shortly",
                "checks": checks + [{"name": "RobloxLookup", "status": CheckStatus.ERROR, "details": typed_err}],
                "profile": {"attempted_username": username, "bloxlink_status": bloxlink_status},
                "parse_failed": False, "lookup_failed": True}

    profile.update(roblox_id=roblox_id, roblox_username=roblox_name,
                   roblox_display_name=roblox_display or roblox_name)

    hist_raw, hist_err = await t1[f"hist_{roblox_id}"]
    past_names = []
    if hist_raw is not None:
        past_names = [h["name"] for h in hist_raw if h.get("name")]
        if past_names:
            profile["past_usernames"] = past_names
            prev = ", ".join(past_names[:5])
            more = f" (+{len(past_names)-5})" if len(past_names) > 5 else ""
            checks.append({"name": "UsernameHistory", "status": CheckStatus.PASS,
                           "details": f"{len(past_names)} past: {prev}{more}"})
        else:
            checks.append({"name": "UsernameHistory", "status": CheckStatus.PASS, "details": "never changed"})
    else:
        checks.append({"name": "UsernameHistory", "status": CheckStatus.SKIPPED, "details": hist_err or "lookup failed"})

    hist_rbx_ids = {hid for hid, _ in db_history if hid and hid != roblox_id}
    hist_rbx_names = {hname for _, hname in db_history if hname and hname.lower() != roblox_name.lower()}

    extra_hist_names = set()
    for hid in hist_rbx_ids:
        key = f"hist_{hid}"
        if key in t1:
            try:
                extra_raw, _ = await t1[key]
                if extra_raw:
                    for h in extra_raw:
                        if h.get("name"): extra_hist_names.add(h["name"])
            except Exception:
                pass

    all_rbx_ids = {roblox_id} | hist_rbx_ids
    all_rbx_names = {roblox_name} | set(past_names) | hist_rbx_names | extra_hist_names
    if MISMATCHED_ALT_FAILS and bloxlink_id and typed_user and typed_user["id"] != bloxlink_id:
        all_rbx_ids.add(typed_user["id"])
        all_rbx_names.add(typed_user["name"])

    covered_ids = fast_ids | ({bloxlink_id} if bloxlink_id else set())
    covered_names = fast_names | blox_delta_names
    remaining_ids = all_rbx_ids - covered_ids
    remaining_names = all_rbx_names - covered_names
    if remaining_ids or remaining_names:
        _fire_t2(remaining_ids, remaining_names, "rem")

    for rid in hist_rbx_ids:
        if f"info_{rid}" in t1:
            continue
        t2[f"xtracker_reg_{rid}"] = _s(xtracker_check(session, "registry/user", rid), f"xtracker_reg_{rid}_hist")
        t2[f"simmer_rab_{rid}"] = _s(simmer_rab_check(session, rid), f"simmer_{rid}_hist")
        t2[f"snow_{rid}"] = _s(snow_core_check(session, rid, force_refresh=force_blacklist_refresh), f"snow_{rid}_hist")

    await _adv(2); await _adv(3); await _adv(4)

    async def _await_all(d):
        out = {}
        for k, task in d.items():
            try: out[k] = await task
            except Exception as e: out[k] = {"status": CheckStatus.SKIPPED, "details": type(e).__name__}
        return out

    t1_res = await _await_all(t1)
    t2_res = await _await_all(t2)
    user_bl_entries, ub_err = (await t0["ubl"]) if "ubl" in t0 else (None, "no discord_id")
    group_bl, gbl_err = await t0["gbl"]

    def _check_id(rid, name):
        key = f"{name}_{rid}"
        r = t1_res.get(key)
        if r is None: r = t2_res.get(key)
        if r is None:
            return {"status": CheckStatus.SKIPPED, "details": "no result"}
        if isinstance(r, dict):
            return r
        if isinstance(r, tuple) and len(r) >= 1 and isinstance(r[0], dict):
            return r[0]
        return {"status": CheckStatus.SKIPPED, "details": f"unexpected shape: {type(r).__name__}"}

    merged_keystone = {"status": CheckStatus.PASS, "details": ""}
    for k in list(t2_res):
        if not k.startswith("keystone_"): continue
        r = t2_res[k]
        if r["status"] == CheckStatus.HIT:
            merged_keystone = r; break
        elif r["status"] == CheckStatus.ERROR and merged_keystone["status"] == CheckStatus.PASS:
            merged_keystone = r
        elif r["status"] == CheckStatus.SKIPPED and merged_keystone["status"] == CheckStatus.PASS:
            merged_keystone = r

    merged_ext = {"matches_by_db": {}, "errors": []}
    for k in list(t2_res):
        if not k.startswith("external_dbs_"): continue
        r = t2_res[k]
        if isinstance(r, dict):
            for dbk, v in r.get("matches_by_db", {}).items():
                merged_ext["matches_by_db"].setdefault(dbk, []).extend(v)
            merged_ext["errors"].extend(r.get("errors", []))

    merged_multi = {"name": "MultiAccount", "status": CheckStatus.PASS, "details": "no patterns"}
    for k in list(t2_res):
        if not k.startswith("multi_"): continue
        r = t2_res[k]
        if r["status"] == CheckStatus.HIT:
            merged_multi = r; break
        elif r["status"] == CheckStatus.ERROR and merged_multi["status"] == CheckStatus.PASS:
            merged_multi = r

    if user_bl_entries is None:
        checks.append({"name": "UserBlacklist", "status": CheckStatus.ERROR, "details": ub_err})
    else:
        me, mt = find_user_blacklist_match(user_bl_entries, discord_id, roblox_name, past_names=past_names)
        if me and mt and "past username" in mt:
            verify, _ = await roblox_user_lookup(session, me["username"])
            if not verify or verify["id"] != roblox_id:
                me = None
        if me and is_ubl_active(me, today):
            passed = False; reason = reason or "User is blacklisted"
            checks.append({"name": "UserBlacklist", "status": CheckStatus.HIT,
                           "details": f"({mt}) — {me['reason']}, end: {me['end_date'] or 'permanent'}"})
        elif me:
            n = "appealed" if me["appealed"].lower()=="yes" else "past end date"
            checks.append({"name": "UserBlacklist", "status": CheckStatus.PASS,
                           "details": f"on list but {n} — {me['reason']}"})
        else:
            checks.append({"name": "UserBlacklist", "status": CheckStatus.PASS,
                           "details": f"not on list ({len(user_bl_entries)} entries)"})

    if "dcage" in t0:
        da = await t0["dcage"]; checks.append(da)
        if da["status"] == CheckStatus.HIT:
            passed = False; reason = reason or f"Discord < {MIN_DISCORD_AGE_DAYS}d"
    else:
        checks.append({"name": "DiscordAccountAge", "status": CheckStatus.SKIPPED, "details": "no Discord ID"})

    info, info_err = pre_info, None
    if info is None:
        info_result = t1_res.get(f"info_{roblox_id}")
        if isinstance(info_result, tuple):
            info, info_err = info_result
        else:
            info, info_err = None, "info fetch failed"

    if info and info.get("isBanned") is not None:
        if info["isBanned"]:
            passed = False; reason = reason or "Roblox account is banned/terminated"
            checks.append({"name": "RobloxBanned", "status": CheckStatus.HIT, "details": "isBanned=True"})
        else:
            checks.append({"name": "RobloxBanned", "status": CheckStatus.PASS, "details": "not banned"})
    elif info_err:
        checks.append({"name": "RobloxBanned", "status": CheckStatus.ERROR, "details": f"unverifiable — {info_err}"})

    if info and info.get("created"):
        cs = info["created"]; cd = parse_iso(cs)
        if cd:
            ad = (datetime.now(timezone.utc) - cd).days
            profile["account_created"] = cs; profile["account_age_days"] = ad
            if ad < 14:
                passed = False; reason = reason or "Roblox account is less than 2 weeks old"
                checks.append({"name": "AccountAge", "status": CheckStatus.HIT, "details": f"{ad}d (<14)"})
            else:
                checks.append({"name": "AccountAge", "status": CheckStatus.PASS, "details": f"{ad}d"})
        else:
            checks.append({"name": "AccountAge", "status": CheckStatus.SKIPPED, "details": f"unparseable: {cs}"})
    else:
        checks.append({"name": "AccountAge", "status": CheckStatus.SKIPPED, "details": info_err or "no created field"})

    for rid in all_rbx_ids:
        reg = _check_id(rid, "xtracker_reg")
        own = _check_id(rid, "xtracker_own")
        label = f"{rid}" + ("" if rid == roblox_id else " (hist)")
        if reg["status"] == CheckStatus.HIT or own["status"] == CheckStatus.HIT:
            passed = False; reason = reason or f"Xtracker: {label}"
            det = []
            if reg["status"] == CheckStatus.HIT: det.append(f"registry: {reg['details'][:150]}")
            if own["status"] == CheckStatus.HIT: det.append(f"ownership: {own['details'][:150]}")
            checks.append({"name": f"Xtracker [{label}]", "status": CheckStatus.HIT, "details": " · ".join(det)})
        elif reg["status"] == CheckStatus.SKIPPED and own["status"] == CheckStatus.SKIPPED:
            checks.append({"name": f"Xtracker [{label}]", "status": CheckStatus.SKIPPED,
                           "details": f"reg:{reg['details'][:60]} own:{own['details'][:60]}"})
        else:
            checks.append({"name": f"Xtracker [{label}]", "status": CheckStatus.PASS,
                           "details": f"reg={reg['status']} own={own['status']}"})

    for rid in all_rbx_ids:
        s = _check_id(rid, "simmer_rab")
        label = f"{rid}" + ("" if rid == roblox_id else " (hist)")
        checks.append({"name": f"SimmerRAB [{label}]", **s})
        if s["status"] == CheckStatus.HIT:
            passed = False; reason = reason or f"Simmer RAB: {label}"

    for rid in all_rbx_ids:
        s = _check_id(rid, "snow")
        label = f"{rid}" + ("" if rid == roblox_id else " (hist)")
        checks.append({"name": f"ExternalDatabase [{label}]", **s})
        if s["status"] == CheckStatus.HIT:
            passed = False; reason = reason or f"Snow Core: {label}"

    rw = (await t0["rw"]) if "rw" in t0 else {"status": CheckStatus.SKIPPED, "details": "no Discord ID"}
    ew = (await t0["ew"]) if "ew" in t0 else {"status": CheckStatus.SKIPPED, "details": "no Discord ID"}
    checks.append({"name": "RobloxWatcher", **rw})
    if rw["status"] == CheckStatus.HIT: passed = False; reason = reason or "Roblox Watcher"
    if ew["status"] == CheckStatus.HIT:
        if EXPLOIT_WATCHER_INFORMATIONAL:
            checks.append({"name": "ExploitWatcher", "status": CheckStatus.PASS,
                           "details": f"⚠️ flagged — informational · {ew['details']}"})
            profile.setdefault("notes", []).append(f"⚠️ **Exploit Watcher:** {ew['details']}")
        else:
            checks.append({"name": "ExploitWatcher", **ew})
            passed = False; reason = reason or "Exploit Watcher"
    else:
        checks.append({"name": "ExploitWatcher", **ew})

    checks.append({"name": "Keystone", **merged_keystone})
    if merged_keystone["status"] == CheckStatus.HIT:
        passed = False; reason = reason or f"Keystone: {merged_keystone['details']}"

    groups_result = t1_res.get(f"groups_{roblox_id}")
    if isinstance(groups_result, tuple):
        ug, err = groups_result
        if ug is None:
            checks.append({"name": "GroupBlacklist", "status": CheckStatus.SKIPPED, "details": f"fetch — {err}"})
        else:
            hits = [g for g in ug if g.get("group", {}).get("id") in (group_bl or [])]
            if hits:
                nm = ", ".join(g["group"].get("name", str(g["group"]["id"])) for g in hits)
                passed = False; reason = reason or f"In blacklisted group: {nm}"
                checks.append({"name": "GroupBlacklist", "status": CheckStatus.HIT, "details": f"in {nm}"})
            else:
                checks.append({"name": "GroupBlacklist", "status": CheckStatus.PASS,
                               "details": f"checked {len(group_bl or [])} groups"})
    elif group_bl is None:
        checks.append({"name": "GroupBlacklist", "status": CheckStatus.ERROR, "details": f"sheet — {gbl_err}"})
    else:
        checks.append({"name": "GroupBlacklist", "status": CheckStatus.SKIPPED, "details": "fetch failed"})

    ext_errors = merged_ext["errors"]
    if ext_errors:
        profile.setdefault("notes", []).extend(f"⚠️ External DB `{k}` failed: {e}" for k, e in ext_errors)
    today_local = datetime.now(timezone.utc).date()
    active_matches_by_db = {}
    for k, matches in merged_ext["matches_by_db"].items():
        active = []
        for m in matches:
            exp = extract_expiry_date(m["record"], m["col_labels"])
            if exp and exp < today_local: continue
            if extract_status_inactive(m["record"], m["col_labels"]): continue
            active.append(m)
        if active: active_matches_by_db[k] = active
    if active_matches_by_db:
        passed = False
        total = sum(len(v) for v in active_matches_by_db.values())
        reason = reason or f"Listed in {len(active_matches_by_db)} external database(s) ({total} active)"
        detail = []
        for k, matches in active_matches_by_db.items():
            db_name = next((c["name"] for c in EXTERNAL_DATABASES if c["key"]==k), k)
            detail.append(f"{db_name}: {len(matches)}")
        checks.append({"name": "ExternalDBs", "status": CheckStatus.HIT, "details": " · ".join(detail)})
        profile["external_matches"] = active_matches_by_db
    else:
        checks.append({"name": "ExternalDBs",
                       "status": CheckStatus.PASS if not ext_errors else CheckStatus.SKIPPED,
                       "details": (f"{len(EXTERNAL_DATABASES)} DBs searched" if not ext_errors
                                   else f"{len(ext_errors)} error(s)")})

    if "name" in merged_multi:
        checks.append({"name": merged_multi["name"],
                       "status": merged_multi["status"], "details": merged_multi["details"]})
        if merged_multi["status"] == CheckStatus.HIT:
            passed = False; reason = reason or f"Multi-account: {merged_multi['details']}"

    if discord_id:
        profile["discord_id"] = discord_id
        profile["discord_username"] = f"<@{discord_id}>"

    race_summary = []
    for rid in all_rbx_ids:
        suffix = "" if rid == roblox_id else " (hist)"
        for key, (domain, _) in list(_race_winners.items()):
            parts = key.split(":")
            if len(parts) >= 2 and parts[1] == str(rid):
                race_summary.append(f"{parts[0]}{suffix} → {domain}")
    if race_summary:
        checks.append({"name": "RaceWinners", "status": CheckStatus.PASS,
                       "details": " · ".join(race_summary[:6])})

    await _adv(5)

    bgc_id = None
    if message_id is not None:
        async with bot.db_lock:
            async with bot.db.execute("SELECT id FROM bgc_checks WHERE message_id=? AND guild_id=?",
                                       (message_id, guild_id)) as cur:
                existing = await cur.fetchone()
            if existing:
                bgc_id = existing[0]
                await bot.db.execute("""UPDATE bgc_checks SET discord_id=?, roblox_id=?, roblox_username=?,
                    passed=?, reason=?, raw_responses=?, bot_version=?, checks_version=?,
                    checked_at=CURRENT_TIMESTAMP WHERE id=?""",
                    (discord_id, profile.get("roblox_id"), profile.get("roblox_username"),
                     int(passed), reason or "PASS", json.dumps(checks),
                     BOT_VERSION, CHECKS_VERSION, bgc_id))
                await bot.db.execute("DELETE FROM check_logs WHERE bgc_id=?", (bgc_id,))
            else:
                cursor = await bot.db.execute("""INSERT INTO bgc_checks
                    (message_id, guild_id, discord_id, roblox_id, roblox_username, passed,
                     reason, raw_responses, bot_version, checks_version)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (message_id, guild_id, discord_id, profile.get("roblox_id"),
                     profile.get("roblox_username"), int(passed), reason or "PASS",
                     json.dumps(checks), BOT_VERSION, CHECKS_VERSION))
                bgc_id = cursor.lastrowid
            await bot.db.commit()
        if checks and bgc_id:
            asyncio.create_task(_persist_check_logs(bgc_id, checks))

    return {"passed": passed, "reason": reason or "PASS", "checks": checks,
            "profile": profile, "parse_failed": False, "bgc_id": bgc_id}


async def run_bgc(message, guild_id, force_blacklist_refresh=True, progress=None):
    parsed = parse_recruitment_message(message.content)
    missing = missing_format_fields(parsed)
    if missing:
        return {"passed": False, "reason": format_missing_message(missing),
                "checks": [{"name": "Format", "status": CheckStatus.ERROR,
                            "details": f"missing: {', '.join(missing)}"}],
                "profile": {}, "parse_failed": True, "format_missing": missing}
    member = message.author if isinstance(message.author, discord.Member) else None
    return await run_bgc_core(parsed["roblox_username"], message.author.id, guild_id,
                               message_id=message.id, parsed_self_report=parsed,
                               force_blacklist_refresh=force_blacklist_refresh,
                               progress=progress, member=member)


async def run_bgc_by_username(username, guild_id, force_blacklist_refresh=True, check_banned=True,
                                skip_preemptive=False):
    return await run_bgc_core(username, None, guild_id, message_id=None,
                               parsed_self_report=None, force_blacklist_refresh=force_blacklist_refresh,
                               check_banned=check_banned, member=None,
                               skip_preemptive=skip_preemptive)


async def run_bgc_by_discord_id(discord_id, guild_id, force_blacklist_refresh=True,
                                 skip_preemptive=False):
    session = bot.session
    member = None
    if guild_id:
        g = bot.get_guild(guild_id)
        if g: member = g.get_member(discord_id)
    if BLOXLINK_ENABLED and guild_id and BLOXLINK_API_KEY and not BLOXLINK_API_KEY.startswith("PASTE"):
        bl_id, _ = await bloxlink_discord_to_roblox(session, guild_id, discord_id)
        if bl_id:
            info, _ = await roblox_user_info(session, bl_id)
            if info and info.get("name"):
                return await run_bgc_core(info["name"], discord_id, guild_id, message_id=None,
                                          parsed_self_report=None,
                                          force_blacklist_refresh=force_blacklist_refresh,
                                          member=member, skip_preemptive=skip_preemptive)
    history = await get_all_roblox_history(discord_id, guild_id)
    if not history:
        return await _run_bgc_discord_only(discord_id, guild_id, force_blacklist_refresh, member=member)
    resolved = None
    for hid, _ in history:
        info, _ = await roblox_user_info(session, hid)
        if info and info.get("name"): resolved = info["name"]; break
    if not resolved:
        extra = [{"name": "RobloxLookup", "status": CheckStatus.SKIPPED, "details": "no historical account resolved"}]
        return await _run_bgc_discord_only(discord_id, guild_id, force_blacklist_refresh,
                                            extra_checks=extra, member=member)
    result = await run_bgc_core(resolved, discord_id, guild_id, message_id=None,
                                 parsed_self_report=None, force_blacklist_refresh=force_blacklist_refresh,
                                 member=member, skip_preemptive=skip_preemptive)
    result["profile"]["discord_only"] = False
    if len(history) > 1: result["profile"]["historical_identities"] = history
    return result


async def _run_bgc_discord_only(discord_id, guild_id, force_blacklist_refresh=True,
                                 extra_checks=None, member=None):
    checks, profile, reason, passed = [], {}, None, True
    session = bot.session; today = datetime.now(timezone.utc).date()
    profile["discord_id"] = discord_id
    profile["discord_username"] = f"<@{discord_id}>"
    profile["discord_only"] = True

    ubl, ub_err = await get_user_blacklist(session, force_refresh=force_blacklist_refresh)
    if ubl is None:
        checks.append({"name": "UserBlacklist", "status": CheckStatus.ERROR, "details": ub_err})
    else:
        me, _ = find_user_blacklist_match(ubl, discord_id, None)
        if me and is_ubl_active(me, today):
            passed = False; reason = reason or "User is blacklisted"
            checks.append({"name": "UserBlacklist", "status": CheckStatus.HIT, "details": me['reason']})
        elif me:
            checks.append({"name": "UserBlacklist", "status": CheckStatus.PASS, "details": "appealed/past end"})
        else:
            checks.append({"name": "UserBlacklist", "status": CheckStatus.PASS, "details": "not on list"})

    da = await check_discord_age(discord_id); checks.append(da)
    if da["status"] == CheckStatus.HIT:
        passed = False; reason = reason or f"Discord < {MIN_DISCORD_AGE_DAYS}d"

    rw = await watcher_check(session, discord_id, RW_API_KEY, "robloxwatcher")
    checks.append({"name": "RobloxWatcher", **rw})
    if rw["status"] == CheckStatus.HIT: passed = False; reason = reason or "Roblox Watcher"

    ew = await watcher_check(session, discord_id, EW_API_KEY, "exploitwatcher")
    if ew["status"] == CheckStatus.HIT:
        if EXPLOIT_WATCHER_INFORMATIONAL:
            checks.append({"name": "ExploitWatcher", "status": CheckStatus.PASS,
                           "details": f"⚠️ flagged — informational · {ew['details']}"})
            profile.setdefault("notes", []).append(f"⚠️ **Exploit Watcher:** {ew['details']}")
        else:
            checks.append({"name": "ExploitWatcher", **ew})
            passed = False; reason = reason or "Exploit Watcher"
    else:
        checks.append({"name": "ExploitWatcher", **ew})

    dc_names = set()
    if member:
        if getattr(member, "name", None): dc_names.add(member.name)
        if getattr(member, "display_name", None): dc_names.add(member.display_name)
    ext = await search_external_dbs(session, {
        "rbx_ids": set(), "rbx_usernames": set(),
        "discord_ids": {discord_id}, "discord_usernames": dc_names,
    }, force_refresh=force_blacklist_refresh)
    if ext["matches_by_db"]:
        passed = False
        reason = reason or f"Listed in {len(ext['matches_by_db'])} external database(s)"
        profile["external_matches"] = ext["matches_by_db"]
        checks.append({"name": "ExternalDBs", "status": CheckStatus.HIT,
                       "details": f"{sum(len(v) for v in ext['matches_by_db'].values())} match(es)"})
    else:
        checks.append({"name": "ExternalDBs",
                       "status": CheckStatus.PASS if not ext["errors"] else CheckStatus.SKIPPED,
                       "details": f"{len(EXTERNAL_DATABASES)} DBs searched"})
    if ext["errors"]:
        profile.setdefault("notes", []).extend(f"⚠️ External DB `{k}` failed: {e}" for k, e in ext["errors"])

    for nm in ("Keystone","XtrackerRegistry","XtrackerOwnership","SimmerRAB","ExternalDatabase","MultiAccount"):
        checks.append({"name": nm, "status": CheckStatus.SKIPPED, "details": "no Roblox ID"})

    if extra_checks: checks.extend(extra_checks)
    return {"passed": passed, "reason": reason or "PASS", "checks": checks,
            "profile": profile, "parse_failed": False, "discord_only": True}


# ==================== EMBEDS ====================
def build_result_embed(result, title_prefix="BGC Result", runner=None):
    p = result["profile"]; passed = result["passed"]
    color = T.SUCCESS if passed else T.DANGER
    icon = T.EMOJI["ok"] if passed else T.EMOJI["fail"]
    embed = discord.Embed(title=branded(f"{icon} {title_prefix}"),
                          description=f"**{'PASSED' if passed else 'FAILED'}**"
                                      + (f"\n> {result['reason']}" if not passed else ""),
                          color=color, timestamp=datetime.now(timezone.utc))
    if runner: embed.set_author(name=f"Requested by {runner.display_name}", icon_url=runner.display_avatar.url)
    if p.get("roblox_id"): embed.set_thumbnail(url=T.roblox_avatar(p["roblox_id"]))
    if p.get("discord_id"):
        embed.add_field(name=f"{T.EMOJI['discord']} Discord",
                        value=f"<@{p['discord_id']}>\n`{p['discord_id']}`", inline=True)
    if p.get("roblox_username"):
        embed.add_field(name=f"{T.EMOJI['roblox']} Roblox",
                        value=f"[{p['roblox_username']}]({T.roblox_profile(p['roblox_id'])})\n`{p['roblox_id']}`",
                        inline=True)
    if p.get("account_age_days") is not None:
        embed.add_field(name=f"{T.EMOJI['calendar']} Account Age", value=f"{p['account_age_days']} days", inline=True)
    elif p.get("attempted_username"):
        embed.add_field(name="🎮 Attempted", value=f"`{p['attempted_username']}` (not found)", inline=True)
    elif p.get("discord_only"):
        embed.add_field(name="Scope", value="Discord-ID only", inline=True)

    via = p.get("resolved_via"); bl_st = p.get("bloxlink_status")
    if via == "bloxlink_preemptive":
        embed.add_field(name="🔗 Identity", value="**Bloxlink** (preemptive cache)", inline=True)
    elif via == "bloxlink":
        embed.add_field(name="🔗 Identity", value="**Bloxlink**", inline=True)
    elif via == "username":
        embed.add_field(name="🔗 Identity", value=f"Typed username (Bloxlink: `{bl_st or 'n/a'}`)", inline=True)
    if p.get("resolved_via_nickname"):
        embed.add_field(name="🏷️ Nickname fallback", value=f"`{p['resolved_via_nickname']}`", inline=True)
    if p.get("preemptive_hit"):
        embed.add_field(name="🏎️ Preemptive", value="Cached identity + xtracker", inline=True)
    if p.get("bloxlink_late_cache"):
        embed.add_field(name="⏱️ Bloxlink late cache", value="From previous timeout", inline=True)

    hits = [c for c in result["checks"] if c["status"] == CheckStatus.HIT]
    errors = [c for c in result["checks"] if c["status"] == CheckStatus.ERROR]
    skips = [c for c in result["checks"] if c["status"] == CheckStatus.SKIPPED]
    passes = [c for c in result["checks"] if c["status"] == CheckStatus.PASS]

    if hits:
        lines = [f"🔴 **{c['name']}** · {c.get('details','')[:160]}" for c in hits[:8]]
        if len(hits) > 8: lines.append(f"*+{len(hits)-8} more*")
        embed.add_field(name=f"Failed ({len(hits)})", value="\n".join(lines)[:1024], inline=False)
    if errors:
        lines = [f"🟠 **{c['name']}** · {c.get('details','')[:160]}" for c in errors[:4]]
        embed.add_field(name=f"Errors ({len(errors)})", value="\n".join(lines)[:1024], inline=False)
    summary = []
    if passes: summary.append(f"🟢 {len(passes)} passed")
    if skips: summary.append(f"🟡 {len(skips)} skipped")
    if summary: embed.add_field(name="Summary", value=" · ".join(summary), inline=False)
    if p.get("past_usernames"):
        names = p["past_usernames"]
        prev = ", ".join(f"`{n}`" for n in names[:6])
        if len(names) > 6: prev += f" *+{len(names)-6}*"
        embed.add_field(name=f"Past names ({len(names)})", value=prev[:1024], inline=False)

    race_check = next((c for c in result["checks"] if c["name"] == "RaceWinners"), None)
    if race_check:
        embed.add_field(name="🏁 Race Winners", value=race_check["details"][:1024], inline=False)

    ext = p.get("external_matches") or {}
    for db_key, matches in ext.items():
        cfg = next((c for c in EXTERNAL_DATABASES if c["key"]==db_key), None)
        if not cfg: continue
        link = f"https://docs.google.com/spreadsheets/d/{cfg['sheet_id']}/edit#gid={cfg['gid']}"
        lines = []
        for m in matches[:3]:
            rec = m["record"]; cols = m["col_labels"]
            reason_idx = date_idx = None
            for ci, lbl in enumerate(cols):
                ll = lbl.lower()
                if any(k in ll for k in ("reason","offense","criteria","punish")) and reason_idx is None: reason_idx = ci
                elif "date" in ll and date_idx is None: date_idx = ci
            parts = []
            if reason_idx is not None and reason_idx in rec["cells"]:
                rv = rec["cells"][reason_idx].get("f") or rec["cells"][reason_idx].get("v")
                if rv: parts.append(f"*{str(rv)[:60]}*")
            if date_idx is not None and date_idx in rec["cells"]:
                dv = rec["cells"][date_idx].get("f") or rec["cells"][date_idx].get("v")
                if dv: parts.append(f"({str(dv)[:20]})")
            matched = m["matches"][0]
            lines.append(f"**{matched['token']}** ({matched['match_type']})\n> {' '.join(parts) if parts else '—'}")
        if len(matches) > 3: lines.append(f"*+{len(matches)-3} more*")
        embed.add_field(name=f"📋 {cfg['name']} ({len(matches)}) · [open]({link})",
                        value="\n".join(lines)[:1024], inline=False)

    notes = p.get("notes") or []
    if notes: embed.add_field(name=f"📝 Notes ({len(notes)})", value="\n".join(notes)[:1024], inline=False)
    embed.set_footer(text=f"v{BOT_VERSION} · checks v{CHECKS_VERSION} · BGC #{result.get('bgc_id') or '—'} · made by {BOT_AUTHOR}")
    return embed


def build_log_embed(result, message=None, runner=None, autorole_result=None, dm_result=None):
    embed = build_result_embed(result, runner=runner)
    if message is not None:
        embed.add_field(name="Applicant", value=f"{message.author.mention} · [Jump]({message.jump_url})", inline=False)
    if autorole_result is not None:
        embed.add_field(name="🎭 Autorole",
                        value=(f"✅ {autorole_result.get('reason')}" if autorole_result.get("applied")
                               else f"⚠️ {autorole_result.get('reason')}"), inline=False)
    if dm_result is not None:
        embed.add_field(name="📬 Acceptance DM",
                        value=("✅ Delivered" if dm_result.get("sent") else f"⚠️ {dm_result.get('reason')}"), inline=False)
    return embed


async def send_logs(result, gid, message=None, runner=None, autorole_result=None, dm_result=None):
    pid, fid, _ = await get_log_channels(gid)
    target = pid if result["passed"] else fid
    if target:
        ch = bot.get_channel(target)
        if ch:
            try: await ch.send(embed=build_log_embed(result, message, runner, autorole_result, dm_result))
            except: logger.warning(f"send_logs failed for {gid}", exc_info=True)


async def log_bgc_to_bot_logs(gid, message, result, duration_ms, autorole_result=None, dm_result=None):
    passed = result["passed"]
    embed = discord.Embed(title=branded("✅ BGC Passed" if passed else "❌ BGC Failed"),
                          description=f"{T.EMOJI['fail'] if not passed else T.EMOJI['ok']} **{result['reason']}**\n"
                                      f"{T.EMOJI['clock']} `{duration_ms}ms`",
                          color=T.SUCCESS if passed else T.DANGER, timestamp=datetime.now(timezone.utc))
    if message:
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="Source", value=f"[Jump]({message.jump_url})", inline=True)
    p = result.get("profile") or {}
    if p.get("roblox_id"):
        embed.set_thumbnail(url=T.roblox_avatar(p["roblox_id"]))
        embed.add_field(name=f"{T.EMOJI['roblox']} Roblox",
                        value=f"[{p['roblox_username']}]({T.roblox_profile(p['roblox_id'])})", inline=True)
    if autorole_result is not None:
        embed.add_field(name="🎭 Autorole",
                        value=(f"✅ {autorole_result.get('reason')}" if autorole_result.get("applied")
                               else f"⚠️ {autorole_result.get('reason')}"), inline=True)
    if dm_result is not None:
        embed.add_field(name="📬 DM",
                        value=("✅ Delivered" if dm_result.get("sent") else f"⚠️ {dm_result.get('reason')}"), inline=True)
    notable = [c for c in result.get("checks", []) if c["status"] != CheckStatus.PASS]
    if notable:
        embed.add_field(name=f"Non-pass ({len(notable)})",
                        value="\n".join(f"{T.EMOJI.get(c['status'],'⚪')} **{c['name']}** — {c.get('details','')[:180]}"
                                        for c in notable)[:1024], inline=False)
    notes = p.get("notes") or []
    if notes: embed.add_field(name=f"📝 Notes ({len(notes)})", value="\n".join(notes)[:1024], inline=False)
    await bot_log(gid, embed=embed)


# ==================== AUTOROLE + DM ====================
async def _apply_autorole(guild, member, result):
    if not AUTO_ROLE_ID: return {"applied": False, "reason": "AUTO_ROLE_ID not set"}
    if not result or not result.get("passed"): return {"applied": False, "reason": "BGC failed"}
    if not isinstance(member, discord.Member): return {"applied": False, "reason": "not a member"}
    if guild is None: return {"applied": False, "reason": "no guild"}
    role = guild.get_role(AUTO_ROLE_ID)
    if role is None: return {"applied": False, "reason": f"role {AUTO_ROLE_ID} missing"}
    if role in member.roles: return {"applied": False, "reason": "already has role"}
    me = guild.me
    if me is None: return {"applied": False, "reason": "bot member not cached"}
    if not me.guild_permissions.manage_roles: return {"applied": False, "reason": "no Manage Roles"}
    if role.position >= me.top_role.position: return {"applied": False, "reason": "role above bot"}
    try:
        await member.add_roles(role, reason=f"BGC #{result.get('bgc_id') or '?'} passed")
        return {"applied": True, "reason": f"assigned {role.mention}"}
    except discord.Forbidden: return {"applied": False, "reason": "Forbidden"}
    except Exception as e: return {"applied": False, "reason": type(e).__name__}


async def _send_acceptance_dm(user, guild):
    if not ACCEPTANCE_DM_ENABLED: return {"sent": False, "reason": "disabled"}
    if not isinstance(user, (discord.User, discord.Member)): return {"sent": False, "reason": "invalid user"}
    try:
        await user.send(ACCEPTANCE_DM_TEMPLATE)
        return {"sent": True, "reason": "sent"}
    except discord.Forbidden: return {"sent": False, "reason": "DMs closed / blocked"}
    except discord.HTTPException as e: return {"sent": False, "reason": f"HTTP {e.status}"}
    except Exception as e: return {"sent": False, "reason": type(e).__name__}


async def _post_pass_actions(message, result, from_edit, silent, runner, duration_ms):
    autorole_result = None; dm_result = None
    if message.guild is not None:
        autorole_result = await _apply_autorole(message.guild, message.author, result)
        if autorole_result.get("applied"):
            if from_edit: dm_result = {"sent": False, "reason": "edit re-run"}
            elif silent: dm_result = {"sent": False, "reason": "silent/backfill"}
            else: dm_result = await _send_acceptance_dm(message.author, message.guild)
        else:
            dm_result = {"sent": False, "reason": f"autorole: {autorole_result.get('reason')}"}
    gid = message.guild.id if message.guild else 0
    await send_logs(result, gid, message, runner, autorole_result, dm_result)
    await log_bgc_to_bot_logs(gid, message, result, duration_ms, autorole_result, dm_result)


async def _safe_post_pass(message, result, from_edit, silent, runner, duration_ms):
    try:
        await _post_pass_actions(message, result, from_edit, silent, runner, duration_ms)
    except Exception:
        logger.warning("Post-pass actions failed", exc_info=True)


# ==================== PROCESS ====================
async def _delayed_reaction(msg, emoji, delay):
    try:
        await asyncio.sleep(delay)
        await msg.add_reaction(emoji)
    except (asyncio.CancelledError, discord.HTTPException):
        pass


async def process_message(message, gid, dry_run=False, from_edit=False,
                          force_blacklist_refresh=True, silent=False, show_progress=True, runner=None,
                          skip_preemptive=False):
    if is_format_template(message.content):
        return {"passed": None, "reason": "template", "checks": [], "profile": {}, "skipped_template": True}
    if not dry_run and not from_edit and await is_already_checked(message.id):
        return {"passed": None, "reason": "already checked", "checks": [], "profile": {}, "skipped_dup": True}
    parsed = parse_recruitment_message(message.content)
    missing = missing_format_fields(parsed)
    if missing:
        reason = format_missing_message(missing)
        result = {"passed": False, "reason": reason,
                  "checks": [{"name": "Format", "status": CheckStatus.ERROR,
                              "details": f"missing: {', '.join(missing)}"}],
                  "profile": {}, "parse_failed": True, "format_missing": missing}
        if not dry_run:
            try: await message.add_reaction("❌")
            except: pass
            if not silent:
                try:
                    await message.reply(f"{sanitize_public_reason(result)}\n-# Run `/about` to see what we check.",
                                        mention_author=False)
                except: pass
            asyncio.create_task(send_logs(result, gid, message, runner))
            asyncio.create_task(log_bgc_to_bot_logs(gid, message, result, 0))
        return result

    reaction_task = None
    if not dry_run:
        reaction_task = asyncio.create_task(_delayed_reaction(message, "⏰", DLY_REACTION_SEC))

    reporter = None
    async with bot.bgc_semaphore:
        if (not dry_run and show_progress and not _caches_hot()
                and bot._active_progress_per_channel[message.channel.id] < MAX_PROGRESS_PER_CHANNEL):
            reporter = ProgressReporter(message.channel, message.author)
            await reporter.start()
            bot._active_progress_per_channel[message.channel.id] += 1
        start = time.time(); duration_ms = 0
        try:
            if skip_preemptive:
                result = await run_bgc_core(parsed["roblox_username"], message.author.id, gid,
                                             message_id=message.id, parsed_self_report=parsed,
                                             force_blacklist_refresh=force_blacklist_refresh,
                                             progress=reporter.advance if reporter else None,
                                             member=message.author if isinstance(message.author, discord.Member) else None,
                                             skip_preemptive=True)
            else:
                result = await run_bgc(message, gid, force_blacklist_refresh,
                                        progress=reporter.advance if reporter else None)
        except Exception as e:
            tb = traceback.format_exc(); logger.error(f"BGC error: {e}\n{tb}")
            result = {"passed": False, "reason": "Verification temporarily unavailable, please try again shortly",
                      "checks": [], "profile": {}, "internal_error": True}
            if not dry_run:
                await bot_log(gid, "🔴 Internal Error", f"```{tb[:1800]}```", T.DANGER)
        finally:
            duration_ms = int((time.time() - start) * 1000)
            if reporter:
                try: await reporter.finish()
                except: pass
                bot._active_progress_per_channel[message.channel.id] -= 1

    if result.get("parse_failed"):
        bot.consecutive_parse_failures += 1
        if bot.consecutive_parse_failures >= PARSE_FAILURE_THRESHOLD and not bot.parse_failure_notified:
            bot.parse_failure_notified = True
            if OWNER_ID:
                try:
                    owner = bot.get_user(OWNER_ID) or await bot.fetch_user(OWNER_ID)
                    if owner: await owner.send(branded(f"⚠️ {bot.consecutive_parse_failures} consecutive parse failures."))
                except: pass
    else:
        bot.consecutive_parse_failures = 0; bot.parse_failure_notified = False

    if dry_run: return result

    if reaction_task is not None:
        if not reaction_task.done():
            reaction_task.cancel()
            try: await reaction_task
            except: pass
    asyncio.create_task(message.remove_reaction("⏰", bot.user))
    asyncio.create_task(message.add_reaction("✅" if result["passed"] else "❌"))

    if not result["passed"] and not silent:
        try:
            await message.reply(f"{sanitize_public_reason(result)}\n-# Run `/about` to see what we check.",
                                mention_author=False)
        except: pass

    if result.get("passed"):
        asyncio.create_task(_safe_post_pass(message, result, from_edit, silent, runner, duration_ms))
    else:
        asyncio.create_task(send_logs(result, gid, message, runner))
        asyncio.create_task(log_bgc_to_bot_logs(gid, message, result, duration_ms))

    return result


# ==================== EVENTS ====================
@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} ({bot.user.id})")
    if bot._online_logged: return
    bot._online_logged = True
    rows = await db_fetchall("SELECT guild_id FROM guild_settings WHERE bot_log_channel IS NOT NULL")
    autorole_text = f"<@&{AUTO_ROLE_ID}>" if AUTO_ROLE_ID else "not configured"
    brand_header = f"**{BRAND_NAME}**\n" if BRAND_NAME else ""
    for (gid,) in rows:
        embed = discord.Embed(title=branded("🟢 Bot Online"),
                              description=f"{brand_header}{bot.user.mention}\nLatency: `{round(bot.latency*1000)}ms`\nGuilds: `{len(bot.guilds)}`\nVersion: `{BOT_VERSION}`\nAutorole: {autorole_text}",
                              color=T.SUCCESS, timestamp=datetime.now(timezone.utc))
        embed.set_footer(text=f"made by {BOT_AUTHOR}")
        await bot_log(gid, embed=embed)


@bot.event
async def on_message(message):
    if message.author.bot or message.guild is None: return
    if message.content.startswith(("/", "!", ".")): return
    if is_privileged_member(message.author): return
    rc = await get_recruitment_channel(message.guild.id)
    if not rc or message.channel.id != rc: return
    if is_format_template(message.content): return
    asyncio.create_task(process_message(message, message.guild.id, force_blacklist_refresh=False))


@bot.event
async def on_raw_message_edit(payload):
    if not payload.guild_id or "content" not in payload.data: return
    rc = await get_recruitment_channel(payload.guild_id)
    if not rc or payload.channel_id != rc: return
    mid = payload.message_id
    existing = _pending_edits.get(mid)
    if existing and not existing.done(): existing.cancel()
    async def _run():
        try:
            try: await asyncio.sleep(EDIT_DEBOUNCE_SEC)
            except asyncio.CancelledError: return
            try:
                ch = bot.get_channel(payload.channel_id) or await bot.fetch_channel(payload.channel_id)
                m = await ch.fetch_message(mid)
            except: return
            if m.author.bot or is_format_template(m.content): return
            if is_privileged_member(m.author): return
            await process_message(m, payload.guild_id, from_edit=True,
                                   force_blacklist_refresh=False, show_progress=False)
        finally:
            if _pending_edits.get(mid) is asyncio.current_task():
                _pending_edits.pop(mid, None)
    _pending_edits[mid] = asyncio.create_task(_run())


@tree.error
async def on_app_command_error(interaction, error):
    logger.error(f"App command error: {error}", exc_info=error)
    embed = discord.Embed(title=branded("Something went wrong"),
                          description=f"```{(str(error) or type(error).__name__)[:1500]}```",
                          color=T.DANGER, timestamp=datetime.now(timezone.utc))
    embed.set_footer(text="Already reported to the bot owner.")
    try:
        if interaction.response.is_done(): await interaction.followup.send(embed=embed, ephemeral=True)
        else: await interaction.response.send_message(embed=embed, ephemeral=True)
    except: pass
    if OWNER_ID:
        try:
            owner = bot.get_user(OWNER_ID) or await bot.fetch_user(OWNER_ID)
            if owner:
                await owner.send(embed=discord.Embed(title=branded("🔴 Command error"),
                                                     description=f"`{getattr(interaction.command, 'qualified_name', 'unknown')}`\n```{traceback.format_exc()[-1800:]}```",
                                                     color=T.DANGER, timestamp=datetime.now(timezone.utc)))
        except: pass


def authorized(interaction):
    if OWNER_ID and interaction.user.id == OWNER_ID: return True
    if interaction.guild and interaction.user.guild_permissions.administrator: return True
    return False


async def _ac_lookup(u):
    try:
        async with bot.session.post("https://users.roblox.com/v1/usernames/users",
                                     json={"usernames": [u], "excludeBannedUsers": False}) as r:
            if r.status == 200:
                data = await r.json()
                return [app_commands.Choice(name=x["name"], value=x["name"]) for x in data.get("data", [])][:25]
    except: pass
    return []


async def roblox_name_ac(interaction, current):
    current = (current or "").strip().lstrip("@")
    if not current:
        try:
            rows = await db_fetchall("SELECT DISTINCT roblox_username FROM bgc_checks WHERE guild_id=? AND roblox_username IS NOT NULL ORDER BY id DESC LIMIT 25",
                                      (interaction.guild_id or 0,))
            return [app_commands.Choice(name=r[0], value=r[0]) for r in rows if r[0]]
        except: return []
    try: return await asyncio.wait_for(_ac_lookup(current), timeout=AUTOCOMPLETE_TIMEOUT)
    except: return []


async def debug_latest_ac(interaction, current):
    current = (current or "").strip()
    try:
        if current:
            rows = await db_fetchall("SELECT DISTINCT discord_id, roblox_username FROM bgc_checks WHERE guild_id=? AND (CAST(discord_id AS TEXT) LIKE ? OR roblox_username LIKE ?) ORDER BY id DESC LIMIT 25",
                                      (interaction.guild_id or 0, f"%{current}%", f"%{current}%"))
        else:
            rows = await db_fetchall("SELECT DISTINCT discord_id, roblox_username FROM bgc_checks WHERE guild_id=? ORDER BY id DESC LIMIT 25",
                                      (interaction.guild_id or 0,))
    except: return []
    out = []
    for did, rn in rows:
        if did: out.append(app_commands.Choice(name=f"Discord · {did}", value=str(did)))
        if rn: out.append(app_commands.Choice(name=f"Roblox · {rn}", value=rn))
    return out[:25]


# ==================== TIMELINE FORMATTER ====================
def _format_timeline(timings, t_start, total, result, header_lines):
    def _start_ms(t): return (t["start"] - t_start) * 1000.0
    def _end_ms(t):   return (t["end"]   - t_start) * 1000.0
    def _dur_ms(t):   return (t["end"]   - t["start"]) * 1000.0

    def _tier(name):
        if name in ("user_blacklist","discord_age","roblox_watcher","exploit_watcher",
                    "group_blacklist","bloxlink","typed_lookup","nickname_lookup"):
            return 0
        if (name.startswith("keystone") or name.startswith("external_dbs")
                or name.startswith("multi_") or name.endswith("_hist")):
            return 2
        return 1

    t0_tasks = [t for t in timings if _tier(t["name"]) == 0]
    t1_tasks = [t for t in timings if _tier(t["name"]) == 1]
    t2_tasks = [t for t in timings if _tier(t["name"]) == 2]

    t1_start_times = [_start_ms(t) for t in t1_tasks]
    t1_fire = min(t1_start_times) if t1_start_times else 0.0

    info_task = next((t for t in timings if t["name"].startswith("user_info")), None)
    hist_task = next((t for t in timings if t["name"].startswith("username_history")), None)
    info_done = _end_ms(info_task) if info_task else 0.0
    hist_done = _end_ms(hist_task) if hist_task else 0.0

    t0_gate = max(t0_tasks, key=_end_ms, default=None)
    longest = max(timings, key=_dur_ms, default=None) if timings else None
    xtracker_tasks = [t for t in timings if t["name"].startswith("xtracker")]
    xtracker_serial = sum(_dur_ms(t) for t in xtracker_tasks)

    waves = {"fast": [], "blox": [], "rem": [], "other": []}
    for t in t2_tasks:
        matched = False
        for w in ("fast", "blox", "rem"):
            if t["name"].endswith(f"_{w}") or t["name"].endswith(f"_{w}_hist"):
                waves[w].append(t); matched = True; break
        if not matched: waves["other"].append(t)

    lines = list(header_lines)
    lines.append(f"Result:   {'PASS' if result['passed'] else 'FAIL'} — {result['reason']}")
    lines.append(f"Total:    {total:.0f}ms")
    lines.append("")
    lines.append("─ Task Timeline (chronological) ─")
    lines.append("```")
    lines.append(f"{'START':>10} {'END':>10} {'DUR':>10}  NAME")
    for t in sorted(timings, key=lambda x: x["start"]):
        lines.append(f"{_start_ms(t):>8.1f}ms {_end_ms(t):>8.1f}ms {_dur_ms(t):>8.1f}ms  {t['name']}")
    lines.append("```")
    lines.append("")
    lines.append("─ Gates / Bottlenecks ─")
    lines.append(f"• T0 → T1 fire:     T={t1_fire:.0f}ms (first ID known)")
    if t0_gate:
        lines.append(f"  - T0 slowest:     {t0_gate['name']} finished T={_end_ms(t0_gate):.0f}ms ({_dur_ms(t0_gate):.0f}ms)")
    if info_task:
        lines.append(f"• Identity finalized (info):  T={info_done:.0f}ms ({_dur_ms(info_task):.0f}ms)")
    if hist_task:
        lines.append(f"• T1 → T2 fire (hist done):   T={hist_done:.0f}ms ({_dur_ms(hist_task):.0f}ms)")
    if longest:
        lines.append(f"• Longest task:     {longest['name']} — {_dur_ms(longest):.0f}ms")
    if xtracker_tasks:
        lines.append(f"• Xtracker total:   {len(xtracker_tasks)} call(s) × {bot.xtracker_limiter.interval:.2f}s limiter = {xtracker_serial:.0f}ms")
    lines.append("")
    lines.append("─ T2 Waves ─")
    for w in ("fast", "blox", "rem", "other"):
        ts = waves[w]
        if not ts: continue
        w_start = min(_start_ms(t) for t in ts)
        w_end = max(_end_ms(t) for t in ts)
        lines.append(f"  {w:>5}:  T={w_start:.0f}ms → T={w_end:.0f}ms  ({len(ts)} task(s), span {w_end-w_start:.0f}ms)")
        for t in sorted(ts, key=lambda x: x["start"]):
            lines.append(f"           {t['name']:<32}  {_dur_ms(t):>6.0f}ms")
    lines.append("")
    return "\n".join(lines)


# ==================== /about ====================
@tree.command(name="about", description="Simple guide: what the bot checks and why you might have failed")
async def about_cmd(interaction):
    await interaction.response.defer(ephemeral=True)
    pages = []

    p1 = discord.Embed(title=branded("🔎 What We Check"), color=T.BRAND,
                       description=("When you post your application, the bot searches **all of these at the same time.**\n"
                                    "-# You don't have to do anything — it runs automatically in a few seconds.\n"
                                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"),
                       timestamp=datetime.now(timezone.utc))
    p1.add_field(name="🔗  **Bloxlink**", value="Links your Roblox account to Discord\n-# The bot **trusts Bloxlink** over your typed username", inline=False)
    p1.add_field(name="🎮  **Your Roblox Account**", value="Username · age · groups you're in · past usernames", inline=False)
    p1.add_field(name="💬  **Your Discord Account**", value="How old your Discord account is", inline=False)
    p1.add_field(name="📋  **Our Blacklist**", value="Our own list of banned users and banned Roblox groups", inline=False)
    p1.add_field(name="🛡️  **Cheater Databases**", value="**Xtracker** and **Keystone** — shared lists used by many clans", inline=False)
    n_ext = len(EXTERNAL_DATABASES)
    if n_ext:
        p1.add_field(name=f"🗄️  **{n_ext} External Blacklists**", value=f"Ban lists from **{n_ext} other source{'s' if n_ext != 1 else ''}** we check for your name", inline=False)
    p1.add_field(name="👁️  **Roblox Watcher**", value="Checks if you've ever been in an **NSFW** or **condo** Discord server", inline=False)
    p1.add_field(name="🕵️  **Simmer**", value="Checks for suspicious **Roblox Studio** activity", inline=False)
    p1.add_field(name="❄️  **Snow Core**", value="Another community's punishment list", inline=False)
    p1.add_field(name="✍️  **Your Answers**", value="What you wrote on the application form", inline=False)
    p1.add_field(name="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                 value=("> ✅ **If everything passes** → you get auto-roled + a DM with next steps\n"
                        "> ❌ **If anything fails** → no role, no DM, generic reply in chat"), inline=False)
    p1.set_footer(text="Page 1 of 2 · click ▶ for why you might have failed")
    pages.append(p1)

    p2 = discord.Embed(title=branded("❌ Why You Might Have Failed"), color=T.DANGER,
                       description=("If the bot reacted with ❌ — **it was one of these reasons.**\n"
                                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬"),
                       timestamp=datetime.now(timezone.utc))
    p2.add_field(name="❌  **You said \"no\"**", value="You answered **no** to *willing to join this clan*", inline=False)
    p2.add_field(name="❌  **Roblox account too new**", value="Must be at least **2 weeks old**", inline=False)
    p2.add_field(name="❌  **Discord account too new**", value="Must be at least **7 days old**", inline=False)
    p2.add_field(name="❌  **In a banned Roblox group**", value="You're in a group that's on our blacklist", inline=False)
    p2.add_field(name="❌  **On our blacklist**", value="You're on our own ban list **and haven't appealed it**", inline=False)
    if n_ext:
        p2.add_field(name="❌  **Another clan banned you**", value=f"You're on **one of the {n_ext} external lists** we check", inline=False)
    p2.add_field(name="❌  **Known cheater**", value="You're in **Xtracker** or **Keystone**", inline=False)
    p2.add_field(name="❌  **Seen in bad servers**", value="You were in an **NSFW** or **condo** Discord server", inline=False)
    p2.add_field(name="❌  **Username doesn't exist**", value="The Roblox username you typed is **not a real account** (typo?)", inline=False)
    p2.add_field(name="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", value="-# ✅ These do **NOT** fail you:", inline=False)
    p2.add_field(name="✅  **Exploit Watcher flags**", value="-# Noted in logs only — doesn't block you", inline=False)
    p2.add_field(name="✅  **Appealed / expired bans**", value="-# If your ban was appealed or expired, you pass", inline=False)
    p2.add_field(name="✅  **Archived Keystone cases**", value="-# Old resolved cases don't count", inline=False)
    p2.add_field(name="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                 value=("**What to do now**\n"
                        "> 📌 Ask staff in the support channel for the **exact** reason\n"
                        "> 🔄 Fix the issue then **post a new message** to be re-checked\n"
                        "> ⚠️ **Don't edit your old message** — the bot won't re-check it"), inline=False)
    p2.set_footer(text="Page 2 of 2 · click ◀ to go back")
    pages.append(p2)

    pager = Paginator(pages, interaction.user.id)
    pager._message = await interaction.followup.send(embed=pages[0], view=pager, ephemeral=True)


# ==================== /setup ====================
def _private_ow(g):
    ow = {g.default_role: discord.PermissionOverwrite(view_channel=False),
          g.me: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                             read_message_history=True, add_reactions=True)}
    if OWNER_ID:
        om = g.get_member(OWNER_ID)
        if om: ow[om] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
    return ow


@tree.command(name="setup", description="Create or reconfigure the BGC log channels for this server")
@app_commands.describe(pass_log="Pass log channel", fail_log="Fail log channel",
                       bot_log_channel="Bot logs channel", recruitment_channel="Recruitment channel")
async def setup_cmd(interaction, pass_log: Optional[discord.TextChannel]=None,
                    fail_log: Optional[discord.TextChannel]=None,
                    bot_log_channel: Optional[discord.TextChannel]=None,
                    recruitment_channel: Optional[discord.TextChannel]=None):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message(branded("Guild only."), ephemeral=True); return
    if any([pass_log, fail_log, bot_log_channel, recruitment_channel]):
        p, f, b = await get_log_channels(guild.id)
        if pass_log: p = pass_log.id
        if fail_log: f = fail_log.id
        if bot_log_channel: b = bot_log_channel.id
        await set_log_channels(guild.id, p, f, b)
        if recruitment_channel: await set_recruitment_channel(guild.id, recruitment_channel.id)
        parts = []
        if pass_log: parts.append(f"pass → {pass_log.mention}")
        if fail_log: parts.append(f"fail → {fail_log.mention}")
        if bot_log_channel: parts.append(f"bot → {bot_log_channel.mention}")
        if recruitment_channel: parts.append(f"recruitment → {recruitment_channel.mention}")
        await interaction.response.send_message(branded("Updated:\n" + "\n".join(parts)), ephemeral=True); return
    p, f, b = await get_log_channels(guild.id)
    if not all([p, f, b]):
        if not guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(branded("Need Manage Channels."), ephemeral=True); return
        await interaction.response.defer(ephemeral=True)
        ow = _private_ow(guild)
        try:
            p_ch = await guild.create_text_channel("bgc-pass", overwrites=ow)
            f_ch = await guild.create_text_channel("bgc-fail", overwrites=ow)
            b_ch = await guild.create_text_channel("bot-logs", overwrites=ow)
        except Exception as e:
            await interaction.followup.send(branded(f"Channel creation failed: {e}"), ephemeral=True); return
        await set_log_channels(guild.id, p_ch.id, f_ch.id, b_ch.id)
        autorole_text = f"<@&{AUTO_ROLE_ID}>" if AUTO_ROLE_ID else "not configured"
        await interaction.followup.send(branded(f"Setup complete.\nPass: {p_ch.mention}\nFail: {f_ch.mention}\nBot: {b_ch.mention}\nAutorole: {autorole_text}"), ephemeral=True)


# ==================== /debug ====================
@tree.command(name="debug", description="Inspect a BGC, list recent ones, find multi-account patterns, or view stats")
@app_commands.describe(bgc_id="BGC record ID", message="Message link",
                       latest_for="@mention / Discord ID / Roblox username",
                       recent="Recent BGC count", alts="Multi-account patterns", stats="Pass/fail + per-check histogram")
@app_commands.autocomplete(latest_for=debug_latest_ac)
async def debug_cmd(interaction, bgc_id: Optional[int]=None, message: Optional[str]=None,
                    latest_for: Optional[str]=None, recent: int=10, alts: bool=False, stats: bool=False):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    gid = interaction.guild_id or 0

    if stats:
        total = (await db_fetchone("SELECT COUNT(*) FROM bgc_checks WHERE guild_id=?", (gid,)))[0]
        pc = (await db_fetchone("SELECT COUNT(*) FROM bgc_checks WHERE guild_id=? AND passed=1", (gid,)))[0]
        today_iso = datetime.now(timezone.utc).date().isoformat()
        tt = (await db_fetchone("SELECT COUNT(*) FROM bgc_checks WHERE guild_id=? AND DATE(checked_at)=?", (gid, today_iso)))[0]
        rate = f"{pc/total*100:.1f}%" if total else "—"
        e = discord.Embed(title=branded("📊 BGC Stats"), color=T.BRAND, timestamp=datetime.now(timezone.utc))
        e.add_field(name="Total", value=f"`{total}`", inline=True)
        e.add_field(name="✅ Passed", value=f"`{pc}`", inline=True)
        e.add_field(name="❌ Failed", value=f"`{total-pc}`", inline=True)
        e.add_field(name="Pass rate", value=f"`{rate}`", inline=True)
        e.add_field(name="Today", value=f"`{tt}`", inline=True)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        hist = await db_fetchall(
            "SELECT cl.check_name, cl.status, COUNT(*) FROM check_logs cl "
            "JOIN bgc_checks bc ON bc.id = cl.bgc_id "
            "WHERE bc.guild_id=? AND bc.checked_at >= ? "
            "GROUP BY cl.check_name, cl.status", (gid, cutoff))
        if hist:
            per_check = defaultdict(lambda: {"PASS": 0, "HIT": 0, "SKIPPED": 0, "ERROR": 0})
            for name, status, count in hist: per_check[name][status] = count
            firing = sorted(((n,c) for n,c in per_check.items() if c["HIT"] > 0),
                            key=lambda x: x[1]["HIT"], reverse=True)
            silent = sorted(((n,c) for n,c in per_check.items()
                             if c["HIT"]==0 and c["PASS"]>0 and c["ERROR"]==0),
                            key=lambda x: x[1]["PASS"], reverse=True)
            erroring = sorted(((n,c) for n,c in per_check.items() if c["ERROR"] > 0),
                              key=lambda x: x[1]["ERROR"], reverse=True)
            if firing:
                e.add_field(name=f"🔴 Firing — last 30d ({len(firing)})",
                    value="\n".join(f"`{n}` — **{c['HIT']}**/{sum(c.values())} "
                                    f"({c['HIT']*100//max(1,sum(c.values()))}%)"
                                    for n,c in firing[:10])[:1024], inline=False)
            if silent:
                e.add_field(name=f"💤 Silent — probably broken ({len(silent)})",
                    value="\n".join(f"`{n}` — 0 hits / {sum(c.values())} runs"
                                    for n,c in silent[:8])[:1024], inline=False)
            if erroring:
                e.add_field(name=f"🟠 Erroring ({len(erroring)})",
                    value="\n".join(f"`{n}` — 🟠 {c['ERROR']}/{sum(c.values())}"
                                    for n,c in erroring[:8])[:1024], inline=False)
        await interaction.followup.send(embed=e, ephemeral=True); return

    if alts:
        dd = await db_fetchall("SELECT discord_id, GROUP_CONCAT(DISTINCT roblox_username), GROUP_CONCAT(DISTINCT roblox_id) FROM bgc_checks WHERE guild_id=? AND discord_id IS NOT NULL AND roblox_id IS NOT NULL GROUP BY discord_id HAVING COUNT(DISTINCT roblox_id) > 1", (gid,))
        dr = await db_fetchall("SELECT roblox_id, roblox_username, COUNT(DISTINCT discord_id) FROM bgc_checks WHERE guild_id=? AND discord_id IS NOT NULL AND roblox_id IS NOT NULL GROUP BY roblox_id HAVING COUNT(DISTINCT discord_id) > 1", (gid,))
        if not dd and not dr:
            await interaction.followup.send(embed=discord.Embed(title=branded("👥 Multi-Account"), description="✅ None found.", color=T.SUCCESS, timestamp=datetime.now(timezone.utc)), ephemeral=True); return
        rows = []
        for d, nc, _ in dd:
            names = [n for n in (nc or "").split(",") if n]
            rows.append((f"<@{d}> → {len(names)} RBX ID(s)", ", ".join(f"`{n}`" for n in names[:5])))
        for i, u, c in dr: rows.append((f"`{u}` (`{i}`) → {c} Discord(s)", None))
        pages = []
        for start in range(0, len(rows), 5):
            chunk = rows[start:start+5]
            e = discord.Embed(title=branded("👥 Multi-Account"), description=f"{start+1}–{start+len(chunk)} of {len(rows)}", color=T.WARN, timestamp=datetime.now(timezone.utc))
            for h, d in chunk: e.add_field(name=h, value=d or "—", inline=False)
            pages.append(e)
        if len(pages) == 1: await interaction.followup.send(embed=pages[0], ephemeral=True)
        else:
            pager = Paginator(pages, interaction.user.id)
            pager._message = await interaction.followup.send(embed=pages[0], view=pager, ephemeral=True)
        return

    select_cols = "SELECT id, message_id, guild_id, discord_id, roblox_id, roblox_username, passed, reason, raw_responses, bot_version, checks_version, checked_at FROM bgc_checks "
    if not any([bgc_id, message, latest_for]):
        rows = await db_fetchall("SELECT id, message_id, discord_id, roblox_username, roblox_id, passed, reason, checked_at FROM bgc_checks WHERE guild_id=? ORDER BY id DESC LIMIT ?", (gid, max(1, min(recent, 25))))
        if not rows:
            await interaction.followup.send(embed=discord.Embed(title=branded("🐞 No BGCs"), description="Use `/check <username>` or apply in recruitment.", color=T.INFO, timestamp=datetime.now(timezone.utc)), ephemeral=True); return
        rc = await get_recruitment_channel(gid)
        e = discord.Embed(title=branded(f"🐞 Recent ({len(rows)})"), color=T.BRAND, timestamp=datetime.now(timezone.utc))
        lines = []
        for bid, mid, did, un, uid, p, r, at in rows:
            icon = "✅" if p else "❌"; who = f"<@{did}>" if did else "—"
            jump = f" [↗](https://discord.com/channels/{gid}/{rc}/{mid})" if (mid and rc) else ""
            lines.append(f"`#{bid}` {icon} {who} · `{un or '?'}`{jump} · {(r or '')[:50]}")
        e.add_field(name="Results", value="\n".join(lines)[:1024], inline=False)
        await interaction.followup.send(embed=e, ephemeral=True); return
    row = None; not_found = branded("No BGC found.")
    if bgc_id:
        row = await db_fetchone(select_cols + "WHERE id=? AND guild_id=?", (bgc_id, gid))
        not_found = branded(f"BGC #{bgc_id} not found.")
    elif message:
        m = re.search(r'channels/(\d+)/(\d+)/(\d+)', message)
        if not m: await interaction.followup.send(branded("Invalid link."), ephemeral=True); return
        mid = int(m.group(3))
        row = await db_fetchone(select_cols + "WHERE message_id=? AND guild_id=? ORDER BY id DESC LIMIT 1", (mid, gid))
        not_found = branded(f"No BGC for message `{mid}`.")
    else:
        did = parse_discord_target(latest_for)
        if did is not None:
            row = await db_fetchone(select_cols + "WHERE discord_id=? AND guild_id=? ORDER BY id DESC LIMIT 1", (did, gid))
            not_found = branded(f"No BGC for <@{did}>.")
        else:
            user, _ = await roblox_user_lookup(bot.session, latest_for.lstrip('@'))
            if not user: await interaction.followup.send(branded("Could not resolve."), ephemeral=True); return
            row = await db_fetchone(select_cols + "WHERE roblox_id=? AND guild_id=? ORDER BY id DESC LIMIT 1", (user["id"], gid))
            not_found = branded(f"No BGC for `{latest_for}`.")
    if not row: await interaction.followup.send(not_found, ephemeral=True); return
    (bid, mid, gid_row, did, rid, run, p, r, raw, bv, cv, cat) = row
    e = discord.Embed(title=branded(f"🐞 BGC #{bid}"),
                      description=f"**{'✅ Passed' if p else '❌ Failed'}** — {r}",
                      color=T.SUCCESS if p else T.DANGER, timestamp=datetime.now(timezone.utc))
    e.add_field(name="Checked", value=cat, inline=True)
    e.add_field(name="Version", value=f"v{bv} · checks v{cv}", inline=True)
    if mid and gid_row:
        rc = await get_recruitment_channel(gid_row)
        if rc: e.add_field(name="Message", value=f"[Jump](https://discord.com/channels/{gid_row}/{rc}/{mid})", inline=True)
    if did: e.add_field(name="💬 Discord", value=f"<@{did}> (`{did}`)", inline=False)
    if rid:
        e.set_thumbnail(url=T.roblox_avatar(rid))
        e.add_field(name="🎮 Roblox", value=f"`{run}` (`{rid}`)\n🔗 https://www.roblox.com/users/{rid}/profile", inline=False)
    logs = await db_fetchall("SELECT check_name, status, details FROM check_logs WHERE bgc_id=? ORDER BY id", (bid,))
    icon_map = {"PASS":"🟢","HIT":"🔴","SKIPPED":"🟡","ERROR":"🟠"}
    for name, st, det in logs:
        e.add_field(name=f"{icon_map.get(st,'⚪')} {name} [{st}]", value=(det or "—")[:1000], inline=False)
    pseudo = {"profile": {"discord_id": did, "roblox_username": run, "roblox_id": rid}}
    await interaction.followup.send(embed=e, view=_DebugRerunView(pseudo, gid_row), ephemeral=True)


# ==================== /lookup ====================
async def _lookup_single(interaction, target):
    roblox_id = roblox_name = discord_id = None
    history = []; bl_status = "disabled"; resolved_via = None
    mention = parse_discord_target(target)
    if mention is not None:
        discord_id = mention
        bl_id, bl_status = (None, "disabled")
        if BLOXLINK_ENABLED and interaction.guild_id and BLOXLINK_API_KEY and not BLOXLINK_API_KEY.startswith("PASTE"):
            bl_id, bl_status = await bloxlink_discord_to_roblox(bot.session, interaction.guild_id, discord_id)
        if bl_id:
            info, _ = await roblox_user_info(bot.session, bl_id)
            if info and info.get("name"):
                roblox_id = bl_id; roblox_name = info["name"]; resolved_via = "bloxlink"
        if not roblox_id:
            history = await get_all_roblox_history(discord_id, interaction.guild_id or 0)
            if not history:
                await interaction.followup.send(branded(f"No RBX for <@{discord_id}> (Bloxlink: `{bl_status}`)."), ephemeral=True); return
            roblox_id, roblox_name = history[0]; resolved_via = "history"
    else:
        clean = target.lstrip('@').strip()
        user, err = await roblox_user_lookup(bot.session, clean)
        if not user:
            await interaction.followup.send(branded(f"Could not resolve `{clean}`.\n> {err}"), ephemeral=True); return
        roblox_id, roblox_name = user["id"], user["name"]; resolved_via = "username"
    info_task = _spawn(roblox_user_info(bot.session, roblox_id))
    hist_task = _spawn(roblox_username_history(bot.session, roblox_id))
    ks_task = _spawn(get_keystone_cases(bot.session, force_refresh=True))
    simmer_task = _spawn(simmer_rab_check(bot.session, roblox_id))
    snow_task = _spawn(snow_core_check(bot.session, roblox_id, force_refresh=True))
    xt_reg_task = _spawn(xtracker_check(bot.session, "registry/user", roblox_id))
    xt_own_task = _spawn(xtracker_check(bot.session, "ownership/user", roblox_id))
    ext_task = _spawn(search_external_dbs(bot.session, {
        "rbx_ids": {roblox_id}, "rbx_usernames": {roblox_name},
        "discord_ids": {discord_id} if discord_id else set(),
        "discord_usernames": set(),
    }, force_refresh=True))
    info, _ = await info_task
    hist_raw, _ = await hist_task
    cases, ks_err = await ks_task
    simmer = await simmer_task; snow = await snow_task
    xt_reg = await xt_reg_task; xt_own = await xt_own_task
    ext = await ext_task
    past_names = [h["name"] for h in (hist_raw or []) if h.get("name")]
    ks_ids = {str(roblox_id)} | {roblox_name.lower()}
    for p in past_names: ks_ids.add(p.lower())
    active, dead, pending, unknown = [], [], [], []
    if cases is not None: active, dead, pending, unknown = ks_search(cases, ks_ids)
    flagged = bool(active or pending or ext["matches_by_db"]) or (
        simmer["status"] == CheckStatus.HIT or snow["status"] == CheckStatus.HIT or
        xt_reg["status"] == CheckStatus.HIT or xt_own["status"] == CheckStatus.HIT)
    e = discord.Embed(title=branded(f"🔎 Lookup — `{roblox_name}`"),
                      color=T.DANGER if flagged else T.SUCCESS, timestamp=datetime.now(timezone.utc))
    e.set_thumbnail(url=T.roblox_avatar(roblox_id))
    id_lines = [f"[{roblox_name}]({T.roblox_profile(roblox_id)}) · `{roblox_id}`"]
    if info and info.get("created"):
        cs = info["created"]; cd = parse_iso(cs)
        if cd: id_lines.append(f"Created {cs[:10]} ({(datetime.now(timezone.utc)-cd).days}d)")
    e.add_field(name="🎮 Roblox", value="\n".join(id_lines), inline=False)
    e.add_field(name="🔗 Via", value=resolved_via or "—", inline=True)
    if discord_id: e.add_field(name="💬 Discord", value=f"<@{discord_id}>", inline=True)
    if past_names:
        prev = ", ".join(f"`{n}`" for n in past_names[:5])
        if len(past_names) > 5: prev += f" *+{len(past_names)-5}*"
        e.add_field(name=f"📝 Past names ({len(past_names)})", value=prev[:1024], inline=False)
    icon = {"PASS":"🟢","HIT":"🔴","SKIPPED":"🟡","ERROR":"🟠"}
    e.add_field(name=f"{icon.get(xt_reg['status'],'⚪')} Xtracker Registry", value=xt_reg["details"][:400] or "—", inline=False)
    e.add_field(name=f"{icon.get(xt_own['status'],'⚪')} Xtracker Ownership", value=xt_own["details"][:400] or "—", inline=False)
    e.add_field(name=f"{icon.get(simmer['status'],'⚪')} Simmer RAB", value=simmer["details"][:400] or "—", inline=False)
    e.add_field(name=f"{icon.get(snow['status'],'⚪')} Snow Core", value=snow["details"][:400] or "—", inline=False)
    if cases is None:
        e.add_field(name="🛡️ Keystone", value=f"⚠️ {ks_err[:200]}", inline=False)
    elif not (active or pending or dead or unknown):
        e.add_field(name="🛡️ Keystone", value="✅ Not found", inline=False)
    else:
        lines = []
        if active: lines.append(f"🔴 **{len(active)} active**")
        if pending: lines.append(f"🟠 **{len(pending)} pending**")
        if dead: lines.append(f"🟢 **{len(dead)} archived**")
        if unknown: lines.append(f"🟡 **{len(unknown)} unknown**")
        e.add_field(name="🛡️ Keystone", value="\n".join(lines)[:1024], inline=False)
    if ext["matches_by_db"]:
        for k, matches in ext["matches_by_db"].items():
            cfg = next((c for c in EXTERNAL_DATABASES if c["key"]==k), None)
            if not cfg: continue
            link = f"https://docs.google.com/spreadsheets/d/{cfg['sheet_id']}/edit#gid={cfg['gid']}"
            lines = []
            for m in matches[:2]:
                matched = m["matches"][0]
                lines.append(f"> **{matched['token']}** ({matched['match_type']})")
            if len(matches) > 2: lines.append(f"> *+{len(matches)-2} more*")
            e.add_field(name=f"📋 {cfg['name']} ({len(matches)}) · [open]({link})", value="\n".join(lines)[:1024], inline=False)
    else:
        e.add_field(name="📋 External DBs", value=("✅ Clean" if not ext["errors"]
                                                  else f"⚠️ {len(ext['errors'])} DB(s) failed"), inline=False)
    e.set_footer(text=f"v{BOT_VERSION}")
    await interaction.followup.send(embed=e, ephemeral=True)


async def _keystone_role_scan(interaction, role, include_historical=True, force_blacklist_refresh=True):
    g = interaction.guild
    cases, err = await get_keystone_cases(bot.session, force_blacklist_refresh)
    if cases is None:
        await interaction.followup.send(branded(f"Keystone: {err}"), ephemeral=True); return
    if role.is_default(): members = [m for m in g.members if not m.bot]; label = "@everyone"
    else: members = [m for m in role.members if not m.bot]; label = role.name
    hits = 0; checked = 0; no_hist = 0; hit_lines = []
    for m in members:
        hist = await get_all_roblox_history(m.id, g.id)
        if not hist: no_hist += 1; continue
        if include_historical:
            ids = set()
            for hid, hn in hist:
                ids.add(str(hid))
                if hn: ids.add(hn.lower())
        else:
            rid, rn = hist[0]; ids = {str(rid)}
            if rn: ids.add(rn.lower())
        checked += 1
        a, _, p, _ = ks_search(cases, ids)
        if a or p:
            hits += 1
            rid, rn = hist[0]
            refs = [f"{c['source']} #{c['case_id']}" for c in (a+p)[:3]]
            hit_lines.append(f"🔴 {m.mention} — `{rn}` (`{rid}`) · {', '.join(refs)}")
    e = discord.Embed(title=branded(f"🛡️ Keystone Scan — {label}"),
                      color=T.DANGER if hits else T.SUCCESS, timestamp=datetime.now(timezone.utc))
    e.add_field(name="Members", value=str(len(members)), inline=True)
    e.add_field(name="Checked", value=str(checked), inline=True)
    e.add_field(name="No history", value=str(no_hist), inline=True)
    e.add_field(name="Hits", value=str(hits), inline=True)
    if hit_lines: e.add_field(name="Flagged", value="\n".join(hit_lines[:15])[:1024], inline=False)
    await interaction.followup.send(embed=e, ephemeral=True)


@tree.command(name="lookup", description="Full user lookup (identity + all databases) — or scan a role against Keystone")
@app_commands.describe(target="Roblox username, @mention, or Discord ID",
                       role="Role scan for Keystone", include_historical="Use all RBX IDs for role scan")
@app_commands.autocomplete(target=roblox_name_ac)
async def lookup_cmd(interaction, target: Optional[str]=None, role: Optional[discord.Role]=None, include_historical: bool=True):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    if not target and not role:
        await interaction.response.send_message(branded("Provide `target` and/or `role`."), ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    first = False
    if target: await _lookup_single(interaction, target); first = True
    if role: await _keystone_role_scan(interaction, role, include_historical=include_historical,
                                        force_blacklist_refresh=not first)


# ==================== /check ====================
@tree.command(name="check", description="Run a BGC on a message link, Roblox username, @mention, or Discord ID")
@app_commands.describe(target="Message link / username / @mention / Discord ID", dry_run="No reactions/replies/logs")
@app_commands.autocomplete(target=roblox_name_ac)
async def check_cmd(interaction, target: str, dry_run: bool=False):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    dt = parse_discord_target(target)
    if dt is not None:
        async with bot.bgc_semaphore:
            result = await run_bgc_by_discord_id(dt, interaction.guild_id or 0,
                                                  force_blacklist_refresh=True, skip_preemptive=True)
        e = build_result_embed(result, f"Check · <@{dt}>", runner=interaction.user)
        if dry_run: e.title = branded(f"[Dry Run] {e.title}")
        await interaction.followup.send(embed=e, view=BGCResultView(result, interaction.guild_id or 0, interaction.user.id), ephemeral=True); return
    m = re.search(r'channels/(\d+)/(\d+)/(\d+)', target)
    if m:
        gid, cid, mid = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (OWNER_ID and interaction.user.id == OWNER_ID):
            rc = await get_recruitment_channel(gid)
            if not rc or cid != rc:
                await interaction.followup.send(branded(f"Non-owners: only <#{rc}>." if rc else "No recruitment channel configured."), ephemeral=True); return
        try:
            ch = bot.get_channel(cid) or await bot.fetch_channel(cid)
            msg = await ch.fetch_message(mid)
        except Exception as e:
            await interaction.followup.send(branded(f"Could not fetch message: {e}"), ephemeral=True); return
        result = await process_message(msg, gid, dry_run=dry_run, force_blacklist_refresh=True,
                                        show_progress=not dry_run, runner=interaction.user,
                                        skip_preemptive=True)
        if result.get("skipped_template"):
            await interaction.followup.send(branded("Format template, not an application."), ephemeral=True); return
        if result.get("skipped_dup"):
            await interaction.followup.send(branded("Already checked."), ephemeral=True); return
        e = build_result_embed(result, "Check · Message", runner=interaction.user)
        if dry_run: e.title = branded(f"[Dry Run] {e.title}")
        await interaction.followup.send(embed=e, view=BGCResultView(result, gid, interaction.user.id), ephemeral=True); return
    async with bot.bgc_semaphore:
        result = await run_bgc_by_username(target, interaction.guild_id or 0, force_blacklist_refresh=True,
                                            check_banned=True, skip_preemptive=True)
    e = build_result_embed(result, f"Check · `{target}`", runner=interaction.user)
    if dry_run: e.title = branded(f"[Dry Run] {e.title}")
    await interaction.followup.send(embed=e, view=BGCResultView(result, interaction.guild_id or 0, interaction.user.id), ephemeral=True)
    if not dry_run and interaction.guild_id:
        await send_logs(result, interaction.guild_id, None, interaction.user)


# ==================== /backfill ====================
@tree.command(name="backfill", description="Re-run BGC on historical recruitment messages")
@app_commands.describe(limit="Max messages (default 100, max 1000)", recheck="Re-run even for already-checked",
                       skip_chitchat="Skip non-applications", silent="Reactions only — no replies")
async def backfill_cmd(interaction, limit: int=100, recheck: bool=False, skip_chitchat: bool=True, silent: bool=True):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message(branded("Guild only."), ephemeral=True); return
    if not (1 <= limit <= 1000):
        await interaction.response.send_message(branded("Limit 1–1000."), ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    status = await interaction.followup.send(branded(f"⏳ Backfilling… `0 / {limit}`"), ephemeral=True)
    rc = await get_recruitment_channel(guild.id)
    if not rc:
        await status.edit(content=branded("❌ No recruitment channel configured. Run `/setup`.")); return
    try: ch = bot.get_channel(rc) or await bot.fetch_channel(rc)
    except Exception as e:
        await status.edit(content=branded(f"❌ Channel: {e}")); return
    await get_group_blacklist(bot.session, force_refresh=True); await get_user_blacklist(bot.session, force_refresh=True)
    await get_keystone_cases(bot.session, force_refresh=True); await get_snow_core(bot.session, force_refresh=True)
    for cfg in EXTERNAL_DATABASES: await fetch_external_db(bot.session, cfg, force_refresh=True)
    checked = skipped = passed = failed = errors = 0; processed = 0
    async for msg in ch.history(limit=limit):
        processed += 1
        if processed % 10 == 0:
            try: await status.edit(content=branded(f"⏳ `{processed}/{limit}` · ✅ {passed} · ❌ {failed}"))
            except: pass
        if msg.author.bot or is_format_template(msg.content): skipped += 1; continue
        if skip_chitchat and not looks_like_application(msg.content): skipped += 1; continue
        if is_privileged_member(msg.author): skipped += 1; continue
        if not recheck and await is_already_checked(msg.id): skipped += 1; continue
        try:
            r = await process_message(msg, guild.id, dry_run=False, from_edit=recheck,
                                       force_blacklist_refresh=False, silent=silent, show_progress=False)
            if r.get("skipped_dup") or r.get("skipped_template"): skipped += 1
            else:
                checked += 1
                if r.get("passed"): passed += 1
                else: failed += 1
        except Exception as e:
            logger.error(f"Backfill error: {e}"); errors += 1
    e = discord.Embed(title=branded("🔄 Backfill Complete"),
                      description=(f"✅ {passed} · ❌ {failed}\n⏭️ {skipped} · 🟠 {errors}\n"
                                   f"**Checked:** `{checked}` · **Scanned:** `{processed}`"),
                      color=T.SUCCESS if not failed and not errors else T.WARN, timestamp=datetime.now(timezone.utc))
    try: await status.edit(content=None, embed=e)
    except: await interaction.followup.send(embed=e, ephemeral=True)


# ==================== /reset ====================
@tree.command(name="reset", description="Owner only — wipe guild settings (roles never removed)")
@app_commands.describe(confirm="Direct confirmation", clear_history="Also delete BGC history")
async def reset_cmd(interaction, confirm: bool=False, clear_history: bool=False):
    if not OWNER_ID or interaction.user.id != OWNER_ID:
        await interaction.response.send_message(branded("Owner only."), ephemeral=True); return
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message(branded("Guild only."), ephemeral=True); return
    if not confirm:
        v = ConfirmResetView(interaction.user.id)
        e = discord.Embed(title=branded("⚠️ Confirm Reset"),
                          description=(f"**Guild: {guild.name}**\n"
                                       f"{'Will also delete BGC history.' if clear_history else 'History preserved.'}\n"
                                       "Roles are never removed by reset."),
                          color=T.WARN, timestamp=datetime.now(timezone.utc))
        await interaction.response.send_message(embed=e, view=v, ephemeral=True)
        v._message = await interaction.original_response()
        await v.wait()
        if not v.confirmed: return
    else:
        await interaction.response.defer(ephemeral=True)
    async with bot.db_lock:
        await bot.db.execute("DELETE FROM guild_settings WHERE guild_id=?", (guild.id,))
        hc = 0
        if clear_history:
            async with bot.db.execute("SELECT COUNT(*) FROM bgc_checks WHERE guild_id=?", (guild.id,)) as cur:
                row = await cur.fetchone(); hc = row[0] if row else 0
            await bot.db.execute("DELETE FROM check_logs WHERE bgc_id IN (SELECT id FROM bgc_checks WHERE guild_id=?)", (guild.id,))
            await bot.db.execute("DELETE FROM bgc_checks WHERE guild_id=?", (guild.id,))
        await bot.db.commit()
    bot._reset_caches()
    e = discord.Embed(title=branded("🗑️ Reset Complete"),
                      description=f"**{guild.name}**\n"
                                  + (f"Deleted `{hc}` BGC records.\n" if clear_history else "")
                                  + "Run `/setup` to reconfigure.",
                      color=T.SUCCESS, timestamp=datetime.now(timezone.utc))
    try:
        if confirm: await interaction.followup.send(embed=e, ephemeral=True)
        else: await interaction.edit_original_response(embed=e, view=None)
    except: pass


# ==================== /health (group) ====================
health_group = app_commands.Group(name="health", description="Health checks, cache management, and diagnostics")


@health_group.command(name="check", description="Ping all services, refresh caches, DM preview, verbose per-user test")
@app_commands.describe(test_users="Comma-separated usernames for verbose per-user test",
                       test_dm="Send exact acceptance DM to yourself")
async def health_check(interaction, test_users: Optional[str]=None, test_dm: bool=False):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    await interaction.response.defer(ephemeral=True)

    groups = {"📋 Blacklists": [], "🌐 Roblox API": [], "🕵️ Watchlists": [],
              "🎭 Autorole & DM": [], "🗄️ External DBs": [], "🧠 Preemptive": [], "💾 System": []}
    bot._reset_caches()
    t0 = time.perf_counter()
    gbl, gbl_e = await get_group_blacklist(bot.session, force_refresh=True)
    groups["📋 Blacklists"].append(f"{'🟢' if gbl is not None else '🔴'} Group `{len(gbl) if gbl is not None else gbl_e}` (`{int((time.perf_counter()-t0)*1000)}ms`)")
    t0 = time.perf_counter()
    ubl, ubl_e = await get_user_blacklist(bot.session, force_refresh=True)
    groups["📋 Blacklists"].append(f"{'🟢' if ubl is not None else '🔴'} User `{len(ubl) if ubl is not None else ubl_e}` (`{int((time.perf_counter()-t0)*1000)}ms`)")
    t0 = time.perf_counter()
    ksc, ks_e = await get_keystone_cases(bot.session, force_refresh=True)
    groups["📋 Blacklists"].append(f"{'🟢' if ksc is not None else '🔴'} Keystone `{len(ksc) if ksc is not None else ks_e}` (`{int((time.perf_counter()-t0)*1000)}ms`)")
    t0 = time.perf_counter()
    snc, snc_e = await get_snow_core(bot.session, force_refresh=True)
    groups["📋 Blacklists"].append(f"{'🟢' if snc is not None else '🔴'} Snow Core `{len(snc) if snc is not None else snc_e}` (`{int((time.perf_counter()-t0)*1000)}ms`)")
    for p in ("rotunnel", "roproxy"):
        ru = await _health_endpoint(bot.session, f"users.{p}.com", "/v1/users/1")
        groups["🌐 Roblox API"].append(f"{'🟢' if ru['ok'] else '🔴'} users.{p}.com" + (f" — {ru['error']}" if not ru['ok'] else ""))
        rg = await _health_endpoint(bot.session, f"groups.{p}.com", "/v1/users/1/groups/roles")
        groups["🌐 Roblox API"].append(f"{'🟢' if rg['ok'] else '🔴'} groups.{p}.com" + (f" — {rg['error']}" if not rg['ok'] else ""))
    rd = await _health_endpoint(bot.session, "users.roblox.com", "/v1/users/1")
    groups["🌐 Roblox API"].append(f"{'🟢' if rd['ok'] else '🔴'} users.roblox.com" + (f" — {rd['error']}" if not rd['ok'] else ""))
    rgd = await _health_endpoint(bot.session, "groups.roblox.com", "/v1/users/1/groups/roles")
    groups["🌐 Roblox API"].append(f"{'🟢' if rgd['ok'] else '🔴'} groups.roblox.com" + (f" — {rgd['error']}" if not rgd['ok'] else ""))
    tid = HEALTH_TEST_ROBLOX_ID or 1
    for ep in ("registry/user", "ownership/user"):
        r = await xtracker_check(bot.session, ep, tid)
        groups["🕵️ Watchlists"].append(f"{'🟢' if r['status'] != CheckStatus.SKIPPED else '🔴'} Xtracker `{ep}` — `{r['status']}`")
    srab = await simmer_rab_check(bot.session, tid)
    groups["🕵️ Watchlists"].append(f"{'🟢' if srab['status'] != CheckStatus.SKIPPED else '🔴'} Simmer RAB — `{srab['status']}`")
    if HEALTH_TEST_DISCORD_ID:
        for nm, k, prod in [("Roblox Watcher", RW_API_KEY, "robloxwatcher"), ("Exploit Watcher", EW_API_KEY, "exploitwatcher")]:
            r = await watcher_check(bot.session, HEALTH_TEST_DISCORD_ID, k, prod)
            groups["🕵️ Watchlists"].append(f"{'🟢' if r['status'] != CheckStatus.SKIPPED else '🔴'} {nm} — `{r['status']}`")
    else:
        groups["🕵️ Watchlists"].append("⚪ Watchers — not configured")
    groups["🕵️ Watchlists"].append(f"{'🟢' if EXPLOIT_WATCHER_INFORMATIONAL else '🔴'} Exploit Watcher — {'informational' if EXPLOIT_WATCHER_INFORMATIONAL else 'blocks'}")
    if BLOXLINK_ENABLED and BLOXLINK_API_KEY and not BLOXLINK_API_KEY.startswith("PASTE"):
        if interaction.guild:
            _, st = await bloxlink_discord_to_roblox(bot.session, interaction.guild.id, interaction.user.id)
            if st in ("ok", "not_linked"): groups["🕵️ Watchlists"].append(f"🟢 Bloxlink — reachable ({st})")
            elif st == "rate_limited": groups["🕵️ Watchlists"].append("🟠 Bloxlink — rate limited")
            elif st == "invalid_key": groups["🕵️ Watchlists"].append("🔴 Bloxlink — invalid key")
            else: groups["🕵️ Watchlists"].append(f"🔴 Bloxlink — {st[:60]}")
        else: groups["🕵️ Watchlists"].append("⚪ Bloxlink — guild required")
    else: groups["🕵️ Watchlists"].append("⚪ Bloxlink — disabled")
    if AUTO_ROLE_ID and interaction.guild:
        role = interaction.guild.get_role(AUTO_ROLE_ID); me = interaction.guild.me
        if role is None: groups["🎭 Autorole & DM"].append(f"🔴 Role `{AUTO_ROLE_ID}` missing")
        elif me is None: groups["🎭 Autorole & DM"].append("🟠 Bot member not cached")
        elif not me.guild_permissions.manage_roles: groups["🎭 Autorole & DM"].append("🔴 No Manage Roles")
        elif role.position >= me.top_role.position: groups["🎭 Autorole & DM"].append(f"🔴 Role `{role.name}` above bot")
        else: groups["🎭 Autorole & DM"].append(f"🟢 Ready — will apply {role.mention}")
    else: groups["🎭 Autorole & DM"].append("⚪ Not configured")
    groups["🎭 Autorole & DM"].append(f"{'🟢' if ACCEPTANCE_DM_ENABLED else '⚪'} Acceptance DM — {'enabled' if ACCEPTANCE_DM_ENABLED else 'disabled'} (`{len(ACCEPTANCE_DM_TEMPLATE)}` chars)")
    for cfg in EXTERNAL_DATABASES:
        t0 = time.perf_counter()
        payload, err = await fetch_external_db(bot.session, cfg, force_refresh=True)
        if payload: groups["🗄️ External DBs"].append(f"🟢 {cfg['name']} — `{len(payload['records'])}` rows (`{int((time.perf_counter()-t0)*1000)}ms`)")
        else: groups["🗄️ External DBs"].append(f"🔴 {cfg['name']} — {err[:60]}")
    if not EXTERNAL_DATABASES:
        groups["🗄️ External DBs"].append("⚪ None configured")
    try:
        row = await db_fetchone("SELECT COUNT(*) FROM preemptive_scans")
        total_pre = row[0] if row else 0
        row = await db_fetchone(
            "SELECT COUNT(*) FROM preemptive_scans WHERE identity_scanned_at >= ?",
            ((datetime.now(timezone.utc) - timedelta(days=IDENTITY_TTL_DAYS)).isoformat(),))
        id_fresh = row[0] if row else 0
        row = await db_fetchone(
            "SELECT COUNT(*) FROM preemptive_scans WHERE xtracker_scanned_at >= ?",
            ((datetime.now(timezone.utc) - timedelta(days=XTRACKER_CACHE_TTL_DAYS)).isoformat(),))
        xt_fresh = row[0] if row else 0
        row = await db_fetchone(
            "SELECT COUNT(*) FROM preemptive_scans WHERE freshness_scanned_at >= ?",
            ((datetime.now(timezone.utc) - timedelta(minutes=FRESHNESS_TTL_MIN)).isoformat(),))
        fresh_fresh = row[0] if row else 0
        groups["🧠 Preemptive"].append(f"Records: `{total_pre}`")
        groups["🧠 Preemptive"].append(f"id fresh: `{id_fresh}` · xtracker fresh: `{xt_fresh}` · fresh: `{fresh_fresh}`")
        groups["🧠 Preemptive"].append(f"Hits: `{bot._metrics_preemptive_hits}` · Misses: `{bot._metrics_preemptive_misses}` · Bloxlink timeouts: `{bot._metrics_bloxlink_timeouts}`")
        groups["🧠 Preemptive"].append(f"TTLs — identity `{IDENTITY_TTL_DAYS}d` · xtracker `{XTRACKER_CACHE_TTL_DAYS}d` · freshness `{FRESHNESS_TTL_MIN}m`")
    except Exception as e:
        groups["🧠 Preemptive"].append(f"🔴 {e}")
    try:
        await db_fetchone("SELECT 1")
        groups["💾 System"].append("🟢 SQLite DB")
    except Exception as e: groups["💾 System"].append(f"🔴 DB — {e}")
    groups["💾 System"].append(f"🟢 Bot v`{BOT_VERSION}` · checks v`{CHECKS_VERSION}`" + (f" · **{BRAND_NAME}**" if BRAND_NAME else ""))
    groups["💾 System"].append(f"aiodns: `{'on' if _AIODNS_AVAILABLE else 'off'}` · Xtracker limiter: `{bot.xtracker_limiter.interval:.2f}s` · Bloxlink cap: `{BLOXLINK_HARD_TIMEOUT_MS}ms`")
    groups["💾 System"].append(f"made by {BOT_AUTHOR} · {BOT_AUTHOR_URL}")
    e = discord.Embed(title=branded("🩺 Health Check"), color=T.BRAND, timestamp=datetime.now(timezone.utc))
    for name, lines in groups.items():
        if lines: e.add_field(name=name, value="\n".join(lines)[:1024], inline=False)
    e.set_footer(text=f"v{BOT_VERSION}")
    await interaction.followup.send(embed=e, ephemeral=True)
    if test_dm:
        dm = await _send_acceptance_dm(interaction.user, interaction.guild)
        if dm["sent"]:
            await interaction.followup.send(embed=discord.Embed(title=branded("📬 Test DM Sent"),
                                                                description="Check your DMs.", color=T.SUCCESS), ephemeral=True)
        else:
            await interaction.followup.send(embed=discord.Embed(title=branded("📬 Test DM Failed"),
                                                                description=f"**Reason:** {dm['reason']}", color=T.WARN), ephemeral=True)
    if test_users:
        for name in [n.strip() for n in test_users.split(",") if n.strip()]:
            user, _ = await roblox_user_lookup(bot.session, name)
            if not user:
                await interaction.followup.send(branded(f"`{name}` not found"), ephemeral=True); continue
            uid = user["id"]
            xt_r = await xtracker_check(bot.session, "registry/user", uid)
            xt_o = await xtracker_check(bot.session, "ownership/user", uid)
            srab = await simmer_rab_check(bot.session, uid)
            snc = await snow_core_check(bot.session, uid)
            body = (f"**{name}** (`{uid}`)\n"
                    f"`xtracker reg` → **{xt_r['status']}**\n```{xt_r['details'][:400]}```\n"
                    f"`xtracker own` → **{xt_o['status']}**\n```{xt_o['details'][:400]}```\n"
                    f"`simmer RAB` → **{srab['status']}**\n```{srab['details'][:400]}```\n"
                    f"`snow core` → **{snc['status']}**\n```{snc['details'][:400]}```")
            for i in range(0, len(body), 1900):
                await interaction.followup.send(body[i:i+1900], ephemeral=True)


@health_group.command(name="quick", description="Skip endpoint tests — just refresh all caches")
async def health_quick(interaction):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    bot._reset_caches()
    gbl, _ = await get_group_blacklist(bot.session, force_refresh=True)
    ubl, _ = await get_user_blacklist(bot.session, force_refresh=True)
    ksc, _ = await get_keystone_cases(bot.session, force_refresh=True)
    snc, _ = await get_snow_core(bot.session, force_refresh=True)
    ext_lines = []
    for cfg in EXTERNAL_DATABASES:
        payload, err = await fetch_external_db(bot.session, cfg, force_refresh=True)
        if payload: ext_lines.append(f"🟢 {cfg['name']}: `{len(payload['records'])}` rows")
        else: ext_lines.append(f"🔴 {cfg['name']}: {err}")
    lines = [
        (f"✅ Group blacklist: `{len(gbl)}`" if gbl is not None else "❌ Group"),
        (f"✅ User blacklist: `{len(ubl)}`" if ubl is not None else "❌ User"),
        (f"✅ Keystone: `{len(ksc)}`" if ksc is not None else "❌ Keystone"),
        (f"✅ Snow Core: `{len(snc)}`" if snc is not None else "❌ Snow Core"),
    ] + ext_lines
    await interaction.followup.send(embed=discord.Embed(
        title=branded("🔄 Refreshed"), description="\n".join(lines),
        color=T.SUCCESS if all(x is not None for x in (gbl, ubl, ksc, snc)) else T.WARN,
        timestamp=datetime.now(timezone.utc)), ephemeral=True)


@health_group.command(name="preemptive",
                      description="Seed a preemptive record for a user (for fast-path testing)")
@app_commands.describe(target="Discord @mention / Discord ID in this guild")
async def health_preemptive(interaction, target: str):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message(branded("Guild only."), ephemeral=True); return
    did = parse_discord_target(target)
    if did is None:
        await interaction.response.send_message(branded("Provide a Discord @mention or ID."), ephemeral=True); return
    member = guild.get_member(did)
    if member is None:
        await interaction.response.send_message(branded("User not in this guild."), ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    key = (did, guild.id)
    if key in _pending_preemptive:
        await interaction.followup.send(branded("Scan already in progress."), ephemeral=True); return
    _pending_preemptive.add(key)
    await _preemptive_scan(member, guild, key)
    row = await db_fetchone(
        "SELECT bloxlink_roblox_id, bloxlink_status, identity_scanned_at, xtracker_scanned_at, freshness_scanned_at "
        "FROM preemptive_scans WHERE discord_id=? AND guild_id=?",
        (did, guild.id))
    if not row:
        await interaction.followup.send(branded("Scan did not produce a record (see logs)."), ephemeral=True); return
    e = discord.Embed(title=branded("🧠 Preemptive Seeded"), color=T.SUCCESS,
                      timestamp=datetime.now(timezone.utc))
    e.add_field(name="User", value=f"<@{did}> (`{did}`)", inline=False)
    e.add_field(name="Roblox ID", value=f"`{row[0] or '—'}`", inline=True)
    e.add_field(name="Status", value=f"`{row[1] or '—'}`", inline=True)
    e.add_field(name="Identity scanned", value=row[2] or "—", inline=False)
    e.add_field(name="Xtracker scanned", value=row[3] or "—", inline=False)
    e.add_field(name="Freshness scanned", value=row[4] or "—", inline=False)
    await interaction.followup.send(embed=e, ephemeral=True)


@health_group.command(name="timeline",
                      description="Live-path BGC timeline. Preemptive cache bypassed. Full per-task timings.")
@app_commands.describe(target="Optional: Discord @mention / Discord ID (defaults to HEALTH_TEST_DISCORD_ID)")
async def health_timeline(interaction, target: Optional[str]=None):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    did = None; member = None
    if target:
        did = parse_discord_target(target)
        if did is None:
            await interaction.response.send_message(branded("Provide a Discord @mention or ID."), ephemeral=True); return
        if interaction.guild:
            member = interaction.guild.get_member(did)
    else:
        did = HEALTH_TEST_DISCORD_ID
        if not did or not HEALTH_TEST_ROBLOX_ID:
            await interaction.response.send_message(branded(
                "Pass `target` or set `HEALTH_TEST_ROBLOX_ID` + `HEALTH_TEST_DISCORD_ID` in config."),
                ephemeral=True)
            return
        if interaction.guild:
            member = interaction.guild.get_member(did)

    await interaction.response.defer(ephemeral=True)

    rid_hint = HEALTH_TEST_ROBLOX_ID if not target else None
    username = None
    if rid_hint:
        info, info_err = await roblox_user_info(bot.session, rid_hint)
        if not info or not info.get("name"):
            await interaction.followup.send(branded(f"Could not resolve test Roblox ID {rid_hint}: {info_err}"), ephemeral=True); return
        username = info["name"]
    elif did:
        hist = await get_all_roblox_history(did, interaction.guild_id or 0)
        if hist:
            info, _ = await roblox_user_info(bot.session, hist[0][0])
            if info and info.get("name"): username = info["name"]

    if not username:
        await interaction.followup.send(branded("Could not resolve a Roblox username for this user."), ephemeral=True); return

    if rid_hint:
        _roblox_info_cache.pop(rid_hint, None)
        _roblox_hist_cache.pop(rid_hint, None)
        _roblox_groups_cache.pop(rid_hint, None)
        _simmer_cache.pop(rid_hint, None)

    cache_state = "warm" if _caches_hot() else "COLD"

    timings = []
    t_start = time.perf_counter()
    try:
        result = await run_bgc_core(
            username, did, interaction.guild_id or 0,
            message_id=None, parsed_self_report=None,
            force_blacklist_refresh=False,
            timings=timings, member=member,
            skip_db_history=True,
            skip_preemptive=True)
    except Exception as e:
        await interaction.followup.send(branded(
            f"Timeline probe raised: {type(e).__name__}: {e}"), ephemeral=True)
        return
    total = (time.perf_counter() - t_start) * 1000.0

    header = [
        "══════ BGC TIMELINE (LIVE PATH) ══════",
        f"Discord:  {did}" + (" (member)" if member else " (not cached)"),
        f"Roblox:   {username}" + (f" ({rid_hint})" if rid_hint else ""),
        f"Cache:    {cache_state}",
        f"Mode:     live path — preemptive bypassed",
        f"Xtracker: limiter={bot.xtracker_limiter.interval:.2f}s",
        f"Bloxlink: hard timeout {BLOXLINK_HARD_TIMEOUT_MS}ms",
    ]
    body = _format_timeline(timings, t_start, total, result, header)
    body += "\n\n─ Notes ─\n"
    body += "• Per-UID Roblox caches cleared — this is what a fresh applicant sees.\n"
    body += "• Preemptive was bypassed for a pure live-path measurement.\n"
    body += "• Use /health preemptive_timeline @user for the fast-path comparison.\n"

    for i in range(0, len(body), 1900):
        await interaction.followup.send(body[i:i+1900], ephemeral=True)


@health_group.command(name="preemptive_timeline",
                      description="Seed preemptive for a user, then measure the fast-path BGC (seed time excluded)")
@app_commands.describe(target="Discord @mention / Discord ID in this guild")
async def health_preemptive_timeline(interaction, target: str):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message(branded("Guild only."), ephemeral=True); return
    did = parse_discord_target(target)
    if did is None:
        await interaction.response.send_message(branded("Provide a Discord @mention or ID."), ephemeral=True); return
    member = guild.get_member(did)
    if member is None:
        await interaction.response.send_message(branded("User not in this guild."), ephemeral=True); return
    await interaction.response.defer(ephemeral=True)

    async with bot.db_lock:
        await bot.db.execute("DELETE FROM preemptive_scans WHERE discord_id=? AND guild_id=?", (did, guild.id))
        await bot.db.commit()
    _bloxlink_late_cache.pop((did, guild.id), None)

    key = (did, guild.id)
    _pending_preemptive.discard(key)
    _pending_preemptive.add(key)
    t_pre_start = time.perf_counter()
    try:
        await _preemptive_scan(member, guild, key)
    except Exception as e:
        await interaction.followup.send(branded(f"Preemptive scan raised: {type(e).__name__}: {e}"), ephemeral=True); return
    t_pre_ms = (time.perf_counter() - t_pre_start) * 1000.0

    row = await db_fetchone(
        "SELECT bloxlink_roblox_id, bloxlink_status, identity_scanned_at, xtracker_scanned_at, freshness_scanned_at "
        "FROM preemptive_scans WHERE discord_id=? AND guild_id=?", (did, guild.id))
    if not row:
        await interaction.followup.send(branded("Preemptive scan produced no record — see logs."), ephemeral=True); return
    if not row[0]:
        await interaction.followup.send(branded(
            f"Preemptive resolved no Roblox ID (status: `{row[1]}`). "
            f"Use /health timeline @{did} for the live path."), ephemeral=True); return
    preemptive_rid = row[0]

    info, info_err = await roblox_user_info(bot.session, preemptive_rid)
    if not info or not info.get("name"):
        await interaction.followup.send(branded(f"Could not resolve Roblox ID {preemptive_rid}: {info_err}"), ephemeral=True); return
    username = info["name"]

    timings = []
    t_start = time.perf_counter()
    try:
        result = await run_bgc_core(
            username, did, guild.id,
            message_id=None, parsed_self_report=None,
            force_blacklist_refresh=False,
            timings=timings, member=member,
            skip_db_history=True,
            skip_preemptive=False)
    except Exception as e:
        await interaction.followup.send(branded(
            f"Timeline raised: {type(e).__name__}: {e}"), ephemeral=True); return
    total = (time.perf_counter() - t_start) * 1000.0

    header = [
        "══════ BGC TIMELINE (PREEMPTIVE FAST PATH) ══════",
        f"Discord:  {did} (member)",
        f"Roblox:   {username} ({preemptive_rid})",
        f"Preemptive seed: {t_pre_ms:.0f}ms (NOT counted in BGC time)",
        f"Bloxlink status: {row[1]}",
        f"Mode:     preemptive ENABLED — fast path as users experience",
        f"Xtracker: limiter={bot.xtracker_limiter.interval:.2f}s",
    ]
    body = _format_timeline(timings, t_start, total, result, header)
    body += "\n\n─ Notes ─\n"
    body += f"• Preemptive seed: {t_pre_ms:.0f}ms — done before timing, not part of BGC total.\n"
    body += "• Xtracker cached 3 days; groups/simmer 30 min; identity 7 days.\n"
    body += "• Compare with /health timeline @user for the live-path baseline.\n"

    for i in range(0, len(body), 1900):
        await interaction.followup.send(body[i:i+1900], ephemeral=True)


tree.add_command(health_group)


# ==================== /wipeuser ====================
async def _resolve_wipe_identities(session, target):
    discord_ids, roblox_ids = set(), set()
    dt = parse_discord_target(target)
    if dt is not None: discord_ids.add(int(dt))
    else:
        user, _ = await roblox_user_lookup(session, target.lstrip('@').strip())
        if user: roblox_ids.add(int(user["id"]))
    for _ in range(2):
        if not discord_ids and not roblox_ids: break
        d_list = list(discord_ids) or [0]; r_list = list(roblox_ids) or [0]
        rows = await db_fetchall(
            f"SELECT DISTINCT discord_id, roblox_id FROM bgc_checks "
            f"WHERE discord_id IN ({','.join('?'*len(d_list))}) OR roblox_id IN ({','.join('?'*len(r_list))})",
            tuple(d_list) + tuple(r_list))
        added = False
        for did, rid in rows:
            if did and did not in discord_ids: discord_ids.add(int(did)); added = True
            if rid and rid not in roblox_ids: roblox_ids.add(int(rid)); added = True
        if not added: break
    if len(discord_ids) == 1: display = f"<@{next(iter(discord_ids))}>"
    elif len(roblox_ids) == 1: display = f"RBX `{next(iter(roblox_ids))}`"
    else: display = target
    return discord_ids, roblox_ids, display


@tree.command(name="wipeuser",
              description="Delete all local BGC data the bot has stored about one user (external DBs untouched)")
@app_commands.describe(target="Discord @mention / Discord ID / Roblox username",
                       hard="Also wipe every linked account in the multi-account graph")
async def wipeuser_cmd(interaction, target: str, hard: bool = False):
    if not authorized(interaction):
        await interaction.response.send_message(branded("Not authorized."), ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    gid = interaction.guild_id or 0
    try:
        discord_ids, roblox_ids, display = await _resolve_wipe_identities(bot.session, target)
    except Exception as e:
        await interaction.followup.send(branded(f"Resolution failed: {e}"), ephemeral=True); return
    if not discord_ids and not roblox_ids:
        await interaction.followup.send(branded(f"Could not resolve `{target}` to any stored record."), ephemeral=True); return
    wheres, params = [], []
    if discord_ids: wheres.append(f"discord_id IN ({','.join('?'*len(discord_ids))})"); params.extend(discord_ids)
    if roblox_ids: wheres.append(f"roblox_id IN ({','.join('?'*len(roblox_ids))})"); params.extend(roblox_ids)
    if not wheres:
        await interaction.followup.send(branded("Nothing to wipe."), ephemeral=True); return
    where_clause = " OR ".join(wheres)
    row = await db_fetchone(f"SELECT COUNT(*) FROM bgc_checks WHERE guild_id=? AND ({where_clause})", (gid, *params))
    total = row[0] if row else 0
    preview = (f"**Target:** {display}\n**Guild:** {interaction.guild.name}\n\n"
               f"**Discord IDs:** {', '.join(f'`{d}`' for d in sorted(discord_ids)) or '—'}\n"
               f"**Roblox IDs:**  {', '.join(f'`{r}`' for r in sorted(roblox_ids)) or '—'}\n\n"
               f"Will delete **{total}** BGC record(s) + associated check logs from **this guild's local DB**.\n"
               f"🛑 **External blacklists, external sheets, Bloxlink, Xtracker, etc. are NOT touched.**\n"
               f"🛑 Cannot be undone.\n"
               f"Graph scope: **{'hard — every linked account also wiped' if hard else 'direct matches only'}**")
    view = ConfirmWipeView(interaction.user.id, display)
    msg = await interaction.followup.send(
        embed=discord.Embed(title=branded("⚠️ Confirm User Wipe"), description=preview,
                            color=T.DANGER, timestamp=datetime.now(timezone.utc)),
        view=view, ephemeral=True)
    view._message = msg
    await view.wait()
    if not view.confirmed: return
    if hard:
        d2, r2, _ = await _resolve_wipe_identities(bot.session, target)
        discord_ids |= d2; roblox_ids |= r2
        wheres, params = [], []
        if discord_ids: wheres.append(f"discord_id IN ({','.join('?'*len(discord_ids))})"); params.extend(discord_ids)
        if roblox_ids: wheres.append(f"roblox_id IN ({','.join('?'*len(roblox_ids))})"); params.extend(roblox_ids)
        where_clause = " OR ".join(wheres)
    deleted_bgc = deleted_logs = 0
    async with bot.db_lock:
        async with bot.db.execute(f"SELECT id FROM bgc_checks WHERE guild_id=? AND ({where_clause})", (gid, *params)) as cur:
            bgc_ids = [r[0] for r in await cur.fetchall()]
        if bgc_ids:
            async with bot.db.execute(f"DELETE FROM check_logs WHERE bgc_id IN ({','.join('?'*len(bgc_ids))})", bgc_ids) as cur:
                deleted_logs = cur.rowcount
            async with bot.db.execute(f"DELETE FROM bgc_checks WHERE id IN ({','.join('?'*len(bgc_ids))})", bgc_ids) as cur:
                deleted_bgc = cur.rowcount
        for did in discord_ids:
            await bot.db.execute("DELETE FROM preemptive_scans WHERE discord_id=? AND guild_id=?", (did, gid))
            _bloxlink_late_cache.pop((did, gid), None)
        await bot.db.commit()
    e = discord.Embed(title=branded("🗑️ User Wipe Complete"),
                      description=(f"**Target:** {display}\n"
                                   f"Deleted **{deleted_bgc}** BGC record(s) and **{deleted_logs}** check-log row(s).\n"
                                   f"Preemptive records also wiped.\n"
                                   f"External blacklists untouched."),
                      color=T.SUCCESS, timestamp=datetime.now(timezone.utc))
    await interaction.followup.send(embed=e, ephemeral=True)
    await bot_log(gid, embed=discord.Embed(title=branded("🗑️ User Data Wipe"),
                                            description=f"By {interaction.user.mention}\n\n{preview[:1500]}",
                                            color=T.DANGER, timestamp=datetime.now(timezone.utc)))


# ==================== RUN ====================
def _validate_config():
    if not DISCORD_BOT_TOKEN or DISCORD_BOT_TOKEN.startswith("PASTE"):
        logger.error("DISCORD_BOT_TOKEN is required — set it in the CONFIG section.")
        raise SystemExit(1)
    missing = []
    for name, val in [("XTRACKER_API_KEY", XTRACKER_API_KEY),
                      ("RW_API_KEY", RW_API_KEY),
                      ("EW_API_KEY", EW_API_KEY),
                      ("SIMMER_API_KEY", SIMMER_API_KEY)]:
        if not val or val.startswith("PASTE"):
            missing.append(name)
    if BLOXLINK_ENABLED and (not BLOXLINK_API_KEY or BLOXLINK_API_KEY.startswith("PASTE")):
        logger.warning("Bloxlink enabled but no key — falling back to typed usernames only.")
    if missing:
        logger.warning(f"Optional API keys not set (checks will SKIP): {', '.join(missing)}")
    if not BLACKLIST_SHEET_ID:
        logger.info("BLACKLIST_SHEET_ID not set — user/group blacklist checks will return empty.")
    if not SNOW_CORE_SHEET_ID:
        logger.info("SNOW_CORE_SHEET_ID not set — Snow Core checks will return empty.")
    if not EXTERNAL_DATABASES:
        logger.info("EXTERNAL_DATABASES empty — external DB checks will be skipped.")
    if not OWNER_ID:
        logger.info("OWNER_ID not set — /reset disabled, owner DMs disabled.")
    if not AUTO_ROLE_ID:
        logger.info("AUTO_ROLE_ID not set — pass-through autorole disabled, acceptance DM not sent.")
    if not DEFAULT_RECRUITMENT_CHANNEL_ID:
        logger.info("DEFAULT_RECRUITMENT_CHANNEL_ID not set — run /setup or set it in CONFIG.")


def _signal_handler(s, f):
    logger.info(f"Signal {s}")
    try: asyncio.get_event_loop().create_task(bot.close())
    except: pass


if __name__ == "__main__":
    _validate_config()
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    try: bot.run(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt: pass

# ── Made by Pizzarobloxh · github.com/Pizzarobloxh ──
