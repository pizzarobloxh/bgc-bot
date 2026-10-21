# BGC Bot

A Discord bot that screens recruitment applications. It resolves the applicant's Roblox identity, checks it against a set of external ban databases and community watchlists, and either grants a role and sends an acceptance DM or replies with a short, non-specific failure reason.

This repository contains the bot's source and a set of operating documents. By using or deploying this bot you agree to the [Terms of Service](TERMS.md) and [Privacy Policy](PRIVACY.md).

---

## What the bot checks

For each application the bot queries:

- **Roblox** — account info, banned status, account age, groups, username history
- **Bloxlink** — links a Discord account to a Roblox account
- **Xtracker** — shared cheat registry
- **Keystone** — shared case database
- **Simmer** — Roblox Studio activity flags
- **Snow Core** — community punishment list
- **Roblox Watcher** — NSFW/condo Discord server membership
- **Exploit Watcher** — exploit flags (informational, does not fail the applicant)
- **Your own blacklists** — a Google Sheet of banned users and banned Roblox groups
- **External blacklists** — up to six additional community-run Google Sheets

Each source is optional. Missing credentials or unreachable sources cause the corresponding check to be skipped rather than fail the application.

---

## Requirements

- Python 3.10 or newer
- A Discord application with a bot user
- A Discord server where you have Administrator permission
- Optional but recommended: API keys for Bloxlink, Xtracker, Roblox Watcher, Exploit Watcher, Simmer

The bot runs with only a Discord bot token. Every optional key makes a check more accurate; none is strictly required.

---

## Setup

**1. Create the Discord bot**

- Go to https://discord.com/developers/applications → New Application
- Add a Bot user, copy the token
- Under *Bot → Privileged Gateway Intents* enable: Presence, Server Members, Message Content
- Under *OAuth2 → URL Generator* select scopes `bot` and `applications.commands`, and permissions: Manage Roles, Manage Channels, Send Messages, Read Message History, Add Reactions, Embed Links
- Invite the bot with the generated URL

The bot's own role must be positioned **above** the role it will auto-assign.

**2. Get API keys (all optional)**

| Service | Where |
| :--- | :--- |
| Bloxlink | https://blox.link → Server Settings → API |
| Xtracker | https://xtracker.xyz → dashboard |
| Roblox Watcher / Exploit Watcher | https://robloxwatcher.com |
| Simmer | https://simmer.icu |

**3. Configure `bgc_bot.py`**

Edit the CONFIG section at the top of the file. The required values are:

```python
DISCORD_BOT_TOKEN = "..."
```

The strongly recommended values are:

```python
XTRACKER_API_KEY = "..."
RW_API_KEY       = "..."
EW_API_KEY       = "..."
BLOXLINK_API_KEY = "..."
SIMMER_API_KEY   = "..."
```

Server-specific values:

```python
OWNER_ID                       = <your Discord user ID>
AUTO_ROLE_ID                   = <role to assign on pass>
DEFAULT_RECRUITMENT_CHANNEL_ID = <channel to monitor>
```

Optional Google Sheet values (for your own blacklists):

```python
BLACKLIST_SHEET_ID = "..."
GROUP_BLACKLIST_GID = "0"
USER_BLACKLIST_GID  = "..."
SNOW_CORE_SHEET_ID  = "..."
EXTERNAL_DATABASES  = [...]
```

**4. Install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install discord.py aiohttp aiosqlite
pip install aiodns pycares       # optional, non-blocking DNS
```

**5. Run**

```bash
python bgc_bot.py
```

On startup you should see a series of log lines ending with `Setup complete` and `Logged in as ...`. If a bot-log channel is configured, a Bot Online embed appears there.

**6. Configure the server**

In Discord, as an administrator:

```
/setup
```

This creates three channels if they don't exist: `#bgc-pass`, `#bgc-fail`, `#bot-logs`, and configures them. To configure channels manually:

```
/setup pass_log:#my-pass fail_log:#my-fail bot_log_channel:#my-logs recruitment_channel:#applications
```

**7. Post the application format**

Post this in the recruitment channel:

```
**Roblox User:** YourRobloxUsername
**Discord User:** yourdiscordusername
**Clanning Experience:** Yes or No
**Willing to Join:** Yes or No
```

The parser accepts variations of these labels. If labels are missing, it falls back to reading the first four non-empty lines in order.

---

## Commands

| Command | Who can run it | What it does |
| :--- | :--- | :--- |
| `/about` | Everyone | Paginated guide for applicants |
| `/check <target>` | Admin | Run a BGC on a message link, username, mention, or Discord ID |
| `/lookup <target>` | Admin | Read-only lookup, no database writes |
| `/debug` | Admin | Inspect a BGC, list recent, find alts, view stats |
| `/backfill` | Admin | Re-run BGC on historical messages |
| `/setup` | Admin | Configure log channels |
| `/wipeuser <target>` | Admin | Delete local data for one user |
| `/health check` | Admin | Ping all services and refresh caches |
| `/health quick` | Admin | Refresh caches only |
| `/health preemptive <user>` | Admin | Seed a preemptive scan manually |
| `/health timeline <user>` | Admin | Timing probe of a live BGC |
| `/health preemptive_timeline <user>` | Admin | Timing probe of a preemptive-path BGC |
| `/reset` | Owner only | Wipe guild settings (roles are never removed) |

---

## Troubleshooting

**The bot doesn't react to applications.**
Check that the Message Content intent is enabled in the Developer Portal. Check that the recruitment channel is configured with `/setup`.

**Every application fails immediately.**
The applicant's message is missing required fields. Check the bot's reply — it lists which fields are missing.

**The auto-role isn't being assigned.**
Check `/health check` → 🎭 Autorole section. The bot's role must be above the target role, and the bot needs Manage Roles permission.

**`/health check` shows a red source.**
The API key for that source is wrong, or the service is temporarily down. Individual failures don't block other checks.

**The bot seems slow on first application after restart.**
Cache warm-up runs for the first ~10 seconds. Subsequent applications use warm caches.

---

## Documentation

- **[Operating Documents](operating_documents.md)** — architecture, performance measurements, diagrams, implementation history, roadmap
- **[Terms of Service](TERMS.md)** — rules for using the bot
- **[Privacy Policy](PRIVACY.md)** — what data the bot collects and stores

---
