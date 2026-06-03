# Agent Instructions

## Workspace Guidance

Use this file for project-specific preferences, recurring workflow conventions, and instructions you want the agent to remember for this workspace. Keep durable facts about the user in `USER.md`, personality/style guidance in `SOUL.md`, and long-term memory in `memory/MEMORY.md`.

## Scheduled Reminders

Before scheduling reminders, check available skills and follow skill guidance first.
Use the built-in `cron` tool to create/list/remove jobs (do not call the cron CLI via `exec`).
Get USER_ID and CHANNEL from the current session (e.g., `8281248569` and `telegram` from `telegram:8281248569`).

**Do NOT just write reminders to MEMORY.md** — that won't trigger actual notifications.

## Heartbeat Tasks

`HEARTBEAT.md` is checked periodically when registered as a cron job. Use the built-in `cron` tool to schedule it (e.g. `cron add --name heartbeat --schedule "every 30m" --message "Check HEARTBEAT.md"`).

- Use `apply_patch` for normal task-list updates, especially when adding, removing, or changing multiple lines.
- Use `edit_file` only for small exact replacements copied from the current `HEARTBEAT.md`.
- Use `write_file` for first creation or intentional full-file rewrites.

When the user asks for a recurring/periodic task, update `HEARTBEAT.md` instead of creating a one-time cron reminder.

## Skill Routing

When a user's request matches a specific skill domain, ALWAYS read the corresponding SKILL.md before attempting the task:

- **创建/编辑/优化技能**: Any request to create, modify, improve, or test a skill → read skill-creator SKILL.md first

Do not attempt these tasks from memory alone — the skills contain specific scripts, APIs, and parameters that change over time.
