# Privacy Policy

**Project:** Pizzarobloxh's Discord Bots
**Effective Date:** October 19, 2026
**Last Updated:** October 19, 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Information We Collect](#2-information-we-collect)
3. [How We Use the Information](#3-how-we-use-the-information)
4. [Data Retention](#4-data-retention)
5. [Data Security](#5-data-security)
6. [Third-Party Services](#6-third-party-services)
7. [Children's Privacy](#7-childrens-privacy)
8. [Your Rights](#8-your-rights)
9. [Changes to This Policy](#9-changes-to-this-policy)
10. [Contact](#10-contact)

---

## 1. Introduction

This Privacy Policy describes how the **Pizzarobloxh** Discord bots (collectively, "the Bots") collect, use, store, and protect information when you interact with them. By using the Bots, you agree to the practices described in this policy.

We are committed to transparency and to handling your information responsibly. We only collect what is necessary to operate the Bots effectively.

---

## 2. Information We Collect

### 2.1 Discord Data

When you interact with the Bots, we may collect and store:

- **Discord User IDs** — a unique numerical identifier assigned to your Discord account by Discord.
- **Discord usernames** — only when provided by you (e.g., typed into a recruitment application or passed to a command).

We do **not** collect:

- Your email address
- Your IP address
- Your payment or billing information
- Your Discord password, token, or login credentials

### 2.2 Roblox Data

Because the Bots perform background checks ("BGC") against Roblox accounts, we collect and store **public Roblox profile data** associated with a Roblox username or ID you submit:

- **Roblox User ID**
- **Roblox username** (current)
- **Roblox display name**
- **Past Roblox usernames** (via Roblox's public username-history API)
- **Roblox account creation date**
- **Roblox group memberships** (public)

This data is publicly visible on roblox.com and is fetched using Roblox's public APIs. We do **not** collect private Roblox data such as email, password, inventory contents, or transaction history.

### 2.3 Application Content

When you submit a recruitment application in a channel where the Bots are configured to operate, the Bots read the **content of that specific message** to extract:

- Roblox username
- Discord username
- Clanning-experience answer
- X-Tracker self-report answer
- Willing-to-join answer

The extracted fields and the final check results are stored in our database. The **raw message body is not persisted** — only the parsed fields and the outcome of our checks.

### 2.4 Server / Guild Data

We may collect and store data related to the Discord servers ("guilds") in which the Bots operate. This may include:

- **Server (Guild) IDs** — unique numerical identifiers for Discord servers
- **Channel IDs** — to identify specific channels where the Bots are configured to operate
- **Role IDs** — where role-based permissions or features are configured
- **Server configuration settings** — preferences or settings that server administrators configure for the Bots

We do **not** collect or log general message content from server members outside of the recruitment channels the Bots are configured to monitor.

### 2.5 Administrative Bypass

Messages posted by users with **Administrator** or **Manage Server** permissions in a guild are ignored entirely by the Bots — no data is collected, stored, or processed from those messages.

---

## 3. How We Use the Information

The information we collect is used solely to:

- **Provide and operate** the Bots' features (background checks, watchlist lookups, moderation tooling).
- **Cross-reference submitted Roblox identities against screening databases** (see §6) to detect known-bad actors, ban evasion, or multi-account patterns.
- **Store server-specific configurations** set by server administrators.
- **Track usage permissions** and ensure appropriate access control.
- **Enforce our Terms of Service**, including investigating abuse or misuse.
- **Detect multi-account patterns** by comparing historical checks within the same guild.

We do **not** sell, rent, or share your data with third parties for marketing or advertising purposes.

---

## 4. Data Retention

We retain collected data only for as long as necessary to provide the Bots' services:

- **Discord User IDs, Roblox IDs, and check results** are retained as long as they are associated with active Bot functionality (BGC history, multi-account detection).
- **Server/Guild data** is retained for as long as the Bots remain in the server. When the Bots are removed, associated server data may be deleted automatically or upon request.
- **Message-derived fields** (see §2.3) are retained alongside the corresponding BGC record and are removed if that record is deleted.
- **Server administrators** can wipe all BGC history for their server at any time using the Bots' administrative commands.
- **Individual users** may request deletion of their data via the contact in §10.

---

## 5. Data Security

We take reasonable technical measures to protect the data we collect from unauthorized access, loss, or misuse, including:

- Local SQLite storage with WAL mode and normal synchronous settings.
- Bot access restricted to server administrators.
- No external analytics trackers.

However, no system is completely secure, and we cannot guarantee absolute security of the information stored. We encourage server administrators to follow Discord's best practices for server security.

---

## 6. Third-Party Services

The Bots operate within the **Discord platform**, which has its own [Privacy Policy](https://discord.com/privacy) and [Terms of Service](https://discord.com/terms). We are not responsible for Discord's data practices.

To perform screening checks, the Bots send **public Roblox identifiers** (Roblox User ID and/or username) to the following third-party services. Each is governed by its own privacy policy:

| Service | Purpose | Data Sent |
|---|---|---|
| Roblox APIs (`roblox.com`, `roproxy.com`, `rotunnel.com`) | Identity resolution, username history, group membership | Roblox User ID / username |
| Google Sheets (`docs.google.com`) | Read-only lookup of public community blacklist databases | None (read-only fetch) |
| `api.xtracker.xyz` | X-Tracker watchlist lookup | Roblox User ID |
| `api.robloxwatcher.com` | Roblox Watcher watchlist lookup | Discord User ID |
| `api.exploitwatcher.com` | Exploit Watcher watchlist lookup | Discord User ID |
| `api.keystone-swords.com` | Keystone case-registry lookup | Roblox User ID / username |
| `api.simmer.icu` | Simmer RAB (Raid Activity Ban) lookup | Roblox User ID |

We do **not** send your Discord username, email, IP, or any data beyond the identifiers listed above. We do not use any advertising or analytics trackers.

---

## 7. Children's Privacy

The Bots are not directed at children under the age of 13 (or the applicable age in your jurisdiction). We do not knowingly collect data from children. If you believe a child has used the Bots in violation of this policy, please contact us so we can take appropriate action.

---

## 8. Your Rights

Depending on your location, you may have certain rights regarding your data, including:

- **Access** — the right to know what data we hold about you.
- **Deletion** — the right to request deletion of your data.
- **Correction** — the right to request correction of inaccurate data.

To exercise any of these rights, please contact us via the official **Pizzarobloxh** Discord support server (see §10). We will respond to requests within a reasonable timeframe.

Server administrators may also independently wipe guild data using the Bots' administrative commands.

---

## 9. Changes to This Policy

We may update this Privacy Policy from time to time. When we do, we will update the **Effective Date** at the top of this document. Continued use of the Bots after any changes constitutes acceptance of the updated policy. We encourage you to review this policy periodically.

---

## 10. Contact

If you have any questions, concerns, or requests related to this Privacy Policy, please reach out via our official Discord support server for bots:

**https://discord.gg/HW4ArA8rAE**

---

*This Privacy Policy was last updated on October 19, 2026.*
