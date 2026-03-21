# JobApplicationBot – Randy Walker

## Quick Start

1. **Run setup.bat** (first time only)
2. **Copy your 4 PDF resumes** to the `resumes/` folder with these exact names:
   - `2025 Randy Walker - IT Executive.pdf`
   - `2025 Randy Walker - Tech Leader.pdf`
   - `2025 Randy Walker - Cloud.pdf`
   - `2025 Randy Walker - Cloud Contract.pdf`
3. **Run run.bat** – the dashboard opens at `http://localhost:5000`
4. **Open Settings** and configure:
   - Your LinkedIn session cookie (for job searching)
   - Email settings (for job alert monitoring + notifications)

---

## Resume Selection Logic

| Situation | Resume Used |
|---|---|
| Indian IT staffing firm detected | Cloud Contract (screening email/phone) |
| VP / CxO / SVP title | IT Executive |
| Cloud / Azure / Infrastructure / DevOps title | Cloud |
| Everything else (IT Manager, Director, etc.) | Tech Leader |

**Indian firm detection** looks for: known Indian IT firm names (Infosys, Wipro, TCS, HCL, etc.), C2C/corp-to-corp patterns, H1B transfer mentions, and other staffing patterns. When detected, the `jobs.randywalker@outlook.com` email and `(479) 871-2172` phone are used automatically.

---

## Q&A Automation (How Claude Answers Questions)

The app tries these methods in order:

1. **Pre-built answers** – Common questions (salary, authorization, relocation, etc.) are answered instantly from your profile data
2. **Claude Code CLI** – If `claude` is installed, questions are piped directly to it — fully automated
3. **Anthropic API key** – If set in Settings, calls the API directly
4. **Clipboard + Claude.ai** – If none of the above: prompt is copied to clipboard, Claude.ai opens in your browser, you paste and return the answer at `http://localhost:5000/answer`

To check if Claude CLI is installed, open a terminal and type: `claude --version`

---

## Getting Your LinkedIn Cookie

1. Log into LinkedIn in Chrome
2. Press F12 → Application tab → Cookies → `www.linkedin.com`
3. Find the `li_at` cookie and copy its value
4. Paste it in Settings → LinkedIn Session Cookie

This lets the bot search and apply on your behalf without triggering re-login.

---

## Job Filtering Rules

- **Role type**: Only management roles are queued (Manager, Director, VP, Head of, etc.). Individual contributor roles (Engineer, Analyst, Specialist, etc.) are auto-skipped.
- **Match score**: Only jobs with 50%+ skill match are queued. You can change this in Settings.
- **Duplicates**: Already-seen job URLs are ignored.
- **Indian firms**: Automatically flagged and use the Contract resume.

---

## Email Monitoring

Forward your LinkedIn/Indeed job alert emails to `randy.walker@live.com`. The app checks your inbox every 30 minutes, extracts job URLs, analyzes them, and adds qualifying ones to your queue.

Configure IMAP in Settings → Email. Use an **App Password** (not your main password).

For Outlook/Live: https://account.microsoft.com/security → App passwords

---

## Automation Levels

| Setting | Behavior |
|---|---|
| Default | App finds jobs → you review → you queue → you click Apply |
| Auto-apply OFF | App finds + analyzes, you approve each application |
| Auto-apply ON | Fully automatic: finds, analyzes, applies with no review |

Start with Auto-apply OFF until you're comfortable with how it works.

---

## Supported Job Sites

- **LinkedIn** (Easy Apply) – Most automated
- **Indeed** (Indeed Apply) – Highly automated
- **Workday** (any `*.myworkdayjobs.com` URL) – Automated form filling
- **Other sites** – Job imported + analyzed; application may need manual steps

---

## Troubleshooting

**LinkedIn shows login page**: Your `li_at` cookie may have expired. Log into LinkedIn again and grab a fresh cookie value.

**Application failed**: Check the job's Notes in the dashboard. The browser window stays open so you can complete it manually if needed.

**Desktop notifications not working**: Make sure Python has notification permissions in Windows Settings → Notifications.

**Claude CLI not found**: Install from https://docs.anthropic.com/en/docs/claude-code or set an Anthropic API key in Settings.
