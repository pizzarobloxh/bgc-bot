# Privacy Policy

**Project:** Pizzarobloxh's Discord Bot  
**Bot:** BGC Bot v4.4.0  
**Developer:** Pizzarobloxh  
**Effective Date:** October 20, 2026  
**Last Updated:** October 20, 2026

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

This Privacy Policy describes how **Pizzarobloxh**'s Discord Bot, **BGC Bot v4.4.0** ("the Bot"), collects, uses, stores, and protects information when you interact with it. By using the Bot, you agree to the practices described in this policy.

This policy covers only the single Discord Bot identified above. It does not cover any other application, service, or bot made by Pizzarobloxh unless expressly stated.

We are committed to transparency and to handling your information responsibly. We only collect what is necessary to operate the Bot effectively.

---

## 2. Information We Collect

### 2.1 Discord Data

When you interact with the Bot, we may collect and store:

- **Discord User IDs** — a unique numerical identifier assigned to your Discord account by Discord.
- **Discord usernames** — when provided by you (for example, typed into a recruitment application or passed to a command), and the username and display name associated with your Discord account when you submit an application.

We do **not** collect:

- Your email address
- Your IP address
- Your payment or billing information
- Your Discord password, token, or login credentials

### 2.2 Roblox Data

Because the Bot performs background checks ("BGC") against Roblox accounts, we collect and store **public Roblox profile data** associated with a Roblox username or ID you submit:

