# Terms of Service

**Developer:** Pizzarobloxh (individual developer)  
**Bot:** BGC Bot v4.4.0  
**Effective Date:** October 20, 2026  
**Last Updated:** October 20, 2026

---

## 1. Acceptance of These Terms

These Terms of Service ("Terms") are a legal agreement between you and **Pizzarobloxh**, an individual developer ("Pizzarobloxh," "the Developer," "we," "us," "our"), who creates and operates the Discord application identified in [Section 2](#2-scope-bgc-enabled-configuration) ("the Bot").

By inviting, accessing, configuring, or interacting with the Bot — including by submitting a recruitment application in a channel that the Bot monitors, or by using any command — you agree to these Terms. If you do not agree, you must not use the Bot.

If you use the Bot on behalf of a Discord server or other entity, you represent that you have authority to bind that server or entity to these Terms.

---

## 2. Scope; BGC-Enabled Configuration

### 2.1 Single application

The Bot is a single Discord application made by Pizzarobloxh. It may provide utility, moderation, entertainment, or community-management features. When it is configured to read recruitment applications, resolve Roblox identities, or query screening databases, it operates as a **BGC-Enabled Bot**.

### 2.2 BGC-Enabled Bot

"BGC-Enabled Bot" means the Bot when it is expressly configured to perform background checks or screening. The Bot is not a BGC-Enabled Bot merely because it is installed in a server or made by Pizzarobloxh.

### 2.3 Application of BGC provisions

Sections 5, 6, 7, and 8 of these Terms apply **only** when the Bot is configured as a BGC-Enabled Bot and only to the extent it is actually configured to perform screening. When the Bot is not configured as a BGC-Enabled Bot, those sections do not apply, and the remaining sections apply to your use of the Bot.

### 2.4 Feature descriptions are not guarantees

Descriptions in the Bot's listing, documentation, or commands describe current functionality. They are not a promise that any particular feature, check, or integration will remain available.

---

## 3. Eligibility

You must be at least **13 years of age**, or the minimum age required to use Discord in your jurisdiction, whichever is higher, to use the Bot. By using the Bot, you represent that you meet this requirement.

If you are under the age of majority in your jurisdiction, you represent that you have permission from a parent or legal guardian to use the Bot.

---

## 4. The Bot Is Not a Consumer Reporting Agency

**The Bot is not a consumer reporting agency, and it does not furnish consumer reports.** Screening outputs from the Bot when configured as a BGC-Enabled Bot are not consumer reports under the U.S. Fair Credit Reporting Act (FCRA) or comparable laws.

You may **not** use the Bot, or any output from the Bot, for any purpose that requires a consumer report or a background check governed by the FCRA or analogous law, including:

- employment, hiring, promotion, or contractor eligibility;
- credit, lending, or financial eligibility;
- housing, tenancy, or real-estate eligibility;
- insurance underwriting or eligibility;
- education admission or disciplinary decisions; or
- any other purpose that is subject to a legally mandated background-check or consumer-reporting regime.

If you are unsure whether your intended use is permitted, do not use the Bot for that purpose.

---

## 5. Background Checks and Automated Screening (BGC-Enabled Bot Only)

### 5.1 What the BGC-Enabled Bot may do

When configured as a BGC-Enabled Bot, the Bot may:

- read recruitment applications posted in a channel it is configured to monitor;
- resolve the submitted typed Roblox username and the Roblox account linked to your Discord account through Bloxlink;
- retrieve public Roblox profile data for the resolved account or accounts, including username history, account creation date, and public group memberships;
- where the typed username and the Bloxlink-linked account differ, screen **both** accounts against watchlists, registries, and screening databases;
- retrieve and screen historical Roblox identities previously associated with your Discord account in the same server, for multi-account detection;
- query third-party watchlists, registries, and screening databases;
- record the results of those checks in a database; and
- post reactions, replies, and log embeds to channels configured by server administrators.

### 5.2 Screening is advisory only

All screening outputs are **advisory**. A "pass" or "fail" is not a legal determination, a finding of guilt, a statement of fact, or a guarantee of safety or trustworthiness. The Bot does not decide whether any person is admitted to, retained in, or removed from a server. **Server administrators retain final decision-making authority.**

### 5.3 No solely automated significant decisions

Where a screening output could significantly affect you, the Bot is not intended to make that decision on its own. A server administrator must review the output and make the final decision. You may ask the relevant server administrator for **human review** of a screening result, including an explanation of the result and an opportunity to contest inaccurate information. Where both a typed and Bloxlink-linked identity are screened and produce different results, a server administrator should review both results and make the final decision.

### 5.4 Automated processing and profiling

The BGC-Enabled Bot may use automated processing to compare identifiers and to flag possible matches. This processing is used to produce an advisory result for a server administrator. It is not used to make a decision based solely on automated processing where that decision would produce legal effects or similarly significant effects without human involvement.

### 5.5 Consent to screening

By submitting an application in a monitored channel, or by asking an administrator to run a command against your identifier, you consent to the screening described in this Section and in the Privacy Policy. This consent covers screening of both the typed username you submit and the Roblox account linked to your Discord account through Bloxlink, including screening of both identities when they differ.

---

## 6. Accuracy; Third-Party Data; No Guarantee

### 6.1 Third-party sources

Screening may rely on third-party services and community-maintained databases. Pizzarobloxh does not control those sources and does not independently verify every entry in them.

### 6.2 False positives and false negatives

Automated matching can produce **false positives** (incorrectly flagging an innocent person) and **false negatives** (failing to flag a person who should have been flagged). You acknowledge that this risk exists and that screening outputs are not infallible. This risk is heightened where a typed username is inaccurate: if the typed username resolves to a different account than the one linked through Bloxlink, both accounts are screened, and a mistyped username could result in screening of an unrelated account. You are responsible for ensuring the accuracy of any username you submit.

### 6.3 No obligation to remove third-party flags

Pizzarobloxh will not remove a screening result solely because a user disputes a third-party database entry. Disputes about a third-party database must be directed to that third party. Pizzarobloxh will investigate reports of a bug in the Bot itself, such as a misparsed username or an incorrect account match.

### 6.4 Availability of checks

If a third-party service is unavailable, rate-limited, or returns an error, a check may be skipped, marked as skipped, or marked as an error. A skipped check is not a pass. Checks begin as soon as an identifier is known. Where a typed username and a Bloxlink-linked account differ, both may be checked in parallel.

---

## 7. Acceptable Use

You agree not to:

1. use the Bot to harass, threaten, defame, dox, or target any person;
2. submit another person's identifier for the purpose of harassment, retaliation, or abuse;
3. use the Bot to make or support a decision that is subject to the FCRA or an analogous background-check law, as described in [Section 4](#4-the-bot-is-not-a-consumer-reporting-agency);
4. reverse-engineer, decompile, scrape, or attempt to extract the Bot's source code, models, prompts, or non-public data;
5. abuse, overload, or attempt to circumvent rate limits, access controls, or screening checks;
6. use the Bot to violate Discord's Terms of Service, Discord's Developer Terms, Discord's Developer Policy, Roblox's Terms of Use, or any applicable law;
7. collect, aggregate, or redistribute data obtained from the Bot for commercial purposes without written permission;
8. impersonate a server administrator, the Developer, or another person to gain access to administrative features;
9. upload or submit special-category data, such as health data, biometric data, or data revealing racial or ethnic origin, political opinions, religious beliefs, or sexual orientation, to the Bot; or
10. use the Bot in any way that creates a legal, security, or reputational risk for the Developer or any third party.
11. You are allowed to change the bots source code found inside of 'bot.py' by doing so you agree to not use my code in any unauthorised way.

---

## 8. Server Administrator Responsibilities

If you invite the Bot to a server or configure its behavior, you agree to:

1. ensure that server members are informed that applications may be automatically screened — including screening of both the typed username and the Bloxlink-linked account where they differ — and that a Privacy Policy applies;
2. configure recruitment and log channels appropriately, and review the Bot's permissions before use;
3. promptly review appeals and deletion requests submitted by your members;
4. make your own independent membership and moderation decisions, and not rely solely on the Bot's output;
5. comply with Discord's Terms of Service, Developer Terms, Developer Policy, Community Guidelines, and all applicable laws; and
6. not use the BGC-Enabled Bot for any purpose prohibited by [Section 4](#4-the-bot-is-not-a-consumer-reporting-agency).

You are solely responsible for your server's moderation decisions and for any consequences of those decisions.

---

## 9. User Submissions

You represent that any identifier, username, application content, or other information you submit to the Bot:

- is accurate to the best of your knowledge;
- is yours, or is submitted with the knowledge and consent of the person identified; and
- does not violate any third party's rights or any law.

You may not submit another person's information for the purpose of harassment, retaliation, or unauthorized screening.

---

## 10. Privacy and Data Protection

The collection, use, storage, and disclosure of personal data in connection with the Bot is described in the **Privacy Policy** that accompanies these Terms. By using the Bot, you acknowledge that you have read the Privacy Policy.

Where the Privacy Policy and these Terms conflict on a data-protection matter, the Privacy Policy controls for that matter.

If you are in the European Economic Area, the United Kingdom, Switzerland, California, or another jurisdiction with mandatory data-protection rights, nothing in these Terms limits any right you have that cannot be waived by contract, including rights of access, correction, deletion, restriction, objection, portability, and rights relating to automated decision-making.

---

## 11. Third-Party Services

The Bot depends on Discord and may depend on third-party APIs, proxies, databases, and watchlists. Pizzarobloxh does not control those services and is not responsible for their:

- availability, uptime, or discontinuation;
- accuracy, completeness, or timeliness;
- terms of service or privacy practices; or
- acts or omissions.

The Bot also uses **Bloxlink** to resolve Discord accounts to Roblox accounts. Bloxlink's terms and privacy practices apply to that service.

Your use of Discord remains governed by Discord's Terms of Service. Your use of Roblox remains governed by Roblox's Terms of Use. If a third-party service is unavailable, a feature that depends on it may be unavailable or may return an incomplete result.

---

## 12. Availability; Changes; Beta Features

### 12.1 Best-effort service

The Bot is provided on a **best-effort, "as available"** basis. Pizzarobloxh does not guarantee uptime, availability, latency, or uninterrupted operation.

### 12.2 Right to change

Pizzarobloxh may add, modify, limit, suspend, or remove any Bot command, feature, integration, or screening source at any time, with or without notice.

### 12.3 Beta features

Features labeled "beta," "preview," "experimental," or similar may be unstable, may change, and may be withdrawn at any time. They are provided without any service-level commitment.

---

## 13. Suspension and Termination

Pizzarobloxh may suspend, restrict, or terminate your access to the Bot — globally, per user, or per server — at any time, with or without notice, if Pizzarobloxh reasonably believes that:

- you have violated these Terms;
- your use creates a legal, security, or operational risk;
- your use may harm another person or community; or
- continued access would violate Discord's terms or applicable law.

You may stop using the Bot at any time by removing it from your server or ceasing interaction. Termination does not automatically delete historical data; deletion requests are handled as described in the Privacy Policy.

---

## 14. Intellectual Property

### 14.1 Ownership

The Bot's source code, design, documentation, branding, prompts, configuration logic, and related materials are owned by Pizzarobloxh and are protected by copyright, trademark, and other applicable laws.

### 14.2 Limited license

Subject to these Terms, you receive a limited, revocable, non-exclusive, non-transferable license to use the Bot through Discord for its intended purposes. No other license is granted.

### 14.3 Restrictions

You may not copy, modify, distribute, sell, sublicense, create derivative works from, or operate a competing service based on the Bot's code or non-public materials without Pizzarobloxh's prior written permission. Public visibility of a repository does not grant a license.

### 14.4 Third-party marks

"Discord," "Roblox," and other third-party names and marks are the property of their respective owners.

---

## 15. Disclaimer of Warranties

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, THE BOT IS PROVIDED **"AS IS" AND "AS AVAILABLE"** WITHOUT WARRANTIES OF ANY KIND, WHETHER EXPRESS, IMPLIED, OR STATUTORY, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE, NON-INFRINGEMENT, ACCURACY, AND QUIET ENJOYMENT.

PIZZAROBLOXH DOES NOT WARRANT THAT:

- the Bot will be uninterrupted, timely, secure, or error-free;
- screening results will be accurate, complete, current, or correctly matched;
- third-party data sources will be available or accurate; or
- defects will be corrected.

Some jurisdictions do not allow the exclusion of certain warranties. In those jurisdictions, the exclusions above apply only to the maximum extent permitted by law.

---

## 16. Limitation of Liability

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, PIZZAROBLOXH SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, EXEMPLARY, OR PUNITIVE DAMAGES, OR FOR ANY LOSS OF PROFITS, REVENUE, DATA, GOODWILL, MEMBERS, REPUTATION, OR BUSINESS OPPORTUNITY, ARISING OUT OF OR RELATING TO THE BOT OR THESE TERMS, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, PIZZAROBLOXH'S TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATING TO THE BOT OR THESE TERMS SHALL NOT EXCEED THE GREATER OF:

1. **TEN U.S. DOLLARS (US$10.00)**; OR
2. the total amount you paid to Pizzarobloxh for the use of the Bot in the twelve months before the event giving rise to the claim.

Nothing in these Terms limits liability that cannot be limited by law, including liability for fraud, willful misconduct, death, or personal injury caused by negligence where such limitation is prohibited.

---

## 17. Indemnification

To the maximum extent permitted by law, you agree to indemnify, defend, and hold harmless Pizzarobloxh from and against any claims, liabilities, damages, losses, and expenses, including reasonable legal fees, arising out of or relating to:

1. your use of the Bot;
2. your violation of these Terms;
3. your violation of any third-party right, including Discord's or Roblox's terms;
4. any identifier, application content, or other information you submit to the Bot; or
5. any moderation, membership, or disciplinary decision you make using the Bot's output.

---

## 18. Dispute Resolution; Governing Law

### 18.1 Informal resolution first

Before filing a formal legal claim, you and Pizzarobloxh (I hope you dont sue me as im bellow the age of 21 and still go to school) agree to try in good faith to resolve the dispute informally. You must send a written notice to the contact in [Section 21](#21-contact) describing the dispute, the relief you want, and your contact details. Pizzarobloxh will do the same if Pizzarobloxh raises a dispute. If the dispute is not resolved within **forty-five (45) days** after the notice, either party may proceed as permitted below.

### 18.2 Courts; no forced arbitration

Subject to [Section 18.3](#18-3-governing-law), any dispute that is not resolved informally may be brought in a court of competent jurisdiction. **These Terms do not require you to arbitrate** and do not waive any right to a jury trial or to participate in a class action where that right cannot be waived by law.

### 18.3 Governing law

These Terms are governed by the laws of the jurisdiction in which Pizzarobloxh resides, without regard to conflict-of-law principles. If you are a consumer, this choice of law does not deprive you of the protection of mandatory consumer-protection laws of your country of residence.

### 18.4 Non-waivable rights

Nothing in this Section 18 limits any right you have under mandatory law, including the right to bring a claim in your local courts or before a consumer-protection authority where that right cannot be waived.

---

## 19. Changes to These Terms

Pizzarobloxh may update these Terms from time to time. When we do, we will update the **Effective Date** at the top of this document. If a change is material, we will make reasonable efforts to provide notice, such as through the Bot's support server or documentation.

Continued use of the Bot after the effective date of an updated version constitutes acceptance of the updated Terms. If you do not agree to an updated version, your remedy is to stop using the Bot.

Changes will not apply retroactively to a dispute that arose before the change.

---

## 20. General Provisions

### 20.1 Severability

If any provision of these Terms is held invalid, illegal, or unenforceable, that provision will be limited or severed to the minimum extent necessary, and the remaining provisions will remain in full force and effect.

### 20.2 Entire agreement

These Terms, together with the Privacy Policy and any additional terms expressly incorporated by reference, constitute the entire agreement between you and Pizzarobloxh regarding the Bot.

### 20.3 No waiver

A failure to enforce any provision is not a waiver of that provision or of any other provision.

### 20.4 Assignment

You may not assign these Terms without Pizzarobloxh's prior written consent. Pizzarobloxh may assign these Terms in connection with a transfer of the Bot or a reorganization.

### 20.5 Force majeure

Pizzarobloxh is not liable for any delay or failure to perform caused by events beyond reasonable control, including outages of Discord, Roblox, third-party APIs, hosting providers, or the internet.

### 20.6 Survival

Sections 4, 6, 9, 10, 14, 15, 16, 17, 18, and 20 survive termination of these Terms.

### 20.7 Third-party beneficiaries

Discord is not a party to these Terms and has no obligations under them. Nothing in these Terms creates any third-party beneficiary right except as expressly stated.

---

## 21. Contact

Questions, concerns, notices, and deletion requests should be sent through the official **Pizzarobloxh** Discord support server for the Bot:

**https://discord.gg/HW4ArA8rAE**

---

*These Terms of Service were last updated on October 20, 2026.*
