# Python layouts in a Databricks monorepo

This document records the findings from comparing Python package layouts in a Poetry-managed monorepo used through Databricks Git folders and local IDEs.

## Goals and team constraints

The repository contains multiple independently managed Poetry projects:

```text
monorepo/
├── project_a/
│   └── pyproject.toml
├── project_b/
│   └── pyproject.toml
└── ...
```

For this spike, the team—not Databricks—imposed these constraints:

- Do not use `%pip install` notebook magic.
- Do not install project wheels.
- Do not modify `sys.path` in notebook code.

Databricks supports all of those techniques; this spike intentionally excludes them.

## Distribution names, import names, and source containers

These names are related but independent:

- **Distribution/project name:** metadata in `pyproject.toml`, such as `data-platform`. Package managers use it.
- **Import package name:** the directory imported by Python, such as `data_platform`. Python code uses it.
- **Source container:** an optional directory, conventionally named `src`, that contains import packages but is not itself imported.

Changing this:

```toml
[tool.poetry]
name = "data-platform"
```

does not determine the Python import name. The `packages` declaration and directory structure do that.

## Flat layout

A conventional flat-layout project places the import package directly under the Poetry project root:

```text
project_a/
├── pyproject.toml
├── project_a/
│   ├── __init__.py
│   └── pipelines/
└── tests/
```

Poetry configuration:

```toml
[tool.poetry]
name = "project-a"
packages = [
    { include = "project_a" }
]
```

When `project_a/` (the outer Poetry project directory) is an import root, the public import is:

```python
from project_a.pipelines import example
```

### Flat-layout advantages

- Source can be imported without installing the project when the project root is already a Python import root.
- Convenient for notebook-first and application development.
- A good fit for a per-project Databricks Git folder because its Git root and Poetry project root are the same.
- Simple relationship between the Poetry project root and import package.

### Flat-layout disadvantages

- Running from the project root can accidentally import the working tree instead of testing an installed distribution.
- Tests may pass even when packaging configuration omits files from a built distribution.
- Project metadata, tests, scripts, and source all share an import root.
- In a monorepo, the outer project directory adds a source-tree import component when only the monorepo root is available.

For example:

```text
monorepo/                 # import root
└── project_a/            # first `project_a` component: project directory
    └── project_a/        # second `project_a` component: import package
        └── pipelines/
```

Direct execution from the monorepo root resolves:

```python
from project_a.project_a.pipelines import example
```

The shorter `project_a.pipelines...` import works when the outer `project_a/` directory is an import root or the project is installed.

## `src` layout

A conventional `src`-layout project places import packages under a non-package source container:

```text
project_a/
├── pyproject.toml
├── src/
│   └── project_a/
│       ├── __init__.py
│       └── pipelines/
└── tests/
```

Poetry configuration:

```toml
[tool.poetry]
name = "project-a"
packages = [
    { include = "project_a", from = "src" }
]
```

The intended installed import is:

```python
from project_a.pipelines import example
```

### `src`-layout advantages

- Separates importable source from project metadata, tests, and tools.
- Prevents accidental import of the working tree merely because Python runs from the project root.
- Encourages tests to exercise the installed package.
- Exposes packaging mistakes earlier, such as files omitted from the distribution.
- Is generally preferable for reusable libraries and projects built and deployed as distributions.

### `src`-layout disadvantages

- The clean package import normally requires installation, usually an editable installation during development.
- Direct source execution requires `<project>/src` to be a Python import root.
- Databricks does not recursively discover nested `src/` directories or interpret `pyproject.toml` to create import roots.
- It conflicts with this spike's team constraints unless an external environment configuration exposes `<project>/src`.

From only the monorepo root, the direct source-tree path is structurally:

```python
from project_a.src.project_a.pipelines import example
```

That path is an accidental traversal of repository directories, not the intended package API.

## A directory named `src` is not necessarily a `src` layout

The production `data_platform` project currently resembles:

```text
janus-databricks/
└── data_platform/
    ├── pyproject.toml
    └── src/
        ├── __init__.py
        └── pipelines/
```

