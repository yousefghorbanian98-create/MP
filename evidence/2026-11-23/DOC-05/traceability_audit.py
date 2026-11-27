from pathlib import Path

CHECKS = {
    "README.md": ["docs/MuscleParadise/adr/007-pwa-primary-release.md", "TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "TODO-PWA-RELEASE-2026-11-23.fa.md", "PWA-EXECUTION-STATE.md"],
    "docs/README.md": ["MuscleParadise/adr/007-pwa-primary-release.md", "MuscleParadise/TODO-2026-11-16.md", "MuscleParadise/TODO-PWA-RELEASE-2026-11-23.fa.md", "MuscleParadise/PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/TODO-PWA-RELEASE-2026-11-23.fa.md": ["adr/007-pwa-primary-release.md", "TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/TODO-2026-11-16.md": ["TODO-PWA-RELEASE-2026-11-23.fa.md", "PWA-EXECUTION-STATE.md", "adr/007-pwa-primary-release.md"],
    "docs/MuscleParadise/SESSION_HANDOFF.md": ["TODO-PWA-RELEASE-2026-11-23.fa.md", "TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/README.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/frontend-ui-ux-flow-option-03-lab-v1-2026-11-23.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md", "فقط طراحی/مرجع"],
    "docs/MuscleParadise/architecture/muscle-paradise-final-pwa-access-flow-v1-2026-11-23.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/ai-autonomous-production-plan-v1-2026-11-23.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/motion-pwa-availability-matrix-2026-11-23.fa.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/studio-motion-current-tree-static-crosswalk-2026-11-23.fa.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/system-integrated-flow-v1-2026-11-23.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/session-decisions-2026-11-23/WIRING-LEDGER.md": ["../../adr/007-pwa-primary-release.md", "../../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../../TODO-PWA-RELEASE-2026-11-23.fa.md", "../../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/session-decisions-2026-11-23/PWA-00-CONTRACT.fa.md": ["../../adr/007-pwa-primary-release.md", "../../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../../TODO-PWA-RELEASE-2026-11-23.fa.md", "../../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/session-decisions-2026-11-23/PWA-00-EVIDENCE.fa.md": ["../../adr/007-pwa-primary-release.md", "../../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../../TODO-PWA-RELEASE-2026-11-23.fa.md", "../../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/project-guide/01-project-map.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/project-guide/04-development-testing-operations.md": ["../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/project-guide/05-security-status-glossary.md": ["../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/MASTER_MAP.md": ["TODO-2026-11-16.md", "adr/007-pwa-primary-release.md", "TODO-PWA-RELEASE-2026-11-23.fa.md", "PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/architecture/finn-loop-microtask-backlog-draft-v1-2026-11-23.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md"],
    "docs/MuscleParadise/TODO-CLOUD-FINANCE-ACCESS.md": ["adr/007-pwa-primary-release.md", "TODO-2026-11-16.md", "TODO-PWA-RELEASE-2026-11-23.fa.md", "PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/DATA-RETENTION.md": ["adr/007-pwa-primary-release.md", "TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "TODO-PWA-RELEASE-2026-11-23.fa.md", "PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/security/biometric-policy.md": ["../adr/007-pwa-primary-release.md", "../TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "../TODO-PWA-RELEASE-2026-11-23.fa.md", "../PWA-EXECUTION-STATE.md"],
    "docs/MuscleParadise/PWA-EXECUTION-STATE.md": ["TODO-PWA-RELEASE-2026-11-23.fa.md", "TODO-2026-11-16.md#pwa-ui-ux-full-backlog-2026-11-23", "adr/007-pwa-primary-release.md"],
}

failed = False
for filename, markers in CHECKS.items():
    path = Path(filename)
    if not path.is_file():
        print(f"FAIL {filename}: missing file")
        failed = True
        continue
    text = path.read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in text]
    if missing:
        print(f"FAIL {filename}: missing markers {missing!r}")
        failed = True
    else:
        print(f"PASS {filename}: {len(markers)} traceability/boundary markers")
print(f"Checked {len(CHECKS)} PWA/decision documents; result={'FAIL' if failed else 'PASS'}")
raise SystemExit(1 if failed else 0)
