# HyprDroid-Packages

Локальный черновик будущего репозитория. `hello-tile` показывает счётчик с Increment и Reset и хранит значение через Tile API. Публикация и запуск внешних тайлов требуют отдельных решений владельца.

```sh
python3 tools/package.py build modules/hello-tile dist
python3 -m zipfile -t dist/hello-tile-1.0.0.hyp
```

[Публикация и формат](docs/PUBLISH.md)

## Official modules

| Module | Package ID | Version | Plugin API | Features | Permissions | Install |
| --- | --- | --- | --- | --- | --- | --- |
| Hello Tile | `hello-tile` | 1.0.0 | 1 | Counter, Increment, Reset | `ui.tile` | `hypr install hello-tile` |
| Clock Tile | `clock-tile` | 1.0.0 | 2 | Local date/time, 12/24-hour format, timer | `ui.tile`, `system.time`, `state.local` | `hypr install clock-tile` |
| Battery Tile | `battery-tile` | 1.0.0 | 2 | Charge, charging status, progress, Refresh | `ui.tile`, `system.battery` | `hypr install battery-tile` |

Run `hypr repo update` before installing. Add the installed module with `hypr tile add <id>`.
`hypr remove <id>` stops a module but keeps state for retained tiles.
Reinstall the same trusted module to restore those tiles. Permanently remove a tile with
`hypr tile remove <tile-id>` to clear its state.

Plugin API v2 supplies a validated declarative tree, typed events, a bounded per-tile
state store, foreground timers and permission-filtered Core snapshots. Lua scripts have
no direct Android API, filesystem or network access.
