# AxiomFig formal Gallery

This directory is generated release evidence, organized as one serif-only directory per scientific
family. Each stem has one PDF and one PNG produced by the real AxiomFig runtime and validated as a
pair.

The Gallery is curated rather than a one-to-one projection of public IDs. Compatibility-only
template IDs remain executable but are not promoted as current Agent recommendations. The Bar
family intentionally includes multiple representative cases for its nine core grammars.

Rebuild and validate from the repository root:

```bash
axiomfig-gallery --gallery gallery --work-root tmp/gallery
axiomfig-validate gallery
```

Sans typography remains a supported runtime mode; it is not duplicated in the formal Gallery.
Technical probes and capability audits belong to tests, temporary workspaces, or reports—not this
user-facing evidence tree.
