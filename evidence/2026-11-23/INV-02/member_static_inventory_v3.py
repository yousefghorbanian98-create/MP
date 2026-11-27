#!/usr/bin/env python3
"""Read-only, literal-level inventory for the PWA-01 member crosswalk (v3)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FEATURE_ROOT = ROOT / "mp-app/client/lib/features"
CLIENT_LIB = ROOT / "mp-app/client/lib"
TEST_ROOT = ROOT / "mp-app/client/test"
ROUTES = ROOT / "mp-app/backend/api/routes.json"
ROUTER = ROOT / "mp-app/client/lib/core/router.dart"
API_CALL = re.compile(
    r"(?P<receiver>\bapi\b|\bref\s*\.\s*(?:read|watch)\(\s*apiClientProvider\s*\))"
    r"\s*\.\s*(?P<method>get|post|put|patch|delete)\s*\(\s*"
    r"(?P<quote>['\"])(?P<path>.*?)(?P=quote)",
    re.IGNORECASE | re.DOTALL,
)
DART_INTERPOLATION = re.compile(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*")
ROUTE_PARAM = re.compile(r"\{[^}]+\}")


def normalized_route(path: str, *, request: bool) -> str:
    path = path.split("?", 1)[0]
    if request:
        path = DART_INTERPOLATION.sub("{}", path)
        if not path.startswith("/api/"):
            path = "/api/v1" + path
    else:
        path = ROUTE_PARAM.sub("{}", path)
    return path.rstrip("/") or "/"


def tree_digest(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> None:
    feature_files = sorted(FEATURE_ROOT.rglob("*.dart"))
    client_files = sorted(CLIENT_LIB.rglob("*.dart"))
    test_files = sorted(TEST_ROOT.glob("*_test.dart"))
    feature_dirs = sorted(path for path in FEATURE_ROOT.iterdir() if path.is_dir())
    route_data = json.loads(ROUTES.read_text(encoding="utf-8"))
    operation_map: dict[tuple[str, str], list[dict]] = {}
    for operation in route_data["operations"]:
        key = (
            operation["method"].upper(),
            normalized_route(operation["path"], request=False),
        )
        operation_map.setdefault(key, []).append(operation)
    route_paths = re.findall(r"path:\s*'([^']+)'", ROUTER.read_text(encoding="utf-8"))

    print("Read-only static inventory; no Dart, Flutter, product source or tests were executed.")
    print(f"feature_directories={len(feature_dirs)} (includes shell); feature_source_files={len(feature_files)}; feature_source_lines={sum(len(p.read_text(encoding='utf-8').splitlines()) for p in feature_files)}")
    print(f"feature_tree_sha256={tree_digest(feature_files)}")
    for path in feature_dirs:
        files = sorted(path.rglob("*.dart"))
        print(f"FEATURE {path.relative_to(ROOT).as_posix()}: files={len(files)} lines={sum(len(p.read_text(encoding='utf-8').splitlines()) for p in files)}")
    print(f"client_lib_source_files={len(client_files)}; client_lib_tree_sha256={tree_digest(client_files)}")
    print(f"flutter_go_router_paths={len(route_paths)}: {', '.join(route_paths)}")
    print(f"flutter_test_files_present={len(test_files)}; test_tree_sha256={tree_digest(test_files)}")
    for path in test_files:
        print(f"TEST_FILE {path.relative_to(ROOT).as_posix()}")
    print(f"backend_routes_manifest_sha256={hashlib.sha256(ROUTES.read_bytes()).hexdigest()}")
    print(f"routes_manifest_paths={len(route_data['paths'])}; operations={len(route_data['operations'])}")
    print("API scan spans client/lib and literal receivers `api`, `ref.read(apiClientProvider)`, and `ref.watch(apiClientProvider)` (whitespace/newlines accepted), excludes ApiClient's HTTP transport; query/parameter shapes normalized.")
    call_count = match_count = 0
    for source in client_files:
        if source.name == "api_client.dart":
            continue
        text = source.read_text(encoding="utf-8")
        for match in API_CALL.finditer(text):
            call_count += 1
            method = match.group("method").upper()
            endpoint = match.group("path")
            operation_list = operation_map.get((method, normalized_route(endpoint, request=True)), [])
            line = text.count("\n", 0, match.start()) + 1
            if operation_list:
                match_count += 1
                details = " || ".join(
                    f"{o['operationId']}; guards={','.join(o.get('guards', [])) or '-'}; roles={','.join(o.get('roles', [])) or '-'}; scopes={','.join(o.get('scopes', [])) or '-'}"
                    for o in operation_list
                )
            else:
                details = "NO_STATIC_MANIFEST_MATCH (may be dynamic/version/alias or extraction limitation)"
            print(f"CALL {source.relative_to(ROOT).as_posix()}:{line} {method} {endpoint} => {details}")
    print(f"literal_api_call_sites={call_count}; manifest_shape_matches={match_count}; unmatched={call_count - match_count}")
    print("REACT_SOURCE: current App.tsx maps /member to MemberRoutePending placeholder; text says full member shell/experience is not implemented; placeholder does not load member data. Staff pages are separate.")
    print("LIMIT: this static scan is not a complete action/API/DB-ownership/error/test crosswalk, runtime test, browser check, or reviewer sign-off.")


if __name__ == "__main__":
    main()
