# nanobot Skills

This directory contains built-in skills that extend nanobot's capabilities.

## Skill Format

Each skill is a directory containing a `SKILL.md` file with:
- YAML frontmatter such as `name`, `description`, and metadata
- Markdown instructions for the agent
- Optional `scripts/`, `references/`, `assets/`, or `evals/` helpers

When skills reference large local documentation or logs, prefer nanobot's built-in
`grep` / `glob` tools to narrow the search space before loading full files.
Use `grep(output_mode="count")` / `files_with_matches` for broad searches first,
use `head_limit` / `offset` to page through large result sets,
and `glob(entry_type="dirs")` when discovering directory structure matters.

## Attribution

These skills are adapted from [OpenClaw](https://github.com/openclaw/openclaw)'s skill system.
The skill format and metadata structure follow OpenClaw's conventions to maintain compatibility.

## Available Skills

The list below reflects the skill directories currently present under `nanobot/skills`.

### General Utilities

| Skill | Description |
|-------|-------------|
| `agent-browser` | Headless browser automation for navigation, clicking, typing, snapshots, and form interactions. |
| `find-skills` | Search and install skills from the ClawHub public registry. |
| `skill-creator` | Create or update AgentSkills, including structure, packaging, and supporting assets. |
| `memory` | Two-layer memory system managed through Dream knowledge files. |
| `weather` | Current weather and forecast lookup. |
| `pdf` | Read, extract, merge, split, OCR, watermark, and otherwise process PDF files. |
| `cron` | Schedule reminders and recurring tasks. |
| `baoyu-slide-deck` | Generate slide deck images from content and style instructions. |

### Workplace Integrations

| Skill | Description |
|-------|-------------|
| `dingtalk-skills` | DingTalk capability hub covering tables, calendar, contacts, group chat, bots, tasks, approval, attendance, logs, and related workflows. |

### Lark / Feishu Skills

| Skill | Description |
|-------|-------------|
| `lark-shared` | Shared Lark CLI setup, auth, identity switching, scopes, and permission guidance. |
| `lark-openapi-explorer` | Explore native Lark OpenAPI endpoints not yet wrapped by existing CLI commands. |
| `lark-skill-maker` | Create reusable skills built around Lark CLI capabilities. |
| `lark-approval` | Approval instance and approval task operations. |
| `lark-attendance` | Attendance groups, shifts, records, approvals, and statistics. |
| `lark-base` | Lark Base schema, field, record, view, and related data operations. |
| `lark-calendar` | Calendar, events, participants, free/busy lookup, and meeting room workflows. |
| `lark-contact` | Directory, org structure, and employee lookup. |
| `lark-doc` | Create, edit, search, upload to, and download from Lark Docs. |
| `lark-drive` | Cloud file storage, file transfer, folders, permissions, and imports into Lark-native assets. |
| `lark-event` | Real-time Lark event subscription and event stream handling. |
| `lark-im` | Messaging, chat history, group management, and media/file handling. |
| `lark-mail` | Draft, send, reply to, search, and manage email. |
| `lark-markdown` | Convert Markdown into Lark-compatible document structures and workflows. |
| `lark-minutes` | Retrieve meeting minutes metadata and related AI-generated artifacts. |
| `lark-okr` | Query and manage Lark OKR periods, objectives, key results, and progress. |
| `lark-sheets` | Spreadsheet creation, read/write, append, search, and export workflows. |
| `lark-slides` | Create, inspect, and manage Lark Slides. |
| `lark-task` | Task and checklist management. |
| `lark-vc` | Video conference records and meeting artifact retrieval. |
| `lark-vc-agent` | Agent workflow guidance for video conference and meeting summary tasks. |
| `lark-whiteboard` | Inspect and edit Lark whiteboards, including visual exports and structured updates. |
| `lark-wiki` | Knowledge space and wiki node management. |
| `lark-workflow-meeting-summary` | Summarize meetings over a time range into a structured report. |
| `lark-workflow-standup-report` | Generate standup-style summaries from calendar and task data. |
