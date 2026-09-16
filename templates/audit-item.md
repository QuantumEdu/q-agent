---
id: "A00"
slug: "template-item"
audit_date: "YYYY-MM-DD"
project: ""
category: ""
severity: "none"
status: "pending"
---

## Summary

<!-- One paragraph: what was inspected, what was found. Be specific about file paths. -->

## Violations

<!-- List each violation with evidence tag. If none found, state "No violations detected." -->

<!-- Format:
- [OBSERVADO: path/to/file#LN-LM] Description of violation and its runtime impact.
- [INFERIDO] Description when evidence is partial or indirect.
- [CONFLICTO: source-a vs source-b] When two sources contradict each other.
-->

## Severity Justification

<!-- Explain why the chosen severity level (none/low/medium/high/critical) was assigned.
     Reference the violations above and their blast radius.
     If severity is "none", state what was verified and why it passes. -->

## EARS Spec

<!-- Required only when severity > none. Use EARS syntax:
     WHEN [trigger or condition]
     THE SYSTEM SHALL [required behavior or constraint]
     [IF [optional condition]]
     [SO THAT [rationale or outcome]]

     If severity is "none", write: N/A — No remediation required. -->