with:

```toml
packages = [
    { include = "src" }
]
```

This declares `src` as the actual import package. It is therefore a **flat-layout project whose import package is named `src`**, not a conventional `src` layout. Its packaged API is:

```python
from src.pipelines import example
```

The word `src` is only conventional when it is a non-package container around another import package.

A correctly named flat-layout migration would be:

```text
data_platform/
├── pyproject.toml
└── data_platform/
    ├── __init__.py
    └── pipelines/
```

with:

```toml
[tool.poetry]
name = "data-platform"
packages = [
    { include = "data_platform" }
]
```

The intended import would then be:

```python
from data_platform.pipelines import example
```

From a monorepo-root-only import path, direct source execution would instead see `data_platform.data_platform...`.

A conventional `src`-layout migration would add another level:

```text
data_platform/
├── pyproject.toml
└── src/
    └── data_platform/
        ├── __init__.py
        └── pipelines/
```

with:

```toml
packages = [
    { include = "data_platform", from = "src" }
]
```

## How Python resolves these imports

Python searches the entries in `sys.path`. For an absolute import, it looks for the first component immediately beneath each import root, then resolves the remaining components below it. Python does not recursively search arbitrary descendants for matching packages.

Shell `PATH` and Python `sys.path` are different:

- `PATH` locates executable programs.
- `sys.path` locates Python modules and packages.

Changing shell `PATH` does not make a Python package importable.

Directories without `__init__.py` can participate as PEP 420 implicit namespace packages. That is why plain Python can traverse the outer project directories in imports such as:

```python
from flat_style.flat_style.pipelines import example
from src_style.src.src_style.pipelines import example
```

when the monorepo root is an import root.

## Databricks Git-folder behavior

A Databricks Git folder is a workspace clone of a Git repository. It provides source-control and workspace-file behavior; it does not install nested Poetry projects.

For Databricks Runtime 11.3 LTS and later, Databricks automatically adds the Git-folder repository root to Python's `sys.path`. For Runtime 14.0 and later, the directory containing the running notebook or script is also the default current working directory for locally executed code.

Given:

```text
/Workspace/Users/<user>/<git-folder>/       # Git-folder root
├── flat_style/
│   └── flat_style/
└── src_style/
    └── src/
        └── src_style/
```

Git-folder-root imports are:

```python
from flat_style.flat_style.pipelines import example
from src_style.src.src_style.pipelines import example
```

Databricks does not use the nested Poetry manifests to transform those into installed-style imports.

### Sparse checkout

Databricks supports cone-mode sparse checkout. It determines which repository paths are present in the workspace clone. It does not normally:

- flatten or relocate selected directories,
- reinterpret `pyproject.toml`,
- install a project,
- or add every selected project's `src/` directory to `sys.path`.

A cone such as `data_platform` recursively selects that directory while retaining repository-relative paths and root-level files.

However, the production sparse-checkout workflow has been observed to resolve `from src.pipelines...`. That proves `data_platform/` is effectively an import root in that execution context, whether through the notebook CWD, Databricks behavior, deployment configuration, or another path entry. Confirm the cause rather than attributing it to Poetry:

```python
import importlib.util
import os
import sys

spec = importlib.util.find_spec("src")

print("CWD:", os.getcwd())
print("src origin:", spec.origin if spec else None)
print("src search locations:", spec.submodule_search_locations if spec else None)
print("sys.path:")
print(*sys.path, sep="\n")
```

The expected project origin is:

```text
.../<git-folder>/data_platform/src/__init__.py
```

If `.../<git-folder>/data_platform` appears in `sys.path`, it explains the short `src.pipelines...` import. This diagnostic also protects against accidentally importing an unrelated installed package named `src`.

## Why local execution and an editor can disagree

There are three separate resolution systems:

1. **Databricks runtime:** Python uses the `sys.path` assembled by Databricks.
2. **Local runtime:** Python uses the interpreter, CWD, environment, and actual `sys.path` of the process.
3. **Editor analysis:** an indexer/language server uses editor workspace roots, configured source roots, selected interpreters, and its own package model.

