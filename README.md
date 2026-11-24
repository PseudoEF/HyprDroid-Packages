# HyprDroid-Packages

Публичный репозиторий официальных модулей HyprDroid. [Подписанный каталог ревизии 2](https://github.com/PseudoEF/HyprDroid-Packages/releases/tag/catalog-v2) содержит модули API v1 и v2. Для старого Core доступен [совместимый каталог v1](https://github.com/PseudoEF/HyprDroid-Packages/releases/tag/catalog-v1).

```sh
python3 tools/package.py build modules/hello-tile dist
python3 -m zipfile -t dist/hello-tile-1.0.0.hyp
```

[Публикация и формат](docs/PUBLISH.md)

## Official modules

| Module | Package ID | Version | Plugin API | Features | Permissions | Install |
| --- | --- | --- | --- | --- | --- | --- |
| [Hello Tile](https://github.com/PseudoEF/HyprDroid-Packages/releases/tag/hello-tile-v1.0.0) | `hello-tile` | 1.0.0 | 1 | Counter, Increment, Reset | `ui.tile` | `hypr install hello-tile` |
| [Clock Tile](https://github.com/PseudoEF/HyprDroid-Packages/releases/tag/clock-tile-v1.0.0) | `clock-tile` | 1.0.0 | 2 | Local date/time, 12/24-hour format, timer | `ui.tile`, `system.time`, `state.local` | `hypr install clock-tile` |
| [Battery Tile](https://github.com/PseudoEF/HyprDroid-Packages/releases/tag/battery-tile-v1.0.0) | `battery-tile` | 1.0.0 | 2 | Charge, charging status, progress, Refresh | `ui.tile`, `system.battery` | `hypr install battery-tile` |

Run `hypr repo update` before installing. Add the installed module with `hypr tile add <id>`.
`hypr remove <id>` stops a module but keeps state for retained tiles.
Reinstall the same trusted module to restore those tiles. Permanently remove a tile with
`hypr tile remove <tile-id>` to clear its state.

Plugin API v2 supplies a validated declarative tree, typed events, a bounded per-tile
state store, foreground timers and permission-filtered Core snapshots. Lua scripts have
no direct Android API, filesystem or network access.
