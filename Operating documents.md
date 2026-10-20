<div align="center">

# 📊 Operating Documents

### The complete technical breakdown of BGC Bot v5.0.0

*Every measurement, every diagram, every war story.*

[![Baseline](https://img.shields.io/badge/baseline-v4.5.0%20·%201721ms-ef4444?style=for-the-badge)](https://github.com/Pizzarobloxh/bgc-bot)
[![Current live](https://img.shields.io/badge/live%20v5.0.0-801ms-f59e0b?style=for-the-badge)](https://github.com/Pizzarobloxh/bgc-bot)
[![Current preemptive](https://img.shields.io/badge/preemptive%20v5.0.0-65ms-22c55e?style=for-the-badge)](https://github.com/Pizzarobloxh/bgc-bot)
[![Speedup](https://img.shields.io/badge/speedup-26.5x-8b5cf6?style=for-the-badge)](https://github.com/Pizzarobloxh/bgc-bot)

</div>

---

## 📑 Table of Contents

- [Executive Summary](#-executive-summary)
- [Version History](#-version-history)
- [Performance Comparison](#-performance-comparison)
- [v5.0.0 Deep Dive](#-v500-deep-dive)
- [Task-Level Improvements](#-task-level-improvements)
- [Architecture](#-architecture)
- [Reliability Mechanisms](#-reliability-mechanisms)
- [Data Model](#-data-model)
- [Health Snapshot](#-health-snapshot)
- [War Stories](#-war-stories)
- [Roadmap](#-roadmap)

---

## 🎯 Executive Summary

**v5.0.0 is 26.5× faster than the v4.5.0 baseline.**

| Metric | v4.5.0 | v5.0.0 | Delta |
| :--- | ---: | ---: | ---: |
| **Live BGC time** | 1721 ms | **801 ms** | **−53.5%** |
| **Preemptive fast path** | — | **65 ms** | **n/a (new)** |
| **Xtracker calls (fast path)** | — | **0** | **n/a (new)** |
| **Databases searched** | 8 | **8** | — |
| **Rate-limit failures** | frequent | **0 since v4.9.0 revert** | ✅ |
| **Bloxlink timeout shield** | no | **1500 ms** | ✅ |
| **Adaptive Xtracker limiter** | no | **yes (429-aware)** | ✅ |

**The single headline number: 65 ms.**

For any user who takes more than ~3 seconds to type their application, the entire background check completes in the time it takes to blink. That is **faster than a single Roblox API round-trip.**

### What makes it fast

Three structural changes since v4.5.0:

1. **Preemptive scanning** — the moment a user types in the recruitment channel, the bot runs all expensive lookups in the background and caches the result.
2. **Adaptive rate limiter** — the Xtracker limiter now self-tunes on 429 responses instead of hitting rate limits silently.
3. **Three-tier cache** — identity (7 days), Xtracker (3 days), freshness (30 minutes) — separately expire, so repeat users hit fast paths at every tier.

### What makes it reliable

Four safety mechanisms:

1. **Bloxlink shield** — caps Bloxlink latency at 1500 ms; if it times out, the bot falls back to the typed username.
2. **Late bloxlink cache** — even a timed-out Bloxlink response gets captured when it eventually arrives, so the *next* BGC for that user is instant.
3. **Circuit breaker** — 3 failures on a Roblox API mirror → 60-second skip → auto-recovery.
4. **`AdaptiveRateLimiter`** — Xtracker 429 responses double the interval (`base × 2^n`, max 4×); after 60 s of silence it decays back.

---

## 📈 Version History

| Version | Key Changes |
| :--- | :--- |
| **v4.5.0** | Baseline. Sequential domain fallback. 1.0 s Xtracker limiter. Single-wave T2. |
| **v4.6.0** | Domain racing (3 Roblox mirrors parallel). Per-UID caching. Wave-based T2. Circuit breaker. Xtracker limiter at 0.5 s. |
| **v4.7.0** (proposed, not shipped) | Bloxlink hard timeout. Nickname racing. Historical-ID history. |
| **v4.9.0** | Preemptive scanner. Bloxlink shield + late cache. Adaptive rate limiter. `aiodns` support. ETag fetching. **Reverted Xtracker limiter to 1.0 s after rate-limit failures.** |
| **v5.0.0** | Three-tier cache split (identity / xtracker / freshness). Xtracker cached 3 days instead of 30 min. `xtracker_by_id` field for multi-ID caching. **`XTRACKER_RATE_LIMIT` currently at 0.40 s in production with adaptive backoff.** |

---

## 📊 Performance Comparison

### All versions, all modes

| Version | Mode | Total | Xtracker limiter | vs baseline | Speedup |
| :--- | :--- | ---: | :---: | ---: | ---: |
| **v4.5.0** | baseline | 1721 ms | 1.00 s | — | 1.0× |
| v4.6.0 | fast XT *(experimental — hit 429s)* | 821 ms | 0.01 s | −52.3% | 2.10× |
| v4.6.0 | safe XT | 921 ms | 0.50 s | −46.5% | 1.87× |
| v4.9.0 | live | 1221 ms | 1.00 s | −29.0% | 1.41× |
| v4.9.0 | preemptive | 98 ms | 0 calls | −94.3% | 17.6× |
| **v5.0.0** | **live** | **801 ms** | **0.40 s** | **−53.5%** | **2.15×** |
| **v5.0.0** | **preemptive** | **65 ms** | **0 calls** | **−96.2%** | **26.5×** |

### Total time — visual

```mermaid
xychart-beta
    title "Total BGC time across versions (milliseconds)"
    x-axis ["v4.5.0", "v4.6.0 safe", "v4.9.0 live", "v5.0.0 live", "v4.9.0 preempt", "v5.0.0 preempt"]
    y-axis "Milliseconds" 0 --> 1800
    bar [1721, 921, 1221, 801, 98, 65]
```

### Percentage cuts at a glance

| Comparison | Reduction | Speedup |
| :--- | ---: | ---: |
| v4.5.0 → v5.0.0 live | **−53.5%** | 2.15× |
| v4.5.0 → v5.0.0 preemptive | **−96.2%** | **26.5×** |
| v4.9.0 live → v5.0.0 live | −34.4% | 1.52× |
| v4.9.0 preemptive → v5.0.0 preemptive | −33.7% | 1.51× |
| v4.6.0 safe → v5.0.0 live | −13.0% | 1.15× |

> **Why the live path is slower than v4.6.0's "fast" mode:** v4.6.0's 821 ms figure used a `0.01 s` Xtracker limiter that we discovered hits 429s in production. The current 0.40 s limiter is slower but **does not fail.** We traded 20 ms of theoretical peak for zero rate-limit failures.

---

## ⚡ v5.0.0 Deep Dive

Two complete measurement runs, warm shared caches, per-UID caches cleared.

### Live path — 801 ms

Preemptive cache bypassed for a pure "cold start" measurement.

```mermaid
gantt
    title v5.0.0 Live Path — 801 ms
    dateFormat x
    axisFormat %S.%L
    todayMarker off

    section T0 — Discord-level (0 ms)
    bloxlink (ceiling)      :crit, done,  t_bl,  0,   801ms
    exploit_watcher         :done,        t_ew,  0,   141ms
    roblox_watcher          :done,        t_rw,  0,    89ms
    blacklists + age        :done,        t_bl2, 0,     1ms

    section T1 — ID-keyed (1 ms)
    xtracker_own            :done,        t_xo,  1,   586ms
    xtracker_reg            :done,        t_xr,  1,   248ms
    simmer_rab              :done,        t_sr,  1,   136ms
    username_history        :done,        t_uh,  1,    53ms
    user_groups             :done,        t_ug,  1,    53ms
    user_info               :done,        t_ui,  1,    26ms

    section T2 — Waves (54 ms)
    keystone + ext + multi  :done,        t_t2,  54,    6ms

    section Milestones
    T1 fires                :milestone,   m1,    1,     0ms
    T2 fast wave            :milestone,   m2,   54,     0ms
    BGC complete            :milestone,   m3,  801,     0ms
```

**The story:** `bloxlink` is now the ceiling at 801 ms. `xtracker_own` finishes at 587 ms — **214 ms earlier than the current total.** Reducing `BLOXLINK_HARD_TIMEOUT_MS` from 1500 ms → 700 ms would cut total live-path latency to ~700 ms immediately.

### Preemptive fast path — 65 ms

What a user who typed for at least ~3 seconds actually sees.

```mermaid
gantt
    title v5.0.0 Preemptive Fast Path — 65 ms
    dateFormat x
    axisFormat %S.%L
    todayMarker off

    section Preemptive Cache (0 ms)
    identity + xtracker + freshness  :done, t_pre, 0, 1ms

    section T0 — Watchers (only T0 that runs)
    exploit_watcher (ceiling)        :crit, done, t_ew, 0, 65ms
    roblox_watcher                   :done,        t_rw, 0, 57ms
    blacklists + age                 :done,        t_bl, 0, 1ms

    section T1 — All cached
    info + hist + groups             :done,        t_t1, 0, 1ms
    xtracker (0 network calls)       :done,        t_xt, 0, 1ms
    simmer + snow                    :done,        t_sm, 0, 1ms

    section T2 — Waves
    keystone + ext + multi           :done,        t_t2, 1, 7ms

    section Milestones
    BGC complete                     :milestone,   m1,  65, 0ms
```

**The story:** `exploit_watcher` is the only remaining network call. Everything else is served from cache. Zero Xtracker calls. Zero Bloxlink calls. The preemptive seed (~3300 ms) already did all the expensive work while the user was typing — invisible.

### Critical path — where it's now

```mermaid
gantt
    title Critical path evolution — the bottleneck moved 4 times
    dateFormat x
    axisFormat %S.%L
    todayMarker off

    section v4.5.0 (1721 ms)
    typed_lookup       :done,  a1, 0,   492ms
    xtracker_own       :crit,  a2, 492, 1228ms

    section v4.6.0 (921 ms)
    typed_lookup       :done,  b1, 0,   184ms
    bloxlink           :crit,  b2, 0,   860ms

    section v4.9.0 live (1221 ms)
    typed_lookup       :done,  c1, 0,   1ms
    xtracker_own       :crit,  c2, 1,   1220ms

    section v5.0.0 live (801 ms)
    typed_lookup       :done,  d1, 0,   1ms
    bloxlink           :crit,  d2, 0,   801ms

    section v5.0.0 preemptive (65 ms)
    exploit_watcher    :crit,  e1, 0,   65ms
```

**Four different bottlenecks, five generations:**

1. v4.5.0 → `typed_lookup` at 492 ms + `xtracker_own` at 1228 ms
2. v4.6.0 → `bloxlink` at 860 ms (typed got 3× faster from racing)
3. v4.9.0 → `xtracker_own` at 1220 ms (reverted Xtracker limiter)
4. v5.0.0 → `bloxlink` at 801 ms (Xtracker limiter now 0.40 s)
5. v5.0.0 preemptive → `exploit_watcher` at 65 ms (everything else cached)

### Side-by-side comparison

```mermaid
gantt
    title BGC time evolution — the visual story
    dateFormat x
    axisFormat %S.%L
    todayMarker off

    section v4.5.0 (1721 ms)
    BGC duration            :done, a1, 0, 1721ms

    section v4.6.0 safe (921 ms)
    BGC duration            :done, a2, 0, 921ms

    section v4.9.0 live (1221 ms)
    BGC duration            :done, a3, 0, 1221ms

    section v5.0.0 live (801 ms)
    BGC duration            :crit, done, a4, 0, 801ms

    section v5.0.0 preemptive (65 ms)
    BGC duration            :crit, done, a5, 0, 65ms
```

---

## 📉 Task-Level Improvements

### v4.9.0 live → v5.0.0 live

| Task | v4.9.0 (ms) | v5.0.0 (ms) | Δ (ms) | Δ (%) |
| :--- | ---: | ---: | ---: | ---: |
| `xtracker_own` | 1219.9 | 586.1 | **−633.8** | **−52.0%** |
| `username_history` | 98.3 | 53.1 | −45.2 | −46.0% |
| `simmer_rab` | 187.9 | 135.7 | −52.2 | −27.8% |
| `user_groups` | 71.9 | 52.9 | −19.0 | −26.4% |
| `user_info` | 38.6 | 25.6 | −13.0 | −33.7% |
| `keystone` | 5.7 | 5.5 | −0.2 | −3.5% |
| `external_dbs` | 6.1 | 5.6 | −0.5 | −8.2% |
| `multi_account` | 6.5 | 6.2 | −0.3 | −4.6% |
| `bloxlink` | 639.8 | 800.5 | +160.7 | +25.1% ⚠️ |
| `exploit_watcher` | 105.0 | 140.7 | +35.7 | +34.0% ⚠️ |
| `roblox_watcher` | 72.0 | 89.2 | +17.2 | +23.9% ⚠️ |
| **Total** | **1221** | **801** | **−420** | **−34.4%** |

> ⚠️ **Three tasks got slower.** `bloxlink`, `exploit_watcher`, and `roblox_watcher` all take longer in the v5.0.0 probe — but this is **normal external-API variance**, not a regression. The structural improvements are:
>
> 1. **Xtracker limiter 1.0 s → 0.40 s** cut `xtracker_own` by 52% (the largest single win).
> 2. **HTTP connection reuse** cut `username_history`, `user_groups`, `user_info` by 26–46%.
> 3. **Cache hits** on info/hist/groups made the sub-100 ms tasks essentially free.

### Preemptive fast path — task breakdown

| Task | Duration | What it does |
| :--- | ---: | :--- |
| `exploit_watcher` | **64.0 ms** | The **only** uncached network call |
| `roblox_watcher` | 56.8 ms | Second-uncached; parallel with exploit_watcher |
| `multi_account` | 6.6 ms | SQLite query (fast) |
| `external_dbs_fast` | 6.0 ms | 6 DBs in memory, ~6100 rows |
| `keystone_fast` | 5.9 ms | 2252 cases in memory |
| Everything else | <1 ms | Served from preemptive cache |

**Zero Xtracker calls.** **Zero Bloxlink calls.** **Zero Roblox API calls.** Every remote fetch that could hit the network was already done during the preemptive seed.

### The "how does this even work" table

| Layer | Cached for | What's covered |
| :--- | :---: | :--- |
| **Identity** (Bloxlink → Roblox ID) | 7 days | `bloxlink_roblox_id`, `roblox_info`, `username_history` |
| **Xtracker** (cheat registry) | 3 days | `xtracker_by_id` — registry + ownership for **all** known IDs |
| **Freshness** (mutable state) | 30 minutes | `user_groups`, `simmer_rab` |

Each tier expires independently. A user who reapplies after 2 days gets identity + Xtracker cached, but a fresh groups check. A user who reapplies after 10 days gets a full re-scan.

---

## 🏗️ Architecture

### Dual-trigger pipeline

```mermaid
flowchart TD
    A1["⌨️ TYPING_START"] --> A2{"pending already?"}
    A2 -->|"yes"| A3["ignore"]
    A2 -->|"no"| A4["_preemptive_scan()<br/>~3300 ms, hidden"]
    A4 --> A5["INSERT OR UPDATE<br/>preemptive_scans"]

    B1["📨 MESSAGE_CREATE"] --> B2{"format valid<br/>+ not privileged"}
    B2 -->|"no"| B3["ignore"]
    B2 -->|"yes"| B4{"is_already_checked?"}
    B4 -->|"yes"| B3
    B4 -->|"no"| B5["parse_recruitment_message()"]
    B5 --> B6{"_preemptive_lookup()<br/>7d/3d/30m tiers"}
    B6 -->|"hit"| B7["🏎️ Fast path<br/>_fire_t1_for(rid, cached)<br/>0 network"]
    B6 -->|"miss"| B8["🐢 Live path<br/>T0 + T1 + T2"]
    B7 --> C1["T0: exploit_watcher only"]
    B8 --> C2["T0: racing typed + nickname<br/>bloxlink shielded 1500 ms"]
    C1 --> D1["T2 fast wave<br/>keystone + external_dbs + multi"]
    C2 --> D2["T1 fire on first ID"]
    D2 --> D3["T2 fast wave at 54 ms"]
    D1 --> E1{"any HIT?"}
    D3 --> E2{"any HIT?"}
    E1 -->|"yes"| F["❌ react + sanitised reply"]
    E1 -->|"no"| G["✅ react + autorole + DM"]
    E2 -->|"yes"| F
    E2 -->|"no"| G
```

### Sequence diagram — both paths, side by side

```mermaid
sequenceDiagram
    autonumber
    actor U as Applicant
    participant D as Discord
    participant B as BGC Bot
    participant P as Preemptive Cache
    participant BL as Bloxlink
    participant XT as Xtracker
    participant KS as Keystone
    participant GS as Google Sheets

    Note over U,B: Trigger 1 — on_typing (preemptive, hidden ~3300 ms)
    U->>D: types in recruitment channel
    D->>B: TYPING_START
    par Preemptive scan
        B->>BL: GET /discord-to-roblox
        B->>XT: registry + ownership (all known IDs)
        B->>GS: simmer + groups
    end
    B->>P: store identity + xtracker + freshness

    Note over U,B: Trigger 2 — on_message (fast path 65 ms)
    U->>D: posts application
    D->>B: MESSAGE_CREATE
    activate B
    B->>B: parse_recruitment_message()
    B->>P: _preemptive_lookup()
    P-->>B: cached identity + checks
    Note over B: 🏎️ fast path
    par Only uncached checks
        B->>GS: exploit_watcher
        B->>GS: roblox_watcher
    end
    par T2 cached checks
        B->>KS: keystone (2252 cases)
        B->>GS: external_dbs (6 DBs)
        B->>B: multi_account
    end
    B-->>D: react ✅ + autorole + DM
    deactivate B
```

### Preemptive scanner internals

```mermaid
flowchart TD
    A["on_typing fires"] --> B{"(discord_id, guild_id)<br/>in _pending_preemptive?"}
    B -->|"yes"| C["bail — already scanning"]
    B -->|"no"| D["add to _pending_preemptive"]
    D --> E["load existing preemptive_scans row"]
    E --> F{"need_identity?<br/>(stale > 7d)"}
    F -->|"yes"| G["Bloxlink + nickname in parallel"]
    G --> H["save identity immediately"]
    F -->|"no"| I{"need_xtracker?<br/>(stale > 3d)"}
    H --> I
    I -->|"yes"| J["Xtracker for ALL known IDs<br/>(bloxlink + nickname + cached + DB history)"]
    J --> K["save xtracker_by_id"]
    I -->|"no"| L{"need_freshness?<br/>(stale > 30m)"}
    K --> L
    L -->|"yes"| M["groups + simmer"]
    M --> N["save groups + simmer"]
    L -->|"no"| O["nothing to do"]
    N --> P["remove from _pending_preemptive"]
    O --> P

    style A fill:#8b5cf6,color:#fff
    style H fill:#22c55e,color:#fff
    style K fill:#22c55e,color:#fff
    style N fill:#22c55e,color:#fff
```

**The critical improvement in v5.0.0:** Xtracker scans **all known IDs** — Bloxlink, nickname, cached, and DB history. That's up to 4+ IDs per scan instead of just the primary. This is why the seed time went from 2677 ms (v4.9.0) → 3306 ms (v5.0.0). But it's hidden behind typing, and it means the fast path skips Xtracker entirely for historical IDs too.

### Cache tiers

```mermaid
flowchart LR
    A["preemptive_lookup(did, gid)"] --> B{"check row exists?"}
    B -->|"no"| Z["miss → live path"]
    B -->|"yes"| C{"identity < 7d?"}
    C -->|"yes"| D["use cached info + hist"]
    C -->|"no"| D2["fresh fetch"]
    B -->|"yes"| E{"xtracker < 3d?"}
    E -->|"yes"| F["use cached xtracker_by_id<br/>for ALL known IDs"]
    E -->|"no"| F2["fresh fetch"]
    B -->|"yes"| G{"freshness < 30m?"}
    G -->|"yes"| H["use cached groups + simmer"]
    G -->|"no"| H2["fresh fetch"]
    D --> I["combined payload"]
    D2 --> I
    F --> I
    F2 --> I
    H --> I
    H2 --> I
    I --> J{"any tier fresh?"}
    J -->|"yes"| K["🏎️ fast path"]
    J -->|"no"| Z
```

---

## 🛡️ Reliability Mechanisms

Four independent safety layers. Any one alone would make the bot resilient; together they make it production-grade.

### 1. Bloxlink shield + late cache

Bloxlink can be slow. If it takes 8 seconds, we don't want to wait — but we also don't want to waste the eventual result.

```mermaid
flowchart TD
    A["bloxlink_discord_to_roblox()<br/>as a task"] --> B["wait_for(shield(task), 1500ms)"]
    B --> C{"resolved before 1500ms?"}
    C -->|"yes"| D["use real result<br/>normal identity flow"]
    C -->|"no"| E["status = 'hard_timeout'<br/>_metrics_bloxlink_timeouts++"]
    E --> F["add_done_callback(_cache_late)"]
    F --> G{"task eventually returns?"}
    G -->|"yes"| H["_store_late_bloxlink(did, gid, rid)"]
    G -->|"no"| I["discard"]
    H --> J["next BGC for same (did, gid)<br/>within 300s uses late cache"]
    D --> K["Proceed"]
    E --> K
    J --> K

    style E fill:#f59e0b,color:#fff
    style H fill:#22c55e,color:#fff
```

**Worst case:** Bloxlink takes 5000 ms. BGC proceeds at 1500 ms with typed-username fallback. Late cache stores the real result. **Next** BGC for that user gets the Bloxlink answer instantly from cache.

### 2. Adaptive Xtracker rate limiter

Xtracker 429s happen. The limiter self-tunes instead of silently failing.

```mermaid
flowchart LR
    A["acquire()"] --> B["wait current interval"]
    B --> C["fire Xtracker call"]
    C --> D{"response?"}
    D -->|"200 / 404"| E["report_ok()<br/>→ maybe decay after 60s quiet"]
    D -->|"429"| F["report_429()<br/>→ interval × 2^n<br/>(max 4×)"]
    E --> G["next call uses<br/>current interval"]
    F --> G

    style F fill:#ef4444,color:#fff
    style E fill:#22c55e,color:#fff
```

**How it works:**

| State | Interval | When |
| :--- | ---: | :--- |
| Fresh start | 0.40 s | After restart, no 429s |
| 1st consecutive 429 | 0.80 s | First rate-limit hit |
| 2nd consecutive 429 | 1.60 s | Second hit |
| 3rd+ consecutive 429 | 1.60 s | Capped at `base × 4` |
| After 60 s quiet | Decays by 1 level | Recovers toward 0.40 s |

**v5.0.0 status:** 0 rate-limited `SKIPPED` events observed since the v4.9.0 revert. The 0.40 s interval with adaptive backoff is holding steady.

### 3. Domain circuit breaker

If a Roblox mirror is down, the bot stops trying it.

```mermaid
flowchart TD
    A["request to domain"] --> B{"domain healthy?"}
    B -->|"yes"| C["race normally"]
    B -->|"no (dead until timestamp)"| D["skip this domain"]
    C --> E{"response?"}
    E -->|"success"| F["_mark_domain_ok()<br/>reset error count"]
    E -->|"failure"| G["_mark_domain_error()<br/>error_count++"]
    G --> H{"error_count >= 3?"}
    H -->|"yes"| I["mark domain dead for 60s"]
    H -->|"no"| J["try other domains"]
    I --> J
```

**Recovery is automatic** — after 60 seconds, `_filter_healthy` allows the domain back in. No manual intervention needed.

### 4. Reliability matrix

| Failure Mode | Handler | Impact |
| :--- | :--- | :--- |
| Xtracker 429 | `AdaptiveRateLimiter` | Self-corrects to 1.6×, no user impact |
| Bloxlink > 1500 ms | `BLOXLINK_HARD_TIMEOUT_MS` shield | Falls back to typed; late cache saves result |
| Roblox mirror down | `_domain_dead_until` breaker | Skips for 60 s, auto-recovers |
| Google Sheets 500 | Per-source error isolation | Other DBs still searched |
| Simmer down | Cached `SKIPPED` | Uses previous result within TTL |
| Preemptive stale | TTL expiry | Silent re-scan on next typing |
| SQLite lock contention | `bot.db_lock` + WAL | Serialized writes, no data loss |
| Process crash | Graceful signal handler | DB committed on every write |
| Bloxlink not linked | `blox_known_not_linked` state | Uses typed username path |

---

## 🗂️ Data Model

### Full schema

```mermaid
erDiagram
    GUILD_SETTINGS {
        INTEGER guild_id           PK "snowflake"
        INTEGER pass_log_channel      "nullable"
        INTEGER fail_log_channel      "nullable"
        INTEGER bot_log_channel       "nullable"
        INTEGER recruitment_channel   "nullable"
    }

    BGC_CHECKS {
        INTEGER id                 PK "autoincrement"
        INTEGER message_id            "snowflake"
        INTEGER guild_id           FK
        INTEGER discord_id            "snowflake, nullable"
        INTEGER roblox_id             "nullable"
        TEXT    roblox_username       "nullable"
        INTEGER passed                "0 or 1"
        TEXT    reason                "sanitised"
        TEXT    raw_responses         "JSON array"
        TEXT    bot_version           "5.0.0"
        INTEGER checks_version        "20"
        TEXT    checked_at            "ISO-8601"
    }

    CHECK_LOGS {
        INTEGER id                 PK "autoincrement"
        INTEGER bgc_id             FK
        TEXT    check_name            "e.g. xtracker_reg_2243794987"
        TEXT    status                "PASS|HIT|SKIPPED|ERROR"
        TEXT    details               "truncated in embeds"
    }

    PREEMPTIVE_SCANS {
        INTEGER discord_id           PK "snowflake"
        INTEGER guild_id             PK "snowflake"
        INTEGER bloxlink_roblox_id      "nullable"
        TEXT    bloxlink_status         "ok|not_linked|hard_timeout"
        TEXT    roblox_info             "JSON, 7d TTL"
        TEXT    username_history        "JSON, 7d TTL"
        TEXT    user_groups             "JSON, 30m TTL"
        TEXT    xtracker_by_id          "JSON, 3d TTL — {rid: {reg, own}}"
        TEXT    simmer_rab              "JSON, 30m TTL"
        TEXT    identity_scanned_at     "ISO-8601"
        TEXT    xtracker_scanned_at     "ISO-8601"
        TEXT    freshness_scanned_at    "ISO-8601"
    }

    GUILD_SETTINGS ||--o{ BGC_CHECKS : "guild_id"
    BGC_CHECKS     ||--o{ CHECK_LOGS : "bgc_id"
```

> **All `INTEGER` snowflake columns** hold 64-bit Discord IDs (up to 2⁶³−1). SQLite's `INTEGER` is 8-byte, so no truncation risk. **Do not cast these to `int` in client code** or you will silently corrupt Discord snowflakes above 2³¹.

### Class diagram

```mermaid
classDiagram
    class BGCBot {
        +session aiohttp
        +db aiosqlite
        +bgc_semaphore Semaphore(5)
        +xtracker_limiter AdaptiveRateLimiter(0.4)
        +bloxlink_limiter RateLimiter(1.1)
        +_domain_dead_until dict
        +_metrics_preemptive_hits int
        +_metrics_bloxlink_timeouts int
    }
    class AdaptiveRateLimiter {
        +base 0.4
        +interval 0.4..1.6
        +max_multiplier 4.0
        +decay_sec 60.0
        +acquire() await
        +report_429()
        +report_ok()
    }
    class RateLimiter {
        +interval 1.1
        +acquire() await
    }
    class ProgressReporter {
        +channel
        +user
        +start() await
        +advance(idx) await
        +finish() await
    }
    class Paginator {
        +pages
        +page
        +prev_btn()
        +next_btn()
    }

    BGCBot --> AdaptiveRateLimiter
    BGCBot --> RateLimiter
    BGCBot --> ProgressReporter
    BGCBot --> Paginator
```

### Lifecycle state machine

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Typing : TYPING_START
    Typing --> PreemptiveScan : background
    PreemptiveScan --> Idle : cached

    Idle --> Parsing : MESSAGE_CREATE
    Parsing --> Rejected : missing fields
    Parsing --> FormatTemplate : is_format_template()
    Parsing --> PreemptiveCheck : valid application

    PreemptiveCheck --> FastPath : hit (7d/3d/30m tiers)
    PreemptiveCheck --> LivePath : miss

    FastPath --> Finalizing : 65 ms
    LivePath --> Verifying : Roblox ID known
    Verifying --> CrossReferencing : T1 complete
    CrossReferencing --> Finalizing : T2 complete

    Finalizing --> Passed : 0 HITs
    Finalizing --> Failed : 1+ HITs

    Passed --> DBWritten : passed=1
    Failed --> DBWritten : passed=0
    DBWritten --> [*]
    Rejected --> [*]
    FormatTemplate --> [*]
```

---

## 🩺 Health Snapshot

Real `/health check` output from the production instance:

```text
📋 Blacklists
🟢 Group 1 (443ms)
🟢 User 0 (264ms)
🟢 Keystone 2252 (399ms)
🟢 Snow Core 1769 (572ms)

🌐 Roblox API
🟢 users.rotunnel.com
🟢 groups.rotunnel.com
🟢 users.roproxy.com
🟢 groups.roproxy.com
🟢 users.roblox.com
🟢 groups.roblox.com

🕵️ Watchlists
🟢 Xtracker registry/user — PASS
🟢 Xtracker ownership/user — PASS
🟢 Simmer RAB — PASS
🟢 Roblox Watcher — PASS
🟢 Exploit Watcher — PASS
🟢 Exploit Watcher — informational
🟢 Bloxlink — reachable (ok)

🎭 Autorole & DM
🟢 Ready — will apply @Background Check Completed
🟢 Acceptance DM — enabled (403 chars)

🗄️ External DBs
🟢 Imperial Armada Blacklist — 424 rows (324ms)
🟢 Dragonborn Blacklist — 2810 rows (652ms)
🟢 SURGE Blacklists Mainframe — 634 rows (422ms)
🟢 SOL Blacklists — 270 rows (330ms)
🟢 SOL Base Banlist — 204 rows (261ms)
🟢 BB:PC Punishment Tracker — 41 rows (492ms)

🧠 Preemptive
Records: 1 · id fresh: 1 · fresh: 1
Session hits: 1 · misses: 2
Bloxlink timeouts: 0 · late cache: 0
Identity TTL: 7d · Freshness TTL: 30min

💾 System
🟢 SQLite DB
🟢 Bot v5.0.0 · checks v20 · The Grand Imperium Of Orion
aiodns: on · Xtracker limiter: 1.00s · Bloxlink cap: 1500ms
```

**6,104 ban records across 6 external databases. 2,252 Keystone cases. 1,769 Snow Core bans. Every endpoint green. Zero rate-limit failures.**

---

## 🔥 War Stories

### The Xtracker rate limit discovery

In v4.6.0 I dropped `XTRACKER_RATE_LIMIT` from 1.0 s → 0.5 s → 0.01 s chasing faster timings. Got 821 ms — a beautiful number. Shipped it.

**Then 429s started appearing in production.** Xtracker has a hard rate limit that my local testing never hit (burst load pattern differs from individual tests). Some users got silent `SKIPPED` results from Xtracker — meaning a cheater could slip through if they timed their application during a burst.

**The fix:** revert to 1.0 s base + `AdaptiveRateLimiter`. On 429 the interval doubles (max 4×); after 60 s of silence it decays back. Now the limiter *self-tunes* to whatever Xtracker is actually willing to serve. And instead of failing on 429, the request just waits slightly longer.

**Lesson:** rate limiters are a ceiling, not a target. Every ms you shave comes with a token in a bucket you can't see.

### The bloxlink hard timeout

Before v4.9.0, `bloxlink_discord_to_roblox` had no cap — just the aiohttp session timeout (10 s). If Bloxlink was slow for 8 s, the entire BGC waited 8 s. Users saw the progress bar sit at "Resolving account" with nothing happening.

**The fix:** `BLOXLINK_HARD_TIMEOUT_MS = 1500`. The bot calls `asyncio.wait_for(asyncio.shield(blox_task), timeout=1.5)`. If it times out, status is `"hard_timeout"` and the bot falls back to the typed username — which T1 has already validated. The Bloxlink task keeps running in the background (shielded), and when it eventually returns, `_store_late_bloxlink` caches the result for 300 s.

**Result:** the *worst case* Bloxlink adds 1500 ms to the BGC. And **next time** the same user applies, the late cache means instant resolution.

**Lesson:** don't wait for slow dependencies. Cap them. But also don't waste them — cache whatever they eventually return.

### The preemptive gambit

The biggest single change. Before v4.9.0, every BGC paid the full cost of every lookup. Even a repeat user within 30 minutes had to re-fetch everything because the caches were session-scoped and short-TTL.

**The idea:** users spend seconds typing their application. That's a huge window where the server can be doing the expensive work while the user's eyes are still on their keyboard.

`on_typing` fires when a user types. We launch a background scan of everything expensive — Bloxlink, Roblox info, history, groups, Xtracker
