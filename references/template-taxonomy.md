# Template taxonomy and registry

## 1. Terms

A **family** is one scientific graphical grammar such as `scatter` or `heatmap`. A **variant** is a
genuinely different canonical form inside that family. A **template ID** is the stable
`<family>/<variant>` pair. Palette, marker, typography, or figure width changes do not create a new
variant.

`layouts` is separate. It composes registered Primary/Auxiliary Axes through the deterministic
Round 05 engine and never changes the scientific identity of a panel.

## 2. Discovery and execution

```plain
templates/index.yaml
        ↓
family/contract.yaml
        ↓
explicit family BUILDERS mapping
        ↓
deterministic runtime and validation
```

`index.yaml` stays small: version, family, variant, geometry, and public/layout classification.
The family contract records input shape and required scientific semantics. Explicit Python imports
resolve the builder without dynamic import magic, plugins, metaclasses, a DSL, or a schema
framework.

## 3. Registry invariants

Registry IDs are globally unique. Every registered family has a contract; every variant has one
builder; contracts, registry, and builder maps must agree exactly. Public scientific templates
produce Gallery artifacts; registered layouts do not.

For each public ID, Gallery contains exactly:

```plain
gallery/sans/<family>/<variant>.pdf
gallery/sans/<family>/<variant>.png
gallery/serif/<family>/<variant>.pdf
gallery/serif/<family>/<variant>.png
```

Technical Tectonic probes live under `gallery/technical/latex/` and are not templates. The
validator rejects missing artifacts, orphan artifacts, missing builders/contracts, duplicate IDs,
and old numbered flat files.

## 4. Knowledge and execution boundary

The taxonomy states what exists and what inputs it accepts. The separate
`references/template-knowledge/index.yaml` routes unresolved scientific intent to one concise topic
file; recommendation prose never enters the registry. `references/figure-intent.md` defines the
validated data-facing execution record. This separation lets an Agent read the registry, one
contract, and at most one knowledge topic instead of loading the entire repository.
