# Modular TUI Host

This repository contains a reference implementation of a **modular terminal
user interface (TUI) framework**. The design follows the contract‑first
approach described in the development and implementation plan: each
feature lives in its own **module** with a minimal manifest and a
factory function. A lightweight **host** discovers these modules,
merges their metadata and provides a simple runtime for users to
explore routes, trigger commands and view state.

## Project Structure

- `schema/tui.module.schema.json` – JSON Schema used to validate
  module manifests.
- `src/host/` – Host runtime, including discovery, manifest loading,
  registry merging, a simple state store and the entry point for
  launching the TUI.
- `src/modules/` – Example modules implementing the contract. Each
  resides in its own folder with a manifest and Python package.
- `tests/` – Unit and snapshot tests that exercise validation, merging
  logic and rendering.

## Running the Host

To run the TUI host manually, point it at the `src/modules` directory:

```sh
python -m host.app ../src/modules
```

You will be presented with a list of routes and commands. Select a
route by number or type a command/keybinding to trigger it. Press `q`
to exit.

## Writing Your Own Module

1. Create a new subdirectory under `src/modules/<your_module>`.
2. Add a `tui.module.yaml` manifest describing routes, commands and
   keybindings. Use the provided JSON Schema as a reference.
3. Create a Python package under `src/modules/<your_module>/<your_module>`
   with a `module.py` that defines a `build_module(host_api)` function.
4. Implement reducers, initial state, view functions and command
   callbacks. Use `host_api.dispatch` to send actions back to the host.

For more details see the individual module documentation in
`docs/modules/`.