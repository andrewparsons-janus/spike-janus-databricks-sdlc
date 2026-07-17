# `src_style`

A Poetry-managed example project using the conventional **`src` layout**.

```text
src_style/
├── pyproject.toml
├── src/
│   └── src_style/
│       └── pipelines/
└── tests/
```

Its intended public import is:

```python
from src_style.pipelines.retro_encabulator.instruments import (
    unilateral_phase_detractor,
)
```

## Pros

- Keeps importable source separate from project metadata, tests, notebooks, and tooling.
- Prevents an interpreter launched from the project root from accidentally importing the working tree instead of the installed distribution.
- Helps detect incomplete package configuration: tests exercise what is actually installed rather than incidental repository files.
- Scales naturally to independently versioned and distributed projects in a monorepo.

## Cons under this spike's Databricks constraints

A `src` layout intentionally does not make `src_style` importable when only the project or monorepo root is available to Python. The actual import root is:

```text
<monorepo-root>/src_style/src
```

The stated constraints rule out the standard ways to expose that directory:

- no `%pip install` notebook magic (including editable installs),
- no `.whl` installation,
- no notebook-level `sys.path` changes.

Sparse checkout alone does not change this; it only decides which repository paths are present. Shell `PATH` also does not help, because Python imports use `sys.path`, not `PATH`.

## Tradeoff

This is the preferred structure if the project will be built, tested, and deployed as a Python distribution. It can still be used with Databricks if the platform supplies an **external** import-root configuration for `<project>/src` (for example, a supported cluster/job `PYTHONPATH` setting). Whether that is acceptable depends on whether environment-level Python-path configuration is within the constraints.

Without either installation or an externally configured import root, use the [`flat_style`](../flat_style/README.md) comparison project instead.

For background, see PyPA's [src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).
