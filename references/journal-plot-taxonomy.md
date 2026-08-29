# Journal-informed plot taxonomy

## Scope and method

This census records graphical forms visible in public article pages or figure captions. It is a
compact architecture input, not a bibliometric study: it does not copy figures, judge scientific
quality, or count every panel. The sample contains 25 papers published in 2024–2025 across Nature,
Nature Communications, Science Advances, Environmental Science & Technology, and Water Research.
Caption wording is sometimes less specific than the rendered panel, so recurrence is deliberately
reported as an approximate paper-level lower bound.

## Caption-level census

| # | Journal and public source | Recurring graphical forms | AxiomFig mapping |
|---:|---|---|---|
| 1 | Nature, [human assembloids](https://doi.org/10.1038/s41586-025-09884-1) | line, scatter, bar, heatmap, survival, field, omics, image | line, scatter, bar, heatmap, survival, field, omics |
| 2 | Nature, [LRP8 study](https://doi.org/10.1038/s41586-025-09500-2) | line, scatter, distribution, heatmap, ordination, image | line, scatter, distribution, heatmap, ordination |
| 3 | Nature, [HIV correlates](https://doi.org/10.1038/s41586-025-09929-5) | line, scatter, distribution, ordination | line, scatter, distribution, ordination |
| 4 | Nature, [progressive coevolution](https://doi.org/10.1038/s41586-025-09779-1) | line, scatter, distribution, ordination, estimation, image | line, scatter, distribution, ordination, estimation |
| 5 | Nature, [human-specific evolution](https://doi.org/10.1038/s41586-025-09811-4) | distribution, ordination, image | distribution, ordination |
| 6 | Nature Communications, [BAI adhesion](https://doi.org/10.1038/s41467-025-67453-6) | line, scatter, distribution, image | line, scatter, distribution |
| 7 | Nature Communications, [diet–microbiome study](https://doi.org/10.1038/s41467-025-67711-7) | line, scatter, distribution, heatmap, estimation, network, omics, image | line, scatter, distribution, heatmap, estimation, association, omics |
| 8 | Nature Communications, [proteome-wide association](https://doi.org/10.1038/s41467-025-66250-5) | scatter, distribution, ordination, omics | scatter, distribution, ordination, omics |
| 9 | Nature Communications, [virus-like RNAs](https://doi.org/10.1038/s41467-025-67822-1) | line, scatter, ordination, survival, omics, image | line, scatter, ordination, survival, omics |
| 10 | Nature Communications, [macroporous frameworks](https://doi.org/10.1038/s41467-025-67123-7) | line, distribution, image | line, distribution |
| 11 | Science Advances, [anabolic matrix](https://doi.org/10.1126/sciadv.adu8440) | line, scatter, bar, heatmap, omics, image | line, scatter, bar, heatmap, omics |
| 12 | Science Advances, [xenotopic synthetic biology](https://doi.org/10.1126/sciadv.adu1710) | schematic, image | outside v1 figure scope |
| 13 | Science Advances, [core–mantle study](https://doi.org/10.1126/sciadv.adu2952) | line, distribution | line, distribution |
| 14 | Science Advances, [graphene study](https://doi.org/10.1126/sciadv.adz1855) | distribution, image | distribution |
| 15 | Science Advances, [soft robots](https://doi.org/10.1126/sciadv.adw8636) | image, schematic | outside v1 figure scope |
| 16 | Environmental Science & Technology, [automated flux chamber](https://doi.org/10.1021/acs.est.5c02365) | line, scatter, image | line, scatter |
| 17 | Environmental Science & Technology, [wildfire particles](https://doi.org/10.1021/acs.est.4c10597) | domain graphics; captions do not consistently name grammar | retained as domain evidence only |
| 18 | Environmental Science & Technology, [photoproduction study](https://doi.org/10.1021/acs.est.4c14286) | domain graphics; captions do not consistently name grammar | retained as domain evidence only |
| 19 | Environmental Science & Technology, [CoTiO3/TiO2 membrane](https://doi.org/10.1021/acs.est.4c12814) | line, scatter, distribution, image | line, scatter, distribution |
| 20 | Environmental Science & Technology, [mitochondrial metabolomics](https://doi.org/10.1021/acs.est.5c12098) | scatter, heatmap, network, omics, image | scatter, heatmap, association, omics |
| 21 | Water Research, [integrated wastewater pilot](https://www.sciencedirect.com/science/article/pii/S0043135424013423) | process trends, multi-series comparison | line, estimation |
| 22 | Water Research, [temperature-shift microbial study](https://www.sciencedirect.com/science/article/pii/S0043135424006912) | constrained ordination, composition, distribution | ordination, distribution |
| 23 | Water Research, [reinforcement-learning control](https://www.sciencedirect.com/science/article/pii/S0043135424010789) | time series, learning curves, performance comparison | line, diagnostics |
| 24 | Water Research, [biofilm microbiome study](https://www.sciencedirect.com/science/article/pii/S0043135425000508) | ordination, association network, composition | ordination, association, distribution |
| 25 | Water Research, [BiLSTM soft sensor](https://www.sciencedirect.com/science/article/pii/S0043135424002495) | time series, observed-versus-predicted, residual behavior | line, scatter, diagnostics |

## Recurrence and v1 consequence

Approximate paper-level lower bounds are: line/time-series 15/25, image or schematic 15/25,
scatter/regression 13/25, distribution 12/25, ordination 7/25, heatmap/matrix 6/25, omics 6/25,
bar/dot 3/25, association/network 3/25, estimation 2/25, survival 2/25, and field/map 1/25.
Bar and several specialized forms are probably under-counted because captions often describe the
scientific result instead of naming the graphical grammar.

The census supports a broad but bounded v1 taxonomy:

- core: `line`, `scatter`, `bar`, `distribution`, `heatmap`;
- statistical interpretation: `estimation`, `diagnostics`, `survival`;
- multivariate and domain science: `ordination`, `association`, `omics`;
- continuous and transport structure: `field`, `flow`;
- composition only: `layouts`.

Images, microscopy, chemical structures, maps/GIS, general diagrams, animation, dashboards, and a
large 3D suite are not AxiomFig v1 plot families. Multi-panel composition is a layout capability,
not a plot family.

