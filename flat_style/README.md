# `flat_style`

A Poetry-managed comparison project using the conventional **flat layout**.

```text
flat_style/
├── pyproject.toml
├── flat_style/
│   └── pipelines/
└── tests/
```

This directory has two distinct import paths, depending on how code is run:

```python
# Poetry-installed project, or an IDE whose import root is <monorepo-root>/flat_style
from flat_style.pipelines.retro_encabulator.instruments import (
    unilateral_phase_detractor,
)

# Direct source execution from a monorepo-root import (including a Databricks Git folder)
from flat_style.flat_style.pipelines.retro_encabulator.instruments import (
    unilateral_phase_detractor,
)
```

The second path is what the included Databricks notebook uses.

## Pros

- The package is directly below the project root, so it can be imported without installation when that root is already on Python's import path.
- Fits the spike's team constraints: no `%pip install`, no wheel installation, and no notebook-level `sys.path` change.
- The source-tree import `flat_style.flat_style...` works from the Databricks-provided monorepo-root import path, including sparse checkouts that contain `flat_style`.
- A local IDE opened at the monorepo root can use that same source-tree import.

## Cons

- The source-tree import (`flat_style.flat_style...`) differs from the Poetry-installed package API (`flat_style...`). A single import statement cannot cover both contexts with this project/package naming structure and the stated constraints.
- Python may import the working-tree package merely because the interpreter's current directory is the project root. This can hide packaging mistakes that would only appear after a distribution is built.
- Project files (tests, configuration, and helper scripts) share the import root with application source.
- It has weaker isolation than the `src` layout and is less useful for proving that only declared package content is importable.

## Tradeoff

Databricks Git folders add the **monorepo root** to `sys.path`, yielding this lookup:

```text
<monorepo-root>/                         # import root
└── flat_style/                           # first `flat_style` component
    └── flat_style/                       # second `flat_style` component: Poetry package
        └── pipelines/
```

Consequently, direct source execution from a Databricks Git folder must use `flat_style.flat_style...`. Sparse checkout can ensure that the `flat_style` tree is present, but it does not alter this lookup.

The shorter `flat_style.pipelines...` is correct only after Poetry installs the project, or when a local IDE explicitly treats `<monorepo-root>/flat_style` as the import root. Under the team's no-install/no-path-configuration constraints, it is not the correct portable import for this nested project structure.

If a consistent public import (`flat_style.pipelines...`) is required in both Databricks source execution and local IDE source execution without installation or import-root configuration, the import package must instead be directly beneath the monorepo root. That would mean eliminating the outer `flat_style` project directory or giving it a different name, which trades away the usual independently managed monorepo-project structure.

For projects intended for standard packaging and deployment, the [`src_style`](../src_style/README.md) layout remains preferable.

For background, see PyPA's [src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).
