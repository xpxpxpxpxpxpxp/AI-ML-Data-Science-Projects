# Can these model outputs prioritize a support queue?

This case study revisits a historical 21-ticket experiment in which a local language model assigned support categories, priorities, ETA phrases, and draft responses. The model marked 20 of 21 tickets High. A support lead using that field would still have to decide which of those 20 tickets to handle first.

Start with [the findings](FINDINGS.md), which quantify the priority and ETA patterns and state what cannot be evaluated. The [offline review notebook](../../SupportTickets.ipynb) is the entry point from the repository's existing link. The [original research notebook](archive/SupportTickets-original.ipynb) remains available, including its prompt, partial row displays, and saved aggregate outputs. It is an archival artifact: the private input data and model runtime are absent from this repository, and its original observation text includes incorrect claims.

## Reproduce the published findings

From the repository root, with Python 3.10+ and no third-party packages:

```sh
python projects/support-triage/analyze.py --check
python -m unittest discover -s projects/support-triage -p 'test_*.py'
```

`--check` verifies the archived notebook's exact SHA-256, parses saved outputs in cells 17 and 38–42, reconciles marginal counts against both cross-tabs, and compares the generated report to `FINDINGS.md`. To rebuild the report after an intentional, audited source change, run `python projects/support-triage/analyze.py` and inspect the diff. No external model, API key, download, or ticket dataset is used.

## Decision from the evidence

The historical model assigned High priority to 20 of 21 tickets and returned 15 different ETA phrases. This makes the priority label weak as a queue sorter, and the ETA field unsuitable as a resolution promise. I would prototype a human review queue with explicit uncertainty and separately measured response and resolution targets. Before routing or sending responses automatically, I would collect consented human labels and actual outcomes, then test escalation misses and ETA calibration. The archived run cannot establish accuracy or service improvement.

The source notebook's 21 inputs and complete model responses are not published as a row-level dataset here. Its first-five displays are insufficient for a full ticket-level audit, so this case study intentionally reports only aggregate facts recoverable from the saved tables. The public report excludes raw ticket text, identifiers, and draft responses.
