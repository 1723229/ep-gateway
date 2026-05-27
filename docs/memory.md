# Memory in nanobot

nanobot's memory is built on a simple belief: memory should feel alive, but it should not feel chaotic.

Good memory is not a pile of notes. It is a quiet system of attention. It notices what is worth keeping, lets go of what no longer needs the spotlight, and turns lived experience into something calm, durable, and useful.

That is the shape of memory in nanobot.

## The Design

nanobot does not treat memory as one giant file.

It separates memory into layers, because different kinds of remembering deserve different tools:

- `sessions/*.jsonl` holds the living short-term conversation for each channel/session.
- `memory/history.jsonl` is the running archive of compressed past turns.
- `SOUL.md`, `USER.md`, and `memory/MEMORY.md` are the durable knowledge files.
- `GitStore` records how those durable files change over time.

By default the workspace is `~/.hiperone/workspace`, so these files live under `~/.hiperone/workspace/`.

This keeps the system light in the moment, but reflective over time.

## The Flow

Memory moves through nanobot in two stages.

### Stage 1: Consolidator

When a conversation grows large enough to pressure the context window, nanobot does not try to carry every old message forever.

Instead, the `Consolidator` summarizes the oldest safe slice of the conversation and appends that summary to `memory/history.jsonl`.

This file is:

- append-only
- cursor-based
- optimized for machine consumption first, human inspection second

Each line is a JSON object:

```json
{"cursor": 42, "timestamp": "2026-04-03 00:02", "content": "- User prefers dark mode\n- Decided to use PostgreSQL"}
```

It is not the final memory. It is the material from which final memory is shaped.

### Stage 2: Dream

`Dream` is the slower, more thoughtful layer. It runs on a cron schedule by default and can also be triggered manually.

Dream reads:

- new entries from `memory/history.jsonl`
- the current `SOUL.md`
- the current `USER.md`
- the current `memory/MEMORY.md`

Then it works in two phases:

1. It studies what is new and what is already known.
2. It edits the long-term files surgically, not by rewriting everything, but by making the smallest honest change that keeps memory coherent.

This is why nanobot's memory is not just archival. It is interpretive.

## The Files

```text
workspace/
├── SOUL.md              # The bot's long-term voice and communication style
├── USER.md              # Stable knowledge about the user
├── sessions/            # Per-session short-term conversation JSONL files
└── memory/
    ├── MEMORY.md        # Project facts, decisions, and durable context
    ├── history.jsonl    # Append-only history summaries
    ├── .cursor          # Consolidator write cursor
    ├── .dream_cursor    # Dream consumption cursor
    └── .git/            # Version history for long-term memory files
```

These files play different roles:

- `SOUL.md` remembers how nanobot should sound.
- `USER.md` remembers who the user is and what they prefer.
- `MEMORY.md` remembers what remains true about the work itself.
- `history.jsonl` remembers what happened on the way there.

## Auto Compact

There are two compaction paths:

- **Token-driven consolidation** runs when the prompt gets too large. It appends summaries to `memory/history.jsonl` and advances an internal cursor, but it does not rewrite older raw session messages immediately.
- **Idle auto compact** runs only when `agents.defaults.idleCompactAfterMinutes` is greater than `0`. It archives older idle-session messages to `memory/history.jsonl`, keeps a recent legal suffix in `sessions/*.jsonl`, and rewrites that session file with the compacted form.

Leave `idleCompactAfterMinutes` at `0` if you need full structured session JSONL for debugging or auditing. Use token-driven consolidation alone when preserving the raw tool-call trail matters more than minimizing idle-session replay cost.

## Why `history.jsonl`

The old `HISTORY.md` format was pleasant for casual reading, but it was too fragile as an operational substrate.

`history.jsonl` gives nanobot:

- stable incremental cursors
- safer machine parsing
- easier batching
- cleaner migration and compaction
- a better boundary between raw history and curated knowledge

You can still search it with familiar tools:

```bash
# grep
grep -i "keyword" memory/history.jsonl

# jq
cat memory/history.jsonl | jq -r 'select(.content | test("keyword"; "i")) | .content' | tail -20

# Python
python -c "import json; [print(json.loads(l).get('content','')) for l in open('memory/history.jsonl','r',encoding='utf-8') if l.strip() and 'keyword' in l.lower()][-20:]"
```

The difference is philosophical as much as technical:

- `history.jsonl` is for structure
- `SOUL.md`, `USER.md`, and `MEMORY.md` are for meaning

## Commands

Memory is not hidden behind the curtain. Users can inspect and guide it.

| Command | What it does |
|---------|--------------|
| `/dream` | Run Dream immediately |
| `/dream-log` | Show the latest Dream memory change |
| `/dream-log <sha>` | Show a specific Dream change |
| `/dream-restore` | List recent Dream memory versions |
| `/dream-restore <sha>` | Restore memory to the state before a specific change |

These commands exist for a reason: automatic memory is powerful, but users should always retain the right to inspect, understand, and restore it.

## Versioned Memory

After Dream changes long-term memory files, nanobot can record that change with `GitStore`.

This gives memory a history of its own:

- you can inspect what changed
- you can compare versions
- you can restore a previous state

That turns memory from a silent mutation into an auditable process.

## Configuration

Dream is configured under `agents.defaults.dream`:

```json
{
  "agents": {
    "defaults": {
      "dream": {
        "intervalH": 2,
        "modelOverride": null,
        "maxBatchSize": 20,
        "maxIterations": 15
      }
    }
  }
}
```

| Field | Meaning |
|-------|---------|
| `intervalH` | How often Dream runs, in hours |
| `modelOverride` | Optional Dream-specific model override |
| `maxBatchSize` | How many history entries Dream processes per run |
| `maxIterations` | The tool budget for Dream's editing phase |
| `annotateLineAges` | Whether Dream annotates stale `MEMORY.md` lines with git-blame age hints before analysis |

In practical terms:

- `modelOverride: null` means Dream uses the same model as the main agent. Set it only if you want Dream to run on a different model.
- `maxBatchSize` controls how many new `history.jsonl` entries Dream consumes in one run. Larger batches catch up faster; smaller batches are lighter and steadier.
- `maxIterations` limits how many read/edit steps Dream can take while updating `SOUL.md`, `USER.md`, and `MEMORY.md`. It is a safety budget, not a quality score.
- `annotateLineAges` defaults to `true`. Set it to `false` if you want Dream to analyze `MEMORY.md` without per-line age hints.
- `intervalH` is the normal way to configure Dream. Internally it runs as an `every` schedule, not as a cron expression.

Idle auto compact is configured separately under `agents.defaults`:

```json
{
  "agents": {
    "defaults": {
      "idleCompactAfterMinutes": 15
    }
  }
}
```

`0` disables idle auto compact, which is the default.

Legacy note:

- Older source-based configs may still contain `dream.cron`. nanobot continues to honor it for backward compatibility, but new configs should use `intervalH`.
- Older source-based configs may still contain `dream.model`. nanobot continues to honor it for backward compatibility, but new configs should use `modelOverride`.

## In Practice

What this means in daily use is simple:

- conversations can stay fast without carrying infinite context
- durable facts can become clearer over time instead of noisier
- the user can inspect and restore memory when needed

Memory should not feel like a dump. It should feel like continuity.

That is what this design is trying to protect.
