# Matplotlib-native attempt ledger

The live machine log was appended during work at
`tmp/figure-capability-audit/attempts.jsonl`. The table below is the committed audit summary. An
attempt is counted only when code or geometry changed; repeatability runs and rasterization are not
attempts. Every final PDF was rasterized and inspected.

| ID | Build attempts | Successful renders | Execution failures | Visual repair cycles | Final verdict | Difficulty | Primary failure codes | Final review |
|---|---:|---:|---:|---:|---|---|---|---|
| 01 | 7 | 5 | 2 | 3 | ACCEPTED | HARD | G03, O02, O04, E01, E02 | Two row strips, one column strip, Matplotlib-owned dendrogram artists, legend and colorbar are present; two final colorbar containment repairs were required. |
| 02 | 2 | 2 | 0 | 1 | ACCEPTED | MODERATE | G04 | Rebuilt from 4 x 4 to the required 5 x 5 shared-variable grid; outer labels and global legend are legible. |
| 03 | 2 | 2 | 0 | 1 | ACCEPTED | MODERATE | G04, T01 | Added supplied-density topology, selected labels and coordinated marginals; no visible clipping. |
| 04 | 2 | 2 | 0 | 1 | ACCEPTED | MODERATE | G06, T03 | Expanded 14 to 24 estimates and added subgroup headers/right statistics while retaining readable rows. |
| 05 | 1 | 1 | 0 | 0 | ACCEPTED | EASY | O03 | Survival and risk-table axes align and remain readable at the frozen page size. |
| 06 | 2 | 2 | 0 | 1 | ACCEPTED | MODERATE | G04, O01 | Expanded to four reliability curves and four coordinated histogram axes. |
| 07 | 3 | 2 | 1 | 1 | ACCEPTED | MODERATE | G04, O02, E01 | Added four 1-D PDP/ICE panels plus a 2-D surface and colorbar; one missing-token runtime repair. |
| 08 | 2 | 2 | 0 | 1 | ACCEPTED WITH FRAGILITY | FRAGILE | T01, T02, T05, E02 | Eighteen labels are contained and readable, but deterministic edge lanes are case-specific. |
| 09 | 2 | 2 | 0 | 1 | ACCEPTED WITH FRAGILITY | FRAGILE | T01, T05, E02 | Thirty labels are legible, but long cross-panel connectors still cross; retained as diagnostic evidence. |
| 10 | 2 | 2 | 0 | 0 | ACCEPTED | EASY | O02, O04 | Dendrogram geometry is computed without plotting by SciPy, then drawn by Matplotlib and aligned to the dot matrix. |
| 11 | 1 | 1 | 0 | 0 | ACCEPTED | EASY | G03 | Intersection bars, set totals and membership connectors share deterministic ordering. |
| 12 | 1 | 1 | 0 | 0 | ACCEPTED | EASY | G03, O01 | Multi-glyph cells, marginal frequencies, percentages and legend remain contained. |
| 13 | 3 | 3 | 0 | 2 | ACCEPTED | HARD | G04, T03, E02 | Overlapping Axes hid labels twice; figure-level labels now preserve all twelve ridge identities. |
| 14 | 1 | 1 | 0 | 0 | ACCEPTED | EASY | A02 | Violin, box, raw-point and supplied-bracket layers remain distinguishable. |
| 15 | 1 | 1 | 0 | 0 | ACCEPTED WITH MINOR DEBT | HARD | T01, T05, E02 | Twelve loading labels are readable; a small amount of loading-label crowding remains. |
| 16 | 1 | 1 | 0 | 0 | ACCEPTED | EASY | None | Known-control Mantel anatomy is complete; the actual Skill render also validated. |
| 17 | 2 | 1 | 1 | 0 | ACCEPTED | MODERATE | G03, O01, O02, E01 | Repaired an invalid colormap token; all four diagnostic panels and the colorbar render. |
| 18 | 2 | 2 | 0 | 1 | ACCEPTED WITH FRAGILITY | FRAGILE | T01, T02, T05, E02 | Selected observation labels use deterministic lanes; layout is readable but case-specific. |
| 19 | 1 | 1 | 0 | 0 | ACCEPTED | MODERATE | G04, O01 | Six panels for two models align; bands, timing and model identity remain legible. |
| 20 | 1 | 1 | 0 | 0 | ACCEPTED | EASY | A02, T01 | Dense Manhattan structure, thresholds, labels and Q-Q reference are visible. |

## Aggregate

- Material attempts: **39**; median **2/case**; P90 **3**; maximum **7**.
- Successful render attempts: **35**; execution failures: **4**; visual repair cycles: **13**.
- Final native results: **20 successful**, including **3 classified FRAGILE**, and **0 MISSING**.
- Five-run repeatability is **20/20**; repeat runs did not increment attempt counts.

## Material iteration notes

- Attempts 01.1 and 01.2 failed before rendering: repository bootstrap import, then the neutral
  palette lookup. Both were benchmark-infrastructure defects, not layout evidence.
- The first contact-sheet pass exposed missing topology in 01–04 and 06–07, insufficient label
  coverage in 08–09, hidden ridge labels in 13, and diagnostic-label overlap in 18.
- The second pass accepted 01–08. Case 09 was deliberately frozen with visible connector crossings
  rather than consuming the budget on more case-local coordinates.
- Case 13 required a second repair because overlapping Axes occluded per-Axes text; the accepted
  solution uses figure-level row labels. Case 18 was accepted after deterministic lane placement.
- A final ownership audit found that cases 01 and 10 still let SciPy create dendrogram artists.
  SciPy now returns only `no_plot` geometry and Matplotlib owns every line. Case 01 then needed two
  visually inspected colorbar-position repairs to restore decorated containment.
- The external probe was run only after these native outcomes and five-run signatures were frozen.