An editor accepting an import does not prove that Databricks or plain Python can import it. Conversely, CPython may resolve implicit namespace packages that an editor cannot navigate because of workspace or module boundaries.

A useful local compatibility check is plain Python started with the monorepo root as its CWD/import root and no project installed into the environment.

## PyCharm behavior

PyCharm distinguishes several concepts:

- **Content root:** files owned and indexed by a module/project.
- **Source root:** starting point used by the static indexer for import resolution.
- **Module/project SDK:** interpreter and dependencies associated with files in that module.
- **Module dependency:** visibility from one module to another; it does not create a new package hierarchy.

Attaching each Poetry project to a repository project is useful because PyCharm can associate files with the correct per-project environment. That is a reasonable monorepo workflow.

### The attached-module limitation

The same subtree cannot be modeled cleanly as both:

```text
<monorepo>/flat_style/          # child module content/import root
```

and:

```text
<monorepo>/                     # parent source root
└── flat_style/                 # package component beneath parent root
```

PyCharm content roots cannot overlap in the way required to preserve both views. When `flat_style/` is the attached child module's content root:

- PyCharm naturally understands `flat_style.pipelines...` through that project and its Poetry environment.
- The outer `flat_style/` cannot necessarily be marked as a namespace package; it is a content root rather than a package beneath the parent source root.
- The repository root cannot simultaneously own the same subtree as a source root.
- A module dependency does not synthesize `flat_style.flat_style...` for static analysis.

Plain CPython can still execute `flat_style.flat_style...` from the monorepo root because it follows `sys.path` and PEP 420 namespace-package rules. Therefore, PyCharm editor navigation can disagree with the built-in Python console even when the console matches Databricks.

### PyCharm configuration choices

There is no perfect classic-module configuration that provides both per-file Poetry environments and exact monorepo-root static resolution.

#### Attached Poetry modules

Benefits:

- automatic per-file environment selection,
- accurate dependency completion for each project,
- good navigation for installed/project-root imports.

Cost:

- the indexer may not navigate Databricks source-tree imports such as `flat_style.flat_style...`.

#### One monorepo module

Benefits:

- the repository root can be the sole content/source root,
- static resolution more closely matches Databricks Git-folder imports.

Cost:

- one interpreter is associated with the repository module,
- automatic per-project interpreter selection is lost.

#### Separate IDE windows

Benefits:

- each Poetry project has its own interpreter and clean project-root imports.

Cost:

- the editor no longer models direct monorepo-root execution,
- cross-project work is less convenient.

### Editable installations can mask import behavior

A normal `poetry install` installs the root project, commonly in editable form. PyCharm indexes the selected interpreter, so it may resolve the clean package import even when direct source execution from the monorepo root cannot.

For a local environment intended to test Databricks source behavior, create it without the root package:

```shell
poetry install --no-root
```

If the root package was already installed, recreate the environment or uninstall it first; `--no-root` does not necessarily remove a prior installation.

## VS Code behavior

The VS Code Python Environments extension supports **Python Projects** for monorepos. A project folder can be associated with a particular environment, which is then used for running, debugging, terminals, and tests.

This is conceptually similar to attached PyCharm projects. It is useful for independently managed Poetry projects, but it can cause the project folder to be treated as the operational context rather than reproducing Databricks' monorepo-root import behavior.

Important documented limitations:

- Pylance currently uses one interpreter per workspace rather than fully honoring multiple Python Projects for analysis.
- Jupyter kernel selection uses a separate/older environment API and can differ from Python Project assignments.
- For independent Pylance analysis with different interpreters, use a VS Code multi-root workspace so each Poetry project is a separate workspace folder.

The same tradeoff applies:

- A project folder as a workspace root gives clean `package...` analysis.
- The monorepo as the sole workspace root more closely resembles Databricks source traversal.
- A multi-root workspace is convenient for development but does not prove imports work from the Databricks Git-folder root.

