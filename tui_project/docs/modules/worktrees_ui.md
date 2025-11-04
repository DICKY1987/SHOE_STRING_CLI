# worktrees_ui Module

The **worktrees_ui** module lists git worktrees and allows the user to
refresh the list. It illustrates how navigation slots can be used and
how simple state updates can be implemented.

## Manifest

The manifest defines a single route `worktrees` mounted in the `nav`
slot, a command `worktrees.refresh` and a keybinding `w` to trigger
the refresh.

## Behaviour

State is initialised with two placeholder worktrees: `main` and
`feature`. When the refresh command is invoked a random extra entry
may be appended to demonstrate state mutation. The view renders the
names in a bulleted list.

## Files

- `tui.module.yaml` – Manifest conforming to the contract schema.
- `worktrees_ui/module.py` – Implementation of the module with reducer,
  view and command.