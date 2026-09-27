---
name: q:session-wrap
description: "Trigger: /q-session-wrap, /session-wrap, /wrap, cerrar sesion. Local-first session summary with optional authorized external persistence and backup."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "1.1.0"
---

# q:session-wrap

## Goal
Close a development session with verified progress, recovery state and a visible
report. No external memory product or database is required.

Load [Selective Context Retrieval](../../references/context-retrieval.md).
Its provider admission and persistence rules apply to every optional write.

## Procedure
1. Inspect actual Git status, relevant commits and test evidence. Do not claim
   unrelated recent commits as this session's work.
2. Save the summary to the existing local task document, or a user-authorized
   project-local session file. Include Goal, Instructions, Discoveries,
   Accomplished, Next Steps and Relevant Files. Observe filesystem permissions;
   if local persistence fails, deliver the summary in chat and report failure.
3. Only if external_write is enabled and the selected provider is configured,
   available and authorized for this write, save an appropriately scoped copy.
   Engram and SkillVault are independent optional targets, not mandatory steps.
   Reuse only an authoritative session identity; never invent one.
4. Only if sqlite_backup is enabled AND source and destination are explicitly
   authorized, perform the requested backup with a supported SQLite procedure.
   Never inspect or copy a home-directory database merely because it exists.
5. Report observed results: local summary locator, commits/checks, external writes
   and backups performed, failed, pending or skipped, plus the next step.

Unavailable external tools do not block closure. Preserve local state, never
auto-install tools, and never treat a save as the final user-facing response.
