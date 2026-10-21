# Privacy Policy

**Last updated:** [21/10/2026]

This Privacy Policy explains what data the BGC Bot ("the Bot") collects, why, how long it is kept, and who it is shared with.

The Bot is operated by the person or group that deployed it ("the Operator"). In most cases the Operator is not the same person as the maintainer of the source code. If you have questions, contact the Operator through the server where the Bot runs.

---

## 1. Data the Bot collects

The Bot processes data at three points: when you type in the recruitment channel, when you submit an application, and when you interact with its commands.

### When you type in the recruitment channel

The Bot runs a background identity scan the moment you start typing. It collects:

- Your Discord user ID and username
- Your Discord nickname (if set)
- The Discord account creation date (derived from your ID)
- The Roblox ID linked to your Discord account via Bloxlink (if any)
- Your Roblox profile info: username, display name, account creation date, banned status
- Your Roblox username history
- Your Roblox group memberships
- Xtracker registry and ownership results for each of your known Roblox IDs
- Simmer RAB result

These are stored in a `preemptive_scans` database table so that a submission can be checked quickly.

### When you submit an application

The Bot reads the content of your message in the recruitment channel and parses:

- The Roblox username you typed
- The Discord username you typed
- Your answers to "Clanning Experience" and "Willing to Join"

The full message text is not stored verbatim. Only the parsed fields are kept.

The Bot then queries the same sources as above plus:

- Your own blacklists (users and groups)
- Keystone cases
- Snow Core bans
- Six external community blacklists
- Roblox Watcher flags
- Exploit Watcher flags

Results are stored in a `bgc_checks` table with per-check details in a `check_logs` table.

### When you interact with commands

Command usage records: the interaction user's Discord ID, the command name, and — for `/check`, `/lookup`, `/wipeuser`, `/health preemptive`, `/health timeline` — the target identity.

### Always

The Bot stores basic logging data on its own host: timestamps, HTTP status codes for external services, and error messages. These logs may contain Discord IDs, Roblox IDs, and usernames.

---

## 2. Why the Bot collects this data

- **To perform the requested checks.** The Bot cannot decide whether an application passes without knowing who applied.
- **To remember previous decisions.** Multi-account detection requires knowing which Discord IDs have previously been associated with which Roblox IDs.
- **To speed up repeat applications.** The preemptive scan runs ahead of your submission so that the actual check is faster.
- **To let moderators audit decisions.** Moderators can use `/debug` to see why an application passed or failed.

---

## 3. Third parties the Bot contacts

Performing a check requires sending your data to these services:

| Service | What is sent | What is received |
| :--- | :--- | :--- |
| Roblox (via `users.rotunnel.com`, `users.roproxy.com`, `users.roblox.com`, and the `groups` equivalents) | Username, Roblox ID | Profile, groups, history, banned status |
| Bloxlink (`api.blox.link`) | Discord ID, server ID | Linked Roblox ID |
| Xtracker (`api.xtracker.xyz`) | Roblox ID | Registry and ownership results |
| Keystone (`api.keystone-swords.com`) | Your Roblox IDs and usernames (in the query) | Full case list (filtered locally) |
| Simmer (`api.simmer.icu`) | Roblox ID | RAB result |
| Snow Core (Google Sheets via `docs.google.com`) | Nothing (full sheet downloaded) | Ban list |
| Roblox Watcher (`api.robloxwatcher.com`) | Discord ID | Flag result |
| Exploit Watcher (`api.robloxwatcher.com`) | Discord ID | Flag result |
| Google Sheets (each external blacklist) | Nothing (full sheet downloaded) | Ban list |

The Bot sends the minimum data required for each query. It does not send your full Discord message content, your application answers, or your chat history to any third party.

Each of these services has its own privacy policy. You are subject to their policies when the Bot queries them on your behalf. The Operator does not control what these services do with the data after they receive it.

---

## 4. How long data is kept

| Data | Retention |
| :--- | :--- |
| `bgc_checks` (applications and their results) | Indefinite — until deleted via `/wipeuser` or `/reset clear_history:True` |
| `check_logs` (per-check details) | Same as `bgc_checks` |
| `guild_settings` (server configuration) | Indefinite |
| `preemptive_scans` (background scan cache) | Automatically deleted once both identity and freshness scans are more than 30 days old |
| In-memory caches (Roblox profile, groups, history, Simmer) | 10 minutes to 30 minutes |
| In-memory caches (Bloxlink resolution) | 30 minutes |
| Guild log channel cache | 60 seconds |
| Race winner logs | 10 minutes |
| Server-side logs | Rotation: 10 MB per file, 5 files maximum |

Deleting your data via `/wipeuser` removes your records from `bgc_checks`, `check_logs`, and `preemptive_scans`. It does not affect any external service — those services have their own retention policies.

---

## 5. Your rights

You have the following rights, subject to the Operator's verification that you are the person the data relates to:

- **Access** — you may ask the Operator what data is stored about you
- **Deletion** — you may ask the Operator to delete your local data using `/wipeuser`
- **Correction** — you may ask the Operator to correct inaccurate data
- **Portability** — you may ask the Operator for a copy of your stored data

Requests should be made through the server's moderators. External database operators must be contacted separately — the Operator cannot delete data from third-party services.

---

## 6. Children

The Bot is not directed at children. If you are under the age required by Discord's Terms of Service, you may not use the Bot. If the Operator becomes aware that data has been collected from a child under the applicable age, the Operator will delete it.

---

## 7. Security

The Bot stores data in a SQLite database on the Operator's host. The Operator takes reasonable steps to protect this database, but no system is perfectly secure. The Bot has no access controls beyond what the operating system provides.

The bot token and API keys used by the Bot are stored in the source file and should be treated as sensitive. If a key is exposed, contact the Operator.

---

## 8. International data transfers

The Bot runs on a server whose location is chosen by the Operator. External services that the Bot queries may be located anywhere in the world. By using the Bot you consent to your data being transferred to wherever the Operator's host and the third-party services are located.

---

## 9. Changes

The Operator may update this Privacy Policy at any time. Updates take effect when posted. Continued use of the Bot after an update means you accept the updated policy.

If a change materially affects how data is used, the Operator will make reasonable efforts to notify users — for example by posting in the bot-log channel.

---

## 10. Contact

Questions or requests should be directed to the Operator through the server where the Bot runs, or through the source repository.

---

## Summary

To make an informed decision about using the Bot:

- If you type in the recruitment channel, the Bot will scan your identity in the background
- If you submit an application, the Bot will store the result permanently unless you ask for it to be deleted
- Your Discord ID and Roblox ID are sent to several external services
- You can request deletion via `/wipeuser` through server staff
- External databases have their own retention which the Bot cannot control

By using the Bot you confirm you have read this policy and understand what data is collected.
