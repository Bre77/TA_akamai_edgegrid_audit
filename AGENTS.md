# Project agent memory

This file is the project's committed home for project-intrinsic agent knowledge: build, test, release, architecture, and sharp-edge notes that should travel with the code.

- Add durable project-specific notes here as they are discovered through real work.
- `lib/requirements.txt` must list every third-party import actually reached at runtime, not just `splunk-sdk`. `bin/akamai_edgegrid_audit.py` imports `requests` and `dateutil` directly, and `lib/akamai/__init__.py` imports `pkg_resources` (via the legacy `pkg_resources.declare_namespace` namespace-package pattern) at import time. These worked historically only because Splunk's bundled Python happened to provide them.
- `setuptools` is pinned `<81` because 82+ dropped the `pkg_resources` module entirely, which `lib/akamai/__init__.py` needs. If that vendored namespace-package shim is ever removed, this pin can go too.
- `splunk-sdk` is capped `>=2.1.1,<3` since 3.0.0 requires Python 3.13 and cannot run on 3.9; Splunk add-ons need to support both during the 3.9->3.13 transition.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
