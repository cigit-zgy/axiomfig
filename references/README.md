# AxiomFig reference map

`SKILL.md` is the Agent entry point. This directory is progressive-disclosure knowledge: read only
the document needed for the current decision.

## Agent-facing references

| Need | Read |
|---|---|
| execution / clarification / unsupported decision | `agent-protocol.md` |
| Figure Intent syntax | `figure-intent.md` |
| choose a figure family when scientific intent is ambiguous | `template-knowledge/index.yaml` → one routed topic |
| choose a grammar/schema inside a selected family | `template-knowledge/index.yaml` → one `family_guides` entry |
| non-default visual or positional request | `element-contracts/index.md` → one routed topic |
| advanced Mantel semantics | `mantel.md` |

## Scientific figure vocabulary

| Need | Read |
|---|---|
| figure elements, ownership, coordinates, spatial relations | `figure-anatomy.md` |
| template registry / family architecture | `template-system.md` |

## Runtime/developer contracts

| Need | Read |
|---|---|
| visual hierarchy, palettes, artist conventions | `style-contract.md` |
| panel / Primary / Auxiliary geometry and reservation | `layout-contract.md` |
| fonts and text behavior | `typography.md` |
| LaTeX syntax/finalization boundary | `latex-contract.md` |
| artifact and structural checks | `validation.md` |
| project design rationale and provenance | `design-rationale.md` |

## Ownership rule

Keep each fact in one layer:

```text
SKILL.md
= route the Agent

references/*.md
= semantics, boundaries, and developer contracts

references/element-contracts/
= default → exception → real adjustment-surface status

references/template-knowledge/
= scientific template recommendation knowledge

src/axiomfig/resources/
= executable visual defaults

src/axiomfig/templates/
= public scientific grammars and data contracts

src/axiomfig/*.py
= deterministic runtime implementation
```

Do not copy numeric style truth into Markdown, turn benchmark-only behavior into public API, or add a
second figure specification beside Figure Intent.
