# Saved-output analysis

Source notebook [`archive/SupportTickets-original.ipynb`](archive/SupportTickets-original.ipynb), SHA-256 `5576ab7c5a210da864716690faeedc51dce2d93543e14111062856e7f5e7bd0b`. The command `python projects/support-triage/analyze.py --check` parses its saved `text/plain` outputs in cells 17 and 38–42, reconciles the tables, and checks the published report text. No model call or private dataset is needed.

| Saved output | Count |
| --- | ---: |
| Input tickets | 21 |
| Technical Issue | 11 |
| Data Recovery | 6 |
| Hardware Issue | 4 |
| High priority | 20 |
| Medium priority | 1 |
| Low priority | 0 |
| Distinct ETA strings | 15 |
| ETA strings beginning “Within” | 10 tickets |
| Conditional or unbounded ETA strings | 11 tickets |

## What the outputs reveal

**Priority has little sorting power in this sample.** The model marked 20/21 tickets High (95.2%); the only Medium ticket is Technical Issue. All 6 Data Recovery and 4 Hardware Issue tickets are High. A queue using this label would still need another decision rule for nearly every ticket. These are model assignments, not verified severities.

**ETA is neither a consistent resolution estimate nor a measured time.** There are 15 distinct phrases for 21 tickets. 10 begin with “Within,” but some explicitly refer to initial assessment or first contact, and one is conditional on parts. The other 11 use language such as “varies” or “depends,” including 6/6 Data Recovery, 3/4 Hardware Issue, and 2/11 Technical Issue tickets. None of these values is an observed resolution duration or a defensible service commitment. The prior claim of an average 2–3 business days cannot be calculated from this archive.

**A review queue is the next experiment.** Separate incident severity, response target, and resolution forecast; permit an explicit “needs diagnosis” state. Ask human reviewers to label urgency and resolution outcomes on a consented sample, then evaluate agreement, escalation misses, calibration, and subgroup failures before any automated routing. The saved outputs alone cannot establish classification accuracy, response safety, speed at scale, or business impact.

## Evidence boundary

The original notebook displays the first five parsed rows and aggregate tables; it does not retain a complete machine-readable row-level result set or the source dataset. This page only publishes aggregates. Its saved outputs document one historical run of a local GGUF model, with no ground-truth categories, priority labels, actual resolution times, or live follow-up. Counts are descriptive of that run and should not be treated as performance metrics.
