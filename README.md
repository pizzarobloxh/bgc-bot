<div align="center">

# 🛡️ BGC Bot

### Discord recruitment background checker — sub-100ms with preemptive scanning

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://github.com/Rapptz/discord.py)
[![Version](https://img.shields.io/badge/v5.0.0-8b5cf6?style=for-the-badge)](https://github.com/Pizzarobloxh/bgc-bot)
[![Preemptive](https://img.shields.io/badge/preemptive-65ms-22c55e?style=for-the-badge)](https://github.com/Pizzarobloxh/bgc-bot)

</div>

---

## What this is

A self-hosted Discord bot that automatically screens recruitment applications. When a user posts in your recruitment channel, the bot:

1. Parses their Roblox username, Discord username, and clanning answers
2. Resolves their Roblox identity via Bloxlink, typed username, Discord nickname, or DB history
3. Runs 20+ checks in parallel against Xtracker, Keystone, Simmer, Snow Core, Roblox Watcher, Exploit Watcher, your private blacklist, and up to 6 external clan lists
4. Reacts with `✅` (pass) or `❌` (fail)
5. On pass: auto-roles them and DMs acceptance instructions
6. On fail: replies with a generic, sanitised reason

**The killer feature:** if the user spent more than ~3 seconds typing their application, all the expensive lookups already happened in the background. The actual check returns in **65ms**.

> **Technical deep dive** → see [`OPERATING_DOCUMENTS.md`](OPERATING_DOCUMENTS.md) for every measured number, diagram, and war story from the current build.

---

## What you need

| Requirement | Notes |
| :--- | :--- |
| **Python 3.10+** | [python.org/downloads](https://www.python.org/downloads/) |
| **Discord Bot Token** | From [discord.com/developers](https://discord.com/developers/applications) |
| **A Discord server you administer** | You need **Administrator** permission |
| **A recruitment channel** | Somewhere users can post applications |

**Optional but strongly recommended:**

| Service | What it does | Get it at |
| :--- | :--- | :--- |
| **Bloxlink** | Resolves Discord → Roblox ID | [blox.link](https://blox.link) |
| **Xtracker** | Shared cheater database | [xtracker.xyz](https://xtracker.xyz) |
| **Roblox Watcher** | NSFW-server membership check | [robloxwatcher.com](https://robloxwatcher.com) |
| **Exploit Watcher** | Informational exploit flag | [robloxwatcher.com](https://robloxwatcher.com) |
| **Simmer** | RAB (Roblox Studio) check | [simmer.icu](https://simmer.icu) |

**Missing keys do NOT crash the bot** — every check that can't run simply returns `SKIPPED`.

---

## Step 1 — Create your Discord bot

1. Go to **[discord.com/developers/applications](https://discord.com/developers/applications)**
2. Click **New Application** → name it (e.g. `BGC Bot`) → **Create**
3. Left sidebar → **Bot** → **Add Bot** → confirm
4. Under **Token** → **Reset Token** → **Copy** → save it somewhere safe (you'll never see it again)
5. Scroll down to **Privileged Gateway Intents** and enable **all three**:
   - ✅ Presence Intent
   - ✅ **Server Members Intent** ← required
   - ✅ **Message Content Intent** ← required
6. Left sidebar → **OAuth2** → **URL Generator**
7. Scopes: check ✅ **bot** and ✅ **applications.commands**
8. Bot Permissions, check:
   - ✅ Manage Roles
   - ✅ Manage Channels
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Add Reactions
   - ✅ Embed Links
   - ✅ Attach Files
9. Copy the generated URL at the bottom, open it in your browser, and invite the bot to your server

> **Bot role position matters.** The bot's own role must be **above** the role it will auto-assign. Server Settings → Roles → drag the bot's role above the recruitment role.

---

## Step 2 — Get your API keys (optional)

Skip any of these and the corresponding check just returns `SKIPPED`.

### Bloxlink (strongly recommended)

1. Go to [blox.link](https://blox.link) → log in with Discord
2. Select your server → **Server Settings** → **API**
3. Copy the **server API key**
4. Also install the Bloxlink bot itself in your server so users can actually link their Roblox

### Xtracker (strongly recommended)

1. Go to [xtracker.xyz](https://xtracker.xyz) → register / log in
2. Navigate to your API dashboard → copy your **API key**

### Roblox Watcher + Exploit Watcher

1. Go to [robloxwatcher.com](https://robloxwatcher.com) → register
2. Two keys are issued: one prefixed `RW_` (Roblox Watcher), one prefixed `EW_` (Exploit Watcher)
3. Copy both

### Simmer

1. Go to [simmer.icu](https://simmer.icu) → register / log in
2. Copy your API key from the dashboard

---

## Step 3 — Configure the bot

Open `bgc_bot.py` and edit the **CONFIG** section near the top. Everything you need to change is in the first ~90 lines.

### Required

```python
DISCORD_BOT_TOKEN = "your-bot-token-here"
```

### Strongly recommended

```python
XTRACKER_API_KEY  = "your-xtracker-key"
RW_API_KEY        = "RW_your-robloxwatcher-key"
EW_API_KEY        = "EW_your-exploitwatcher-key"
BLOXLINK_API_KEY  = "your-bloxlink-server-key"
SIMMER_API_KEY    = "your-simmer-key"
```

### Your server's IDs

Enable Discord **Developer Mode** first (User Settings → Advanced → Developer Mode), then right-click any channel/role/user → **Copy ID**.

```python
OWNER_ID                       = 0  # your Discord user ID (right-click yourself)
AUTO_ROLE_ID                   = 0  # role to assign on pass
DEFAULT_RECRUITMENT_CHANNEL_ID = 0  # channel for applications
```

### Branding (optional)

```python
BRAND_NAME       = "Your Server Name"
BRAND_GROUP_URL  = "https://www.roblox.com/communities/YOUR_GROUP_ID"
LOGO_EMOJI       = "<:LOGO:YOUR_EMOJI_ID>"  # optional
```

### Blacklists (optional)

If you have a Google Sheet of banned users/groups:

```python
BLACKLIST_SHEET_ID  = "the-long-string-from-your-sheet-url"
GROUP_BLACKLIST_GID = "0"           # the tab's gid, or "0" for first tab
USER_BLACKLIST_GID  = "123456789"   # the tab's gid
SNOW_CORE_SHEET_ID  = ""            # optional
SNOW_CORE_GID       = "0"
```

To find a Google Sheet's `gid`: open the sheet, look at the URL. The `#gid=NNNNN` at the end is the tab ID.

### External clan blacklists (optional)

```python
EXTERNAL_DATABASES = [
    {
        "key": "my_alliance",
        "sheet_id": "1aBcDeFg...",
        "gid": "0",
        "name": "My Alliance Blacklist",
    },
    # add up to 6
]
```

Each entry searches one external Google Sheet for the applicant's ID, username, and Discord tag.

---

## Step 4 — Install and run

### Install dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# Core deps
pip install discord.py aiohttp aiosqlite

# Optional — makes DNS non-blocking
pip install aiodns pycares
```

### Run the bot

```bash
python bgc_bot.py
```

**First-run checklist** — you should see in the console:

```text
[INFO] bgc: aiodns installed — aiohttp will use it for non-blocking DNS
[INFO] bgc: DNS pre-resolve complete
[INFO] bgc: Setup complete (aiodns=on)
[INFO] bgc: Logged in as BGC Bot#1234 (1234567890)
[INFO] bgc: Cache pre-warm starting
[INFO] bgc: Cache pre-warm complete in 2103ms
```

If **Bot Online** appeared in your bot-log channel, you're live.

---

## Step 5 — Set up your server

In Discord, as an administrator:

```text
/setup
```

With **no parameters**, the bot auto-creates three private channels:

| Channel | Purpose |
| :--- | :--- |
| `#bgc-pass` | Full embed for every passing application |
| `#bgc-fail` | Full embed for every failing application |
| `#bot-logs` | Health events, errors, preemptive scan activity |

**Or configure channels manually:**

```text
/setup pass_log:#my-pass-channel fail_log:#my-fail-channel bot_log_channel:#my-logs recruitment_channel:#applications
```

---

## Step 6 — Publish the application format

Post this in your recruitment channel so applicants know what to write:

```text
**Roblox User:** YourRobloxUsername
**Discord User:** yourdiscordusername
**Clanning Experience:** Yes or No
**Willing to Join:** Yes or No
```

The bot accepts many variations — it looks for the labels `roblox user`, `discord user`, `clanning experience`, `willing to join`. It even falls back to bare-line parsing if labels are missing.

> **Important:** Tell users **not to edit** their posted application. Edited messages are ignored to prevent bypasses.

---

## Step 7 — Test it

```text
/health check
```

You'll get a full diagnostic:

- All Roblox API mirrors status
- All blacklist sources (row counts + response times)
- All watchlists (Xtracker, Simmer, Roblox Watcher, Exploit Watcher, Bloxlink)
- Auto-role readiness
- Preemptive cache stats
- Bot version + AIODNS status + Xtracker limiter state

All green = you're ready.

**Then post a test application yourself** and watch the bot react.

---

## Commands reference

### For everyone

| Command | Description |
| :--- | :--- |
| `/about` | Paginated guide for applicants: what's checked and why a check fails |

### For admins

| Command | Description |
| :--- | :--- |
| `/check <target>` | Run a BGC on a message link, Roblox username, @mention, or Discord ID |
| `/lookup <target>` | Full read-only lookup (no DB writes, no role changes) |
| `/debug <options>` | Inspect a BGC, list recent, find alts, view stats |
| `/backfill` | Re-run BGC on historical recruitment messages |
| `/setup` | Reconfigure log channels |
| `/wipeuser <target>` | Delete all local BGC data about one user |
| `/health check` | Full system health check |
| `/health quick` | Just refresh caches (fast) |
| `/health preemptive <user>` | Manually seed a preemptive scan for a user |
| `/health timeline <user>` | Live-path timing probe (bypasses preemptive) |
| `/health preemptive_timeline <user>` | Fast-path timing probe (uses preemptive) |

### Owner only

| Command | Description |
| :--- | :--- |
| `/reset` | Wipe guild settings (roles are never removed) |

---

## Daily operations

**You don't need to do anything.** The bot runs itself:

- **Every message** in the recruitment channel is checked automatically
- **Preemptive scans** fire the moment a user starts typing — before they post
- **Caches auto-refresh** every 30 minutes in the background
- **Health events** log to `#bot-logs` automatically
- **Errors** go to your DMs if `OWNER_ID` is set

**Manual tasks you might want to do:**

| When | Do this |
| :--- | :--- |
| Something looks off | `/health check` |
| Suspect a user has alts | `/debug alts:True` |
| New external blacklist to add | Edit `EXTERNAL_DATABASES` in config, restart |
| Role missing on passers | `/health check` → look at 🎭 Autorole section |
| User wants their data removed | `/wipeuser @user` |

---

## Troubleshooting

| Problem | Cause | Fix |
| :--- | :--- | :--- |
| Bot doesn't react at all | `Message Content Intent` disabled | Developer Portal → Bot → enable it → restart |
| Bot reacts `❌` immediately | Format missing fields | Check the applicant's message — needs 4 fields |
| `/health check` shows 🔴 for a source | API key wrong or service down | Check the key; test the source manually |
| Auto-role not being applied | Role hierarchy issue | Bot's role must be **above** `AUTO_ROLE_ID` |
| Auto-role not being applied (2) | Missing permission | Bot needs **Manage Roles** |
| Acceptance DM not delivered | User has DMs off | Normal — the bot logs "DMs closed/blocked" |
| `/reset` says "Owner only" | `OWNER_ID` is 0 or wrong | Set it to **your** Discord user ID |
| All checks `SKIPPED` | No API keys set | At least set `XTRACKER_API_KEY` |
| Preemptive never hits | Users type fast (<3s) | Normal — falls back to live path |
| Bot spam-scans users | `on_typing` fires per-channel | By design — one scan per user per channel |
| Slow first BGC after restart | Cold caches | Wait 30s for keep-warm to finish |

### Still stuck?

```text
/health check
```

Copy the entire embed and look for any 🔴 lines. That's usually where the problem is. If everything is 🟢 but the bot still isn't working:

1. Check the terminal output for errors
2. Confirm `bot.py` is the one you're running (not an old copy)
3. Confirm the bot is actually in your server and has **all** required permissions

---

## FAQ

**Q: Does the bot work without Bloxlink?**
Yes. It falls back to the typed username and the user's Discord nickname. Bloxlink just makes the identity resolution more accurate when the typed username is wrong.

**Q: What if a user has no Roblox account at all?**
The bot resolves the Discord-only path — checks are limited to user blacklist, Discord age, watchers, and external DBs. Roblox-specific checks return `SKIPPED`.

**Q: How does the preemptive scanner work?**
The `on_typing` event fires the moment a user starts typing in the recruitment channel. The bot runs the expensive lookups in the background (hidden from the user) and stores the result. When the user actually posts, the BGC reads from cache.

**Q: Will the bot detect alts?**
Yes — `MultiAccount` check compares the current application against historical DB records. Enable failure with `MULTI_ACCOUNT_FAIL = True` (default is `False` — informational only).

**Q: Can I run this on multiple servers?**
Yes — the bot is per-guild. Each server configures its own channels via `/setup`. The database is shared across guilds but scoped per-guild for queries.

**Q: Where is the data stored?**
Local SQLite file `bgc.db` next to `bgc_bot.py`. Tables:
- `bgc_checks` — every completed BGC
- `check_logs` — per-check details for each BGC
- `guild_settings` — per-guild channel config
- `preemptive_scans` — cached identities + checks

**Q: How do I update the bot?**
Pull the new `bgc_bot.py`, restart. The DB schema migrates automatically on startup.

**Q: Is there a rate limit on Xtracker?**
Yes — the adaptive limiter starts at 1.0s between calls. On 429 responses it doubles the interval (max 4x). After 60s of silence it decays back. You should never see a rate-limited `SKIPPED` in production.

**Q: What if I want to see the full check results for a user?**
```text
/debug latest_for:@username
```
Shows every check with its status, details, and a re-run button.

**Q: Does the bot log private user data anywhere external?**
No. Every lookup is HTTP → response → store in `bgc.db`. No telemetry, no external analytics, no message bodies sent anywhere except the recruitment channel it's in.

---

## Next steps

- **See every measured number** → [`OPERATING_DOCUMENTS.md`](operating_documents.md)
- **War stories** → [`OPERATING_DOCUMENTS.md#war-stories`](operating_documents.md#war-stories)
- **Architecture diagrams** → [`OPERATING_DOCUMENTS.md#architecture`](operating_documents.md#architecture)
- **Performance comparison** → [`OPERATING_DOCUMENTS.md#version-history`](operating_documents.md#version-history)
- **Roadmap** → [`OPERATING_DOCUMENTS.md#roadmap`](operating_documents.md#roadmap)

<div align="center">

**Built by [Pizzarobloxh](https://github.com/Pizzarobloxh) — for communities that take recruitment seriously.**

</div>
