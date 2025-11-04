# TUI Architecture and Roadmap

## Overview

The TUI (Terminal User Interface) project provides a modular, extensible framework for building terminal-based applications. The architecture is designed around a host-module pattern where the host provides foundational utilities and the modules provide domain-specific functionality.

## Architecture

### Core Components

#### Host Layer (`src/host/`)

The host layer provides foundational utilities that all TUI modules can depend on:

- **formatting.py**: ANSI color and text formatting with TTY and NO_COLOR support
- **messages.py**: Consistent message display for info, warnings, errors, and success
- **progress.py**: Progress indicators and spinners for long-running operations
- **help_registry.py**: Centralized help system for registering and displaying help content
- **cli_parser.py**: Command-line argument parsing with argparse integration
- **navigation.py**: Route management and navigation history for multi-screen applications

#### Module Layer (`src/modules/`)

Modules are self-contained functional units that:
- Declare their capabilities via a manifest (`tui.module.yaml`)
- Register routes, commands, and help topics
- Integrate with the host utilities
- Can be loaded and unloaded dynamically

#### Registry and Discovery

- **manifest.py**: Loads and validates module manifests against the JSON schema
- **registry.py**: Maintains the global registry of loaded modules and their metadata
- **discovery.py**: Discovers and loads modules from the filesystem
- **store.py**: Manages persistent storage for module state and configuration

### Design Principles

1. **Standard Library Only**: All host utilities use only Python standard library to minimize dependencies
2. **TTY Awareness**: All output respects TTY detection and NO_COLOR environment variable
3. **Modularity**: Clear separation between host and module concerns
4. **Extensibility**: New modules can be added without modifying the core system
5. **Consistency**: Shared formatting, messaging, and navigation patterns across all modules

## Data Flow

```
User Input → CLI Parser → Navigator → Module Handler
                ↓              ↓
           Help Registry   Progress/Messages
                ↓              ↓
            Formatting ← Terminal Output
```

1. User invokes a command via CLI
2. CLI parser processes arguments and determines the target route/command
3. Navigator activates the appropriate module handler
4. Module performs its work, using progress/message utilities for feedback
5. Help can be requested at any point via the help registry
6. All output flows through formatting utilities respecting color support

## Roadmap

### Phase 1: Foundation (Current)
- [x] Core formatting utilities with NO_COLOR support
- [x] Message display utilities
- [x] Progress indicators and spinners
- [x] Help registry system
- [x] CLI parser integration
- [x] Navigation and routing
- [x] Documentation and conventions

### Phase 2: Enhanced Modules
- [ ] Expand ledger_view module with filtering and sorting
- [ ] Add worktrees_ui enhancements for branch management
- [ ] Implement module hot-reloading
- [ ] Add inter-module messaging

### Phase 3: Advanced Features
- [ ] Keyboard shortcut system
- [ ] Configuration file support
- [ ] Plugin API for external modules
- [ ] Module marketplace/discovery
- [ ] Automated testing framework for modules

### Phase 4: Performance and Polish
- [ ] Optimize module loading and discovery
- [ ] Add comprehensive error handling and recovery
- [ ] Implement logging and diagnostics
- [ ] Performance profiling and optimization

## Module Development

### Creating a New Module

1. Create module directory: `src/modules/my_module/my_module/`
2. Define manifest: `src/modules/my_module/tui.module.yaml`
3. Implement module logic in `module.py`
4. Register routes and help topics
5. Write tests in `tests/test_my_module.py`

### Module Structure

```
src/modules/my_module/
├── tui.module.yaml       # Manifest with metadata and routes
└── my_module/
    ├── __init__.py       # Package exports
    └── module.py         # Module implementation
```

### Best Practices

- Use host utilities for all output (formatting, messages, progress)
- Register comprehensive help content
- Handle errors gracefully with clear messages
- Support non-TTY environments
- Write tests that exercise all routes and commands
- Document module-specific conventions

## Testing Strategy

- **Unit Tests**: Test individual utilities and functions in isolation
- **Integration Tests**: Test module loading, registration, and interaction
- **Functional Tests**: Test complete user workflows end-to-end
- **Performance Tests**: Validate performance characteristics remain acceptable

## Security Considerations

- All module manifests are validated against a JSON schema
- Module discovery respects filesystem boundaries
- No dynamic code execution from untrusted sources
- All file operations use pathlib for path safety

## Future Considerations

- **Internationalization**: Support for multiple languages
- **Theming**: Customizable color schemes
- **Accessibility**: Screen reader support and alternative output modes
- **Distribution**: Packaging and distribution mechanisms
- **Versioning**: Semantic versioning for modules and host API
