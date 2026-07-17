# spike-janus-databricks-sdlc

DE-9081

## How Databricks Git folders fit this spike

A Databricks Git folder is a clone of a remote Git repository stored in the Databricks workspace. It is created from **Workspace** > **Create** > **Git folder** (or with `git clone` from the Databricks web terminal), and it tracks the cloned repository's branches and changes. In a workspace, a clone is typically located under a path such as:

```text
/Workspace/Users/<your-email>/<parent-folder>/<git-folder-name>
```

The Git folder is source-control/workspace storage; it is **not** a Python package installation mechanism. Cloning this monorepo makes the checked-out files, notebooks, and `pyproject.toml` files available in the workspace, but it does not install its Poetry projects, build wheels, or automatically expose every nested project's `src/` directory as a Python import root.

Databricks recommends that each collaborator create their own Git folder and work on their own branch. Git operations are performed against that workspace clone: pull updates the checked-out files, while commit and push publish local changes. Pulling upstream changes clears notebook state, so results should not be treated as durable notebook artifacts.

### Sparse checkout

Databricks supports optional **cone-mode sparse checkout** when creating a Git folder. It is a client-side Git setting that limits the clone to selected directory subtrees—useful when a monorepo exceeds Git-folder size limits. A cone pattern such as:

```text
src_style
```

recursively includes the contents of `src_style` and also includes files immediately under the monorepo root. Multiple patterns can be specified. The patterns can later be edited in Git-folder settings, but a sparse checkout created in this mode cannot be converted back to a non-sparse checkout.

Sparse checkout determines **which paths are present** in the clone. It preserves those paths' relative layout: it does not move `src_style/src/src_style` to the Git-folder root, configure `PYTHONPATH`, or otherwise alter Python import resolution.

See Databricks' [Create and manage Git folders](https://docs.databricks.com/aws/en/repos/git-operations-with-repos) documentation for the supported Git workflow, permissions, sparse-checkout settings, and limitations.

## Databricks Git-folder import constraints

This spike compares Python project layouts for projects inside a monorepo cloned as a Databricks Git folder.

The current constraints are:

- Do not use `%pip install` notebook magic.
- Do not install a `.whl`.
- Do not modify `sys.path` in notebook code.

A shell `PATH` entry only locates executables; it does **not** make Python packages importable. Python imports are resolved from `sys.path` (which can be populated by an installed distribution, the interpreter's working/import root, or external `PYTHONPATH` configuration).

Sparse checkout controls which paths are cloned; it does not change their relative locations or make a project's `src/` directory importable. If the Databricks environment exposes only the monorepo root as an import root, a `src`-layout project still requires installation or an externally configured Python import root that points to `<project>/src`.

The projects in this repository demonstrate the tradeoff:

- [`src_style`](./src_style/README.md): conventional `src/` layout, preferred for package isolation and distribution correctness, but not directly importable under the constraints above.
- [`flat_style`](./flat_style/README.md): conventional flat layout, directly importable as `flat_style` when its project root is an import root, but with weaker isolation. A monorepo root alone is not enough when the project and package share the name `flat_style`.
