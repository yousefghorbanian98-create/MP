#!/usr/bin/env python3
"""Read-only crosswalk audit using generated interaction map and current Studio source."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MAP = ROOT / "docs/MuscleParadise/architecture/interaction-map.json"
ROUTES = ROOT / "mp-app/backend/api/routes.json"
APP = ROOT / "mp-app/studio/src/App.tsx"
ROLE_NAV = ROOT / "mp-app/studio/src/lib/roleNav.ts"
NAVIGATION = ROOT / "mp-app/studio/src/lib/navigation.ts"


def norm(path: str) -> str:
    path = path.split("?", 1)[0]
    path = path.replace("*", "{}")
    path = re.sub(r"\{[^}]+\}", "{}", path)
    return path.rstrip("/") or "/"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_pages(source: str) -> dict[str, str]:
    block = re.search(r"const pages: Record<PageId, \(\) => JSX\.Element> = \{(.*?)\n\};", source, re.S)
    if not block:
        raise SystemExit("FAIL: App.tsx pages map not found")
    return dict(re.findall(r"^\s*([a-z]+):\s*([A-Za-z0-9_]+),", block.group(1), re.M))


def parse_roles(source: str, page_ids: set[str]) -> dict[str, list[str]]:
    all_staff_match = re.search(r"const ALL_STAFF: readonly Role\[\] = \[(.*?)\];", source, re.S)
    if not all_staff_match:
        raise SystemExit("FAIL: ALL_STAFF source list not found")
    all_staff = re.findall(r"\"([a-z_]+)\"", all_staff_match.group(1))
    block_match = re.search(r"export const PAGE_RULES: Record<string, NavRule> = \{(.*?)\n\};", source, re.S)
    if not block_match:
        raise SystemExit("FAIL: PAGE_RULES source map not found")
    block = block_match.group(1)
    # Restrict property boundaries to known PageId keys; otherwise `roles:` itself
    # is mistaken for the next top-level property (notably multiline finance rules).
    key_pattern = re.compile(r"^\s*(" + "|".join(re.escape(p) for p in sorted(page_ids)) + r")\s*:", re.M)
    matches = list(key_pattern.finditer(block))
    result: dict[str, list[str]] = {}
    for index, match in enumerate(matches):
        page = match.group(1)
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(block)
        body = block[match.end():body_end]
        all_match = re.search(r"\broles:\s*ALL_STAFF\b", body)
        list_match = re.search(r"\broles:\s*\[([^\]]*)\]", body, re.S)
        if all_match:
            result[page] = all_staff
        elif list_match:
            result[page] = re.findall(r"\"([a-z_]+)\"", list_match.group(1))
    return result


def main() -> None:
    app_text = APP.read_text(encoding="utf-8")
    role_text = ROLE_NAV.read_text(encoding="utf-8")
    nav_text = NAVIGATION.read_text(encoding="utf-8")
    interaction = json.loads(MAP.read_text(encoding="utf-8"))
    route_data = json.loads(ROUTES.read_text(encoding="utf-8"))
    pages = parse_pages(app_text)
    roles = parse_roles(role_text, set(pages))
    # Keep generated Studio pages distinct from similarly named Flutter surfaces.
    surfaces = {
        item["surface"].casefold(): item
        for item in interaction["surfaces"]
        if item.get("kind") == "studio-page"
    }
    operations = {
        (item["method"].upper(), norm(item["path"])): item
        for item in route_data["operations"]
    }

    print("Read-only inventory; no product source, test, or policy was changed/run.")
    print(f"HEAD_SOURCE_SHA={__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip()}")
    for path in (MAP, ROUTES, APP, ROLE_NAV, NAVIGATION):
        print(f"INPUT_SHA256 {path.relative_to(ROOT).as_posix()} {sha(path)}")
    print(f"studio_staff_page_ids={len(pages)}: {', '.join(pages)}")
    print(f"interaction_map_surfaces={len(interaction['surfaces'])}; api_contract_operations={len(route_data['operations'])}; contract_paths_from_gate={interaction.get('contract_paths')}")
    print(f"interaction_map_has_state_field={any('state' in surface for surface in interaction['surfaces'])}")
    staff_used: set[tuple[str, str]] = set()
    all_used: set[tuple[str, str]] = set()
    staff_test_gaps: list[str] = []
    for page, component in pages.items():
        surface = surfaces.get(page.casefold())
        if surface is None:
            print(f"PAGE {page}: SURFACE_MISSING; route=/staff/{page}; component={component}")
            staff_test_gaps.append(page)
            continue
        tests = surface.get("tests", [])
        for test in tests:
            full = ROOT / test
            print(f"TEST_EXISTS {test} {full.is_file()}")
        if not tests:
            staff_test_gaps.append(page)
        api_lines = []
        for endpoint in surface.get("endpoints", []):
            method = endpoint["method"].upper()
            path = endpoint["path"]
            key = (method, norm(path))
            staff_used.add(key)
            all_used.add(key)
            api_lines.append(
                f"{method} {path} [UI-guard={','.join(endpoint.get('guards', [])) or '-'}; API-roles={','.join(endpoint.get('roles', [])) or '-'}; contract={endpoint.get('in_contract')}]"
            )
        component_path = surface.get("file", "?")
        page_roles = roles.get(page, [])
        print(
            f"PAGE {page} route=/staff/{page} component={component_path} import={component} "
            f"roles={'/'.join(page_roles) or 'UNKNOWN'} controls={surface.get('controls')} "
            f"tests={';'.join(tests) or 'NONE'} state=UNKNOWN_NOT_MAPPED"
        )
        for api_line in api_lines:
            print(f"  API {api_line}")

    for surface in interaction["surfaces"]:
        for endpoint in surface.get("endpoints", []):
            all_used.add((endpoint["method"].upper(), norm(endpoint["path"])))
    no_surface = sorted(set(operations) - all_used)
    member_page_rules = [page for page, page_roles in roles.items() if "member" in page_roles]
    is_staff_excludes_member = 'role !== "member"' in nav_text and 'role !== "guest"' in nav_text
    placeholder_present = "function MemberRoutePending" in app_text and "پوسته و تجربهٔ کامل عضو" in app_text
    print(f"staff_pages_without_test_reference={','.join(staff_test_gaps) or 'none'}")
    print(f"staff_endpoint_shapes_referenced={len(staff_used)}; any_interaction_surface_endpoint_shapes_referenced={len(all_used)}; manifest_operations_without_any_surface_reference={len(no_surface)}")
    print("UNMAPPED_CONTRACT_OPERATIONS (absence from interaction map only; not proof of dead code):")
    for method, path in no_surface:
        print(f"  {method} {path}")
    print(f"member_role_in_page_rules={','.join(member_page_rules)}")
    print(f"isStaffRole_excludes_member={is_staff_excludes_member}; member_route_placeholder_symbol_present={placeholder_present}")
    print("STATE_GAP: generated map contains controls/endpoints/tests but no per-page loading/empty/error/persistence-state field; report UNKNOWN, not pass.")
    print("LIMIT: static map/source only; no test execution, DB model/ownership audit, browser QA, or reviewer acceptance.")


if __name__ == "__main__":
    main()
