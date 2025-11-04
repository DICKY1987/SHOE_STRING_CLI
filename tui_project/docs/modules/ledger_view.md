# ledger_view Module

The **ledger_view** module provides a simple table of ledger entries. It
demonstrates the use of reducers, commands and keybindings within the
modular TUI framework.

## Manifest

The manifest declares a single route `ledger` mounted in the `main`
slot, a command `ledger.reload` and a keybinding `r` mapped to that
command.

## Behaviour

On initialisation the module populates its state with three static
entries. The **Reload** command simulates fetching new data by
generating random amounts for each entry. The view function renders
the state as a simple table with headings and borders.

## Files

- `tui.module.yaml` – Manifest conforming to the contract schema.
- `ledger_view/module.py` – Implementation of the module. Contains
  reducer, view and command definitions.