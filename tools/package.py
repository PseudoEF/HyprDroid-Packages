#!/usr/bin/env python3
"""Build reproducible sample packages and prepare detached Ed25519 signatures."""
import argparse
import base64
import hashlib
import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

DOMAIN = b"HyprDroid catalog v1\n"
REPO = "PseudoEF/HyprDroid-Packages"
RELEASE = f"https://github.com/{REPO}/releases/download"
ROOT = Path(__file__).resolve().parents[1]

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

def strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate key: {key}")
        result[key] = value
    return result

def read_json(data):
    return json.loads(data, object_pairs_hook=strict_object)

def validate_id(value):
    if not isinstance(value, str) or len(value) > 80 or not re.fullmatch(r"[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*", value):
        raise ValueError("Invalid package ID")

def validate_version(value):
    if not isinstance(value, str) or not re.fullmatch(r"(0|[1-9][0-9]{0,9})(\.(0|[1-9][0-9]{0,9})){2}", value):
        raise ValueError("Invalid package version")
    if any(int(component) > 2147483647 for component in value.split(".")):
        raise ValueError("Version component exceeds the Core limit")

def validate_manifest(manifest):
    fields = {"id", "version", "apiVersion", "runtime", "entry", "permissions", "dependencies"}
    if not isinstance(manifest, dict) or set(manifest) != fields:
        raise ValueError("Invalid manifest fields")
    if type(manifest["apiVersion"]) is not int or manifest["apiVersion"] != 1 or manifest["runtime"] != "lua":
        raise ValueError("Unsupported runtime or API")
    validate_id(manifest["id"])
    validate_version(manifest["version"])
    entry = manifest["entry"]
    if not isinstance(entry, str) or len(entry) > 80 or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\.lua", entry):
        raise ValueError("The scaffold expects a Lua entry in the module root")
    permissions = manifest["permissions"]
    allowed = {"terminal.print", "system.device", "system.battery", "ui.window", "ui.tile"}
    if not isinstance(permissions, list) or not all(isinstance(p, str) and p in allowed for p in permissions):
        raise ValueError("Invalid permissions")
    if len(set(permissions)) != len(permissions):
        raise ValueError("Duplicate permission")
    dependencies = manifest["dependencies"]
    if not isinstance(dependencies, dict) or len(dependencies) > 16 or manifest["id"] in dependencies:
        raise ValueError("Invalid dependencies")
    for module_id, version in dependencies.items():
        validate_id(module_id)
        validate_version(version)

def build(module, output):
    manifest = read_json((module / "manifest.json").read_bytes())
    validate_manifest(manifest)
    module_id, version, entry = (manifest[field] for field in ("id", "version", "entry"))
    source = module / entry
    if source.is_symlink():
        raise ValueError("Symlink entries are forbidden")
    data = source.read_bytes()
    if not data or len(data) > 16 * 1024 or b"\x00" in data or data.startswith(b"\x1b"):
        raise ValueError("Expected a bounded textual Lua source")
    data.decode("utf-8")
    output.mkdir(parents=True, exist_ok=True)
    target = output / f"{module_id}-{version}.hyp"
    with zipfile.ZipFile(target, "w") as archive:
        for name, content in (("manifest.json", encode(manifest)), (entry, data)):
            archive.writestr(zipfile.ZipInfo(name), content, compress_type=zipfile.ZIP_STORED)
    return target

def sign(data, key):
    path = key.resolve(strict=True)
    if path.is_relative_to(ROOT):
        raise ValueError("Keep the private key outside the repository")
    with tempfile.TemporaryDirectory() as folder:
        message = Path(folder) / "message"
        message.write_bytes(data)
        return subprocess.check_output(["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", str(path), "-in", str(message)]).hex()

def make_catalog(args):
    records = []
    for artifact in args.artifacts:
        data = artifact.read_bytes()
        with zipfile.ZipFile(artifact) as archive:
            manifest = read_json(archive.read("manifest.json"))
            validate_manifest(manifest)
        module_id, version = manifest["id"], manifest["version"]
        filename = f"{module_id}-{version}.hyp"
        if artifact.name != filename:
            raise ValueError(f"Expected artifact name {filename}")
        records.append({
            "manifest": manifest, "sha256": hashlib.sha256(data).hexdigest(),
            "signature": sign(data, args.key),
            "url": f"{RELEASE}/{module_id}-v{version}/{filename}", "status": "active",
        })
    if not (1 <= args.revision <= 2147483647) or not re.fullmatch(r"[a-z0-9-]{1,64}", args.key_id):
        raise ValueError("Invalid revision or key ID")
    previous = read_json(args.previous_payload.read_bytes()) if args.previous_payload else None
    by_id = {item["manifest"]["id"]: item for item in records}
    if len(by_id) != len(records) or len(by_id) > 64:
        raise ValueError("Duplicate IDs or too many packages")
    if previous:
        if previous["repository"] != REPO or args.revision <= previous["revision"]:
            raise ValueError("New catalogue revision must increase")
        for old in previous["packages"]:
            module_id = old["manifest"]["id"]
            new = by_id.get(module_id)
            if new is None:
                by_id[module_id] = old
                continue
            old_version, new_version = (tuple(map(int, entry["manifest"]["version"].split("."))) for entry in (old, new))
            if new_version < old_version or (new_version == old_version and new != old):
                raise ValueError(f"Cannot change or roll back the published version of {module_id}")
    for module_id in args.revoke:
        if module_id not in by_id:
            raise ValueError(f"Cannot revoke unknown package {module_id}")
        by_id[module_id] = {**by_id[module_id], "status": "revoked"}
    if len(by_id) > 64:
        raise ValueError("Catalogue contains more than 64 packages")
    payload = encode({"schemaVersion": 1, "repository": REPO, "revision": args.revision,
                      "packages": [by_id[key] for key in sorted(by_id)]})
    if len(payload) > 64 * 1024:
        raise ValueError("Catalogue payload exceeds the Core limit")
    envelope = {"keyId": args.key_id, "payload": base64.b64encode(payload).decode(),
                "signature": sign(DOMAIN + payload, args.key)}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "catalog.json").write_bytes(encode(envelope))
    (args.output / "catalog.payload.json").write_bytes(payload)

def main():
    cli = argparse.ArgumentParser()
    commands = cli.add_subparsers(required=True)
    compile_cmd = commands.add_parser("build")
    compile_cmd.add_argument("module", type=Path)
    compile_cmd.add_argument("output", type=Path)
    compile_cmd.set_defaults(run=lambda args: print(build(args.module, args.output)))
    catalog = commands.add_parser("catalog")
    catalog.add_argument("--key", type=Path, required=True)
    catalog.add_argument("--key-id", required=True)
    catalog.add_argument("--revision", type=int, required=True)
    catalog.add_argument("--previous-payload", type=Path)
    catalog.add_argument("--revoke", action="append", default=[])
    catalog.add_argument("output", type=Path)
    catalog.add_argument("artifacts", type=Path, nargs="*")
    catalog.set_defaults(run=make_catalog)
    args = cli.parse_args()
    args.run(args)

if __name__ == "__main__":
    main()
