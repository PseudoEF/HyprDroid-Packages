# HyprDroid-Packages

Каталог модулей HyprDroid и инструменты подготовки подписанных релизов. `hello-tile` показывает счётчик с Increment и Reset и хранит значение через Tile API. Публикация регулируется отдельной политикой. Внешнее исполнение Lua в Core отключено.

```sh
python3 tools/package.py build modules/hello-tile dist
python3 -m zipfile -t dist/hello-tile-1.0.0.hyp
```

[Публикация и формат](docs/PUBLISH.md)