- **Roblox User ID**
- **Roblox username** (current)
- **Roblox display name**
- **Past Roblox usernames** (via Roblox's public username-history API)
- **Roblox account creation date**
- **Roblox group memberships** (public)

This data is publicly visible on roblox.com and is fetched using Roblox's public APIs. We do **not** collect private Roblox data such as email, password, inventory contents, or transaction history.

Where a typed Roblox username resolves to a different account than the one linked through Bloxlink, public profile data for **both** accounts may be retrieved and stored. See [§2.6](#2-6-identity-mismatch-screening).

### 2.3 Application Content

When you submit a recruitment application in a channel where the Bot is configured to operate, the Bot reads the **content of that specific message** to extract:

- Roblox username
- Discord username
- Clanning-experience answer
- X-Tracker self-report answer
- Willing-to-join answer

The extracted fields and the final check results are stored in our database, along with metadata such as the bot version and check-rules version used. The **raw message body is not persisted** — only the parsed fields and the outcome of our checks.

### 2.4 Server / Guild Data

We may collect and store data related to the Discord servers ("guilds") in which the Bot operates. This may include:

- **Server (Guild) IDs** — unique numerical identifiers for Discord servers
- **Channel IDs** — to identify specific channels where the Bot is configured to operate
- **Role IDs** — where role-based permissions or features are configured
- **Server configuration settings** — preferences or settings that server administrators configure for the Bot

We do **not** collect or log general message content from server members outside of the recruitment channels the Bot is configured to monitor.

### 2.5 Administrative Bypass

Messages posted by users with **Administrator** or **Manage Server** permissions in a guild are ignored entirely by the Bot — no data is collected, stored, or processed from those messages.

### 2.6 Identity Mismatch Screening

When you submit a recruitment application, the Bot resolves:

1. the **typed Roblox username** you submitted, and
2. the **Roblox account linked to your Discord account through Bloxlink**.

If these resolve to different Roblox accounts, the Bot screens **both** accounts. This means:

- The typed username's public Roblox profile data (username, display name, past usernames, account creation date, public group memberships) is retrieved and stored.
- The typed username's Roblox User ID is sent to **Xtracker**, **Simmer**, and **Snow Core** for watchlist screening.
- The typed username and its Roblox ID are included in **Keystone** and **external blacklist** searches.

This dual screening is performed to detect identity mismatches and attempted evasion. It means that a mistyped username could result in screening of an unrelated Roblox account. You are responsible for ensuring the accuracy of any username you submit.

---

## 3. How We Use the Information

The information we collect is used solely to:

- **Provide and operate** the Bot's features, including background checks, watchlist lookups, and moderation tooling.
- **Cross-reference submitted Roblox identities against screening databases** (see [§6](#6-third-party-services)) to detect known-bad actors, ban evasion, or multi-account patterns.
- **Screen both the typed and Bloxlink-linked Roblox identities when they differ**, to detect identity mismatches and attempted evasion.
- **Store server-specific configurations** set by server administrators.
- **Track usage permissions** and ensure appropriate access control.
- **Enforce our Terms of Service**, including investigating abuse or misuse.
- **Detect multi-account patterns and identity mismatches** by comparing historical checks within the same guild and by screening both typed and Bloxlink-linked identities when they differ.

We do **not** sell, rent, or share your data with third parties for marketing or advertising purposes.

---

## 4. Data Retention

We retain collected data only for as long as necessary to provide the Bot's services:

- **Discord User IDs, Roblox IDs, and check results** are retained as long as they are associated with active Bot functionality, including BGC history and multi-account detection.
- **Server/Guild data** is retained for as long as the Bot remains in the server. When the Bot is removed, associated server data may be deleted automatically or upon request.
- **Message-derived fields** (see [§2.3](#2-3-application-content)) are retained alongside the corresponding BGC record and are removed if that record is deleted.
- **Diagnostic logs** containing operational metadata may be retained locally for troubleshooting and are rotated automatically.
- **Server administrators** can wipe all BGC history for their server at any time using the Bot's administrative commands.
- **Individual users** may request deletion of their data via the contact in [§10](#10-contact).

---

## 5. Data Security

We take reasonable technical measures to protect the data we collect from unauthorized access, loss, or misuse, including:

- Local SQLite storage with WAL mode and normal synchronous settings.
- Bot access restricted to server administrators.
- Local diagnostic logs use rotating file handlers with size limits.
- No external analytics trackers.

However, no system is completely secure, and we cannot guarantee absolute security of the information stored. We encourage server administrators to follow Discord's best practices for server security.

---

## 6. Third-Party Services

The Bot operates within the **Discord platform**, which has its own [Privacy Policy](https://discord.com/privacy) and [Terms of Service](https://discord.com/terms). We are not responsible for Discord's data practices.

To perform screening checks, the Bot sends **public Roblox identifiers** (Roblox User ID and/or username) to the following third-party services. Each is governed by its own privacy policy:

| Service | Purpose | Data Sent |
|---|---|---|
| Roblox APIs (`roblox.com`, `roproxy.com`, `rotunnel.com`) | Identity resolution, username history, group membership | Roblox User ID / username |
| Bloxlink (`api.blox.link`) | Discord ↔ Roblox account linking | Discord User ID, Guild ID |
| Google Sheets (`docs.google.com`) | Read-only lookup of public community blacklist databases, including Snow Core | None (read-only fetch) |
| `api.xtracker.xyz` | Xtracker watchlist lookup | Roblox User ID |
| `api.robloxwatcher.com` (Roblox Watcher) | Roblox Watcher watchlist lookup | Discord User ID |
| `api.robloxwatcher.com` (Exploit Watcher product) | Exploit Watcher watchlist lookup | Discord User ID |
| `api.keystone-swords.com` | Keystone case-registry lookup | Roblox User ID / username |
| `api.simmer.icu` | Simmer RAB (Raid Activity Ban) lookup | Roblox User ID |

**Dual-identity screening.** When a typed Roblox username and a Bloxlink-linked account differ, the typed account's Roblox User ID may also be sent to Xtracker, Simmer, and Snow Core (via Google Sheets) for screening.

**Reduced historical queries.** For historical Roblox IDs beyond the most recent historical identity, Xtracker ownership checks are not performed; only registry checks are performed. This reduces third-party queries for historical identities.

**Diagnostic commands.** The Bot owner has access to diagnostic commands, such as `/health check` and `/health timeline`, that run screening checks on configured test identifiers or identifiers specified by the owner. The `/health timeline` command does not read stored user history and does not write to the database. These commands are not available to regular users.

We do **not** send your Discord username, email, IP address, or any data beyond the identifiers listed above. We do not use any advertising or analytics trackers.

---

## 7. Children's Privacy

The Bot is not directed at children under the age of 13, or the applicable age in your jurisdiction. We do not knowingly collect data from children. If you believe a child has used the Bot in violation of this policy, please contact us so we can take appropriate action.

---

## 8. Your Rights

Depending on your location, you may have certain rights regarding your data, including:

- **Access** — the right to know what data we hold about you.
- **Deletion** — the right to request deletion of your data.
- **Correction** — the right to request correction of inaccurate data.

To exercise any of these rights, please contact us via the official **Pizzarobloxh** Discord support server (see [§10](#10-contact)). We will respond to requests within a reasonable timeframe.

Server administrators may also independently wipe guild data using the Bot's administrative commands, including the `/wipeuser` command for deleting local BGC data about a specific user.

---

## 9. Changes to This Policy

We may update this Privacy Policy from time to time. When we do, we will update the **Effective Date** at the top of this document. Continued use of the Bot after any changes constitutes acceptance of the updated policy. We encourage you to review this policy periodically.

---

## 10. Contact

If you have any questions, concerns, or requests related to this Privacy Policy, please reach out via our official Discord support server for the Bot:

**https://discord.gg/HW4ArA8rAE**

---

*This Privacy Policy was last updated on October 20, 2026.*
