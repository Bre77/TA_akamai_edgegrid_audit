# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.
- `lib/requirements.txt` must list every third-party import actually reached at runtime, not just `splunk_input_runtime`. `bin/akamai_edgegrid_audit.py` imports `requests` and `dateutil` directly, and `lib/akamai/__init__.py` imports `pkg_resources` (via the legacy `pkg_resources.declare_namespace` namespace-package pattern) at import time. These worked historically only because Splunk's bundled Python happened to provide them.
- `setuptools` is pinned `<81` because 82+ dropped the `pkg_resources` module entirely, which `lib/akamai/__init__.py` needs. If that vendored namespace-package shim is ever removed, this pin can go too.
- This app runs on `splunk_input_runtime` (https://github.com/Bre77/splunk-input-runtime), not `splunklib`/`splunk-sdk`. `lib/requirements.txt` pins it to an exact commit archive URL with a `sha256:` hash recorded in a comment above it (no PyPI package exists yet, so there is no `==version` line to pin against). Bump both the commit and the recorded hash together when the runtime releases a new version; never point at a branch.
- Credential handling goes through `self.context.credentials.protect_input_fields(...)` (see `bin/akamai_edgegrid_audit.py`), not manual `storage_passwords` list/delete/create calls. This preserves the credential identity `(owner=nobody, app=TA_akamai_edgegrid_audit, realm=<stanza name>, username=<field name>)` that existing installs already have for `client_token`, `client_secret`, `access_token`, and the optional `proxy` (declared as `SecretField("proxy", optional=True)` so a blank proxy is left alone, never deleted, and never clears the other three secrets) - do not change that tuple without a captain-level decision; it strands users' stored secrets. The proxy setting stays per-input; it is not a global setting.
- The runner (`Script.run_script`) owns `EventWriter.close()`; app code must not call it explicitly.
- `.build.sh` strips `__pycache__` with `find lib -type d -name __pycache__ -prune -exec rm -rf {} +` (depth-agnostic) rather than fixed-depth globs, because vendored packages (e.g. `setuptools`'s bundled `_vendor` tree) nest `__pycache__` dirs deeper than any fixed glob reaches, and AppInspect fails the package on leftover compiled `.pyc` files.
- `.github/workflows/validate.yml` runs `.build.sh` + AppInspect on every push/PR via `Bre77/splunk_nats`'s reusable workflow; keep it green before any Splunkbase republish.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
