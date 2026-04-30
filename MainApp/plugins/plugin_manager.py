import json
import importlib.util
import sys
from pathlib import Path
from typing import Optional

_plugins: dict[str, object] = {}
_editor_actions: dict[str, list] = {}


def _get_plugins_dirs() -> list[Path]:
    if getattr(sys, 'frozen', False):
        return [Path(sys.executable).parent / "plugins"]
    return [Path(__file__).resolve().parent]


_plugins_dirs: list[Path] = _get_plugins_dirs()


def _find_plugin_dir(name: str) -> Path | None:
    for base in _plugins_dirs:
        d = base / name
        if d.is_dir() and (d / "plugin.json").exists():
            return d
    return None


def _find_init(plugin_dir: Path) -> Path | None:
    for name in ("__init__.py", "__init__.pyc"):
        p = plugin_dir / name
        if p.exists():
            return p
    return None


def discover_plugins() -> list[str]:
    seen: set[str] = set()
    names: list[str] = []
    for base in _plugins_dirs:
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name not in seen and (d / "plugin.json").exists():
                seen.add(d.name)
                names.append(d.name)
    return names


def load_plugin(name: str) -> Optional[object]:
    if name in _plugins:
        return _plugins[name]
    plugin_dir = _find_plugin_dir(name)
    if plugin_dir is None:
        return None
    init_file = _find_init(plugin_dir)
    if init_file is None:
        return None
    try:
        if str(plugin_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dir))
        spec = importlib.util.spec_from_file_location(
            f"plugins.{name}", str(init_file),
            submodule_search_locations=[str(plugin_dir)],
        )
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = f"plugins.{name}"
        sys.modules[f"plugins.{name}"] = mod
        spec.loader.exec_module(mod)
        plugin = mod.Plugin()
        if plugin.is_available():
            plugin.on_load()
        _plugins[name] = plugin
        return plugin
    except Exception as e:
        print(f"Plugin '{name}' load error: {e}")
        return None


def register_editor_action(editor_type: str, label: str, handler):
    _editor_actions.setdefault(editor_type, []).append({
        "label": label,
        "handler": handler,
    })


def get_editor_actions(editor_type: str) -> list[dict]:
    return list(_editor_actions.get(editor_type, []))


def load_all_plugins():
    for name in discover_plugins():
        load_plugin(name)


def get_plugin(name: str) -> Optional[object]:
    if name not in _plugins:
        return load_plugin(name)
    return _plugins.get(name)


def loaded_plugins() -> list[object]:
    return list(_plugins.values())


def plugin_info(name: str) -> Optional[dict]:
    plugin_dir = _find_plugin_dir(name)
    if plugin_dir is None:
        return None
    manifest = plugin_dir / "plugin.json"
    if not manifest.exists():
        return None
    return json.loads(manifest.read_text(encoding="utf-8"))
