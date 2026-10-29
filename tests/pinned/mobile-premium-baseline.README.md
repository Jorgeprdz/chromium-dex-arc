# Immutable mobile ownership baseline

`mobile-premium-baseline.json` records SHA-256 of the protected complete files and
exact method bodies from commit `677c73fcebd14d37b52ec68e2dffba627282c0bf`.
It was generated from that commit's Git objects, never from the tested HEAD.
Method bodies use the existing `arc_toolbar_probe.method_body` extractor and UTF-8.
Whole-file hashes use the original bytes.

The tests compare current source with these stored values, retaining exact ownership
checks without network requests, ancestor Git objects, or deeper CI checkouts.
`test_mobile_premium_shallow.py` runs them from a directory without `.git` and verifies
that a changed protected pull owner still fails. Missing baselines fail the tests;
there is no skip, automatic refresh or fallback to current source.

Only change this baseline after explicit approval of changes to the protected
camera, pull, gesture, viewport, status visibility or capture scheduling contracts.
These checks do not demonstrate device acceptance.
