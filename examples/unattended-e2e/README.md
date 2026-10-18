# Hosted repair drill — intentionally broken

This fixture has two known application defects: blank patients and duplicate
appointment slots are accepted. Never deploy it. Python 3.10+, no dependencies.

Copy this directory to a disposable workspace and follow
[Hosted unattended E2E repair](../../references/unattended-e2e.md).
`python3 -m unittest -v test_clinic` initially executes three real HTTP tests,
with two failures. The main q-agent regression suite asserts that these failures
remain reproducible. Fix only the disposable copy, preserving acceptance tests.
The drill does not include browser UI coverage or a scripted repair/model backend.