Teams should commit a `.code-workspace` or `.vscode/settings.json` that deliberately chooses the desired model, and validate Databricks imports separately.

## Zed behavior

Zed uses Python **toolchains**. The selected toolchain controls:

- the interpreter passed to built-in language servers such as basedpyright,
- Python tasks and tests,
- virtual-environment activation in new integrated terminals,
- dependency resolution for language tooling.

Zed automatically discovers common virtual environments and allows manual toolchain selection. Compared with PyCharm attached modules, Zed does not currently document equivalent automatic per-file switching among multiple Poetry environments inside one worktree.

Practical options for a Poetry monorepo are:

1. Open one Poetry project as the Zed worktree when focused on that project.
2. Open the monorepo and manually select the relevant toolchain.
3. Define project-specific tasks that invoke Poetry with an explicit project directory.
4. Use a shared development environment if project dependency sets are compatible.
5. Put basedpyright settings in each `pyproject.toml` or `pyrightconfig.json`, while recognizing that active toolchain selection remains an editor concern.

As with PyCharm and VS Code, a language server can resolve packages from the selected environment that direct Databricks source execution cannot. Confirm runtime compatibility with plain Python and Databricks diagnostics.

## Recommendations

### Monorepo with independently managed projects

The conventional packaging recommendation is a `src` layout per project:

```text
monorepo/
├── project_a/
│   ├── pyproject.toml
│   └── src/
│       └── project_a/
└── project_b/
    ├── pyproject.toml
    └── src/
        └── project_b/
```

Use this when projects are installed in development, tests, and deployment. It provides the strongest packaging isolation and least ambiguous public APIs.

Under this team's no-install/no-path-configuration constraints, a conventional `src` layout is not directly compatible with Databricks Git-folder source imports. A correctly named flat layout is the pragmatic alternative when the relevant Poetry project root is reliably available as an import root.

Avoid naming an import package `src`.

### Per-project repositories

A flat layout is a natural fit for a Databricks notebook/application repository under the team constraints:

```text
project-repo/             # Git root and project import root
├── pyproject.toml
└── data_platform/
```

Both local project-root execution and Databricks can use:

```python
from data_platform.pipelines import example
```

For reusable libraries or projects deployed as distributions, prefer a `src` layout and install the package.

### Public import design

Do not treat doubled source-tree imports as desirable public APIs:

```python
from data_platform.data_platform...
from project_a.src.project_a...
```

They expose repository nesting rather than the package contract. Prefer:

```python
from data_platform.pipelines import example
```

and establish an execution/deployment contract that provides the corresponding project root or installed package.

## Validation checklist

For each project and execution environment, answer these independently:

1. What is the intended distribution name?
2. What is the intended import package name?
3. Which exact directories are in runtime `sys.path`?
4. What is the notebook or process CWD?
5. Is the project installed, including as an editable installation?
6. Which file does the import resolve to?
7. Is the editor using the same interpreter and import roots as runtime?
8. Does sparse checkout only select files, or is another mechanism exposing the project directory?

Useful diagnostic:

```python
import importlib.util
import os
import sys

package = "data_platform"  # or the current package name
spec = importlib.util.find_spec(package)

print("CWD:", os.getcwd())
print("spec:", spec)
print("origin:", spec.origin if spec else None)
print("search locations:", spec.submodule_search_locations if spec else None)
print("sys.path:")
print(*sys.path, sep="\n")
```

The resolved origin is more reliable evidence than whether an IDE underlines an import.

## References

- [PyPA: src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Databricks: Create and manage Git folders](https://docs.databricks.com/aws/en/repos/git-operations-with-repos)
- [Databricks: Work with Python and R modules](https://docs.databricks.com/aws/en/files/workspace-modules)
- [PyCharm: Configuring project structure](https://www.jetbrains.com/help/pycharm/configuring-project-structure.html)
- [VS Code: Python environments](https://code.visualstudio.com/docs/python/environments)
- [Zed: Python](https://zed.dev/docs/languages/python)
