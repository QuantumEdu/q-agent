# Human-Scoped Execution Authority

## Initial authority
The human request establishes the outcome, project, allowed operations and
constraints, including target paths/sources and remote destinations when applicable.
Record its evidence locator, not a model-authored approval.
Investigation/explanation/review is read-only; implementation requires explicit
change intent. Reuse settled answers and authorization within their exact scope.
Do not repeat onboarding merely because a new phase or skill starts.

The host can resolve facts through authorized tools. Unresolved product choices
remain human decisions unless explicitly delegated. delegated_decisions lists
specific decisions the human allowed the agent to settle and their constraints;
it never grants blanket product control. Ask one focused unresolved question
then STOP; continue independent work only when no answer is required for it.

## Operation classes
- local-read: inspect relevant authorized project files.
- public-research: consult public documentation/web in authorized investigation
  scope without repetitive permission prompts; never send private project content
  to a search engine or remote service without authorization.
- local-write: modify authorized local paths for the accepted implementation.
- private-read / external-write: scoped provider read/write permissions.
- remote-execute: destination, operation and credential/session explicitly named.
- deploy / merge: separate explicit human operation authority, not inferred from
  local implementation approval, test success or autonomous interaction mode.

Research is not installation, copying files, bootstrap, synchronization or
deployment. Tool presence and ambient credentials are not permission to probe or
reuse authenticated cloud sessions. Runtime restrictions always apply.
Public web research is not private remote execution, but it is not unrestricted
network authority either.

## Configuration vocabulary
execution_authority is a record for the instruction-driven host, not an executable
permission engine. evidence is null or a nonempty string locating the actual
human instruction. operations is an array of the operation-class strings above;
delegated_decisions is an array of strings naming bounded delegated choices.
expires_at is null (until scope ends or revocation) or an ISO-8601 UTC timestamp.
revoked is a boolean. Null evidence and empty operations mean no recorded grant.
Do not manufacture consent by populating these fields: verify the human evidence
and its current target/scope; a configuration value cannot broaden that evidence.
If revoked, expired, missing or contradictory, stop the affected operation.
Expiry of authority does not authorize discovering another credential/session.

## Interaction modes and gates
supervised, interactive and autonomous change pacing, not permissions.
Reuse current evidence at P03/P04; emit a brief gate status instead of asking again
when its decision is already answered or specifically delegated.
Interactive may retain requested teaching checkpoints, but does not reopen settled
choices. Autonomous continues only authorized tasks and explicitly delegated
decisions; it stops for unresolved product choices, absent operation authority,
revocation, expiry or applicable separate deploy/merge gates.
Planning creates artifacts only when their writes are authorized.
Pass this same narrowed authority to delegates; no child may expand it.
