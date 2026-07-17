# `flat_style`

A Poetry-managed comparison project using the conventional **flat layout**.

```text
flat_style/
├── pyproject.toml
├── flat_style/
│   └── pipelines/
└── tests/
```

Its intended public import is:

```python
from flat_style.pipelines.retro_encabulator.instruments import (
    unilateral_phase_detractor,
)
```

## Pros

- The package is directly below the project root, so it can be imported without installation when that root is already on Python's import path.
- Fits the spike's constraints: no `%pip install`, no wheel installation, and no notebook-level `sys.path` change.
- A Databricks environment that exposes the **`flat_style` project root** as an import root can import `flat_style` directly.
- Simple notebook-first workflow for source checked out alongside the notebook.

## Cons

- Python may import the working-tree package merely because the interpreter's current directory is the project root. This can hide packaging mistakes that would only appear after a distribution is built.
- Project files (tests, configuration, and helper scripts) share the import root with application source.
- It has weaker isolation than the `src` layout and is less useful for proving that only declared package content is importable.

## Tradeoff

Use this layout when direct source imports from a Databricks Git folder are a hard requirement and installing projects or configuring Python import roots is not available.

The relevant import root must be the project directory:

```text
<monorepo-root>/flat_style
```

The package is then directly beneath it:

```text
<monorepo-root>/flat_style/flat_style
```

A monorepo root alone does **not** make `flat_style.pipelines` available in this naming scheme: Python resolves `flat_style` to the outer project directory first. Sparse checkout may reduce the checked-out files, but it does not change this resolution; the package's placement beneath the existing import root enables the import.

For projects intended for standard packaging and deployment, the [`src_style`](../src_style/README.md) layout remains preferable.

For background, see PyPA's [src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).
