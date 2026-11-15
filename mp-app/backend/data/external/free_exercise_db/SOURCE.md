# free-exercise-db — source record (M33-c1)

- Repo: https://github.com/yuhonas/free-exercise-db
- Upstream commit: `f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5` (2026-09-27)
- File: `dist/exercises.json` (copied here as `exercises.json`)
- sha256: `5bb747e3fc658f095a60dcbf6d53c96627acdcc6ffb6fffde86f7e26995d40bf`
- Exercises: 876
- License: **The Unlicense** (public domain — see `LICENSE.md` upstream; entry in `NOTICE-THIRD-PARTY.md`)
- Use: exercise catalog metadata for the 14-ability system (axis tagging in M33-c3).
  Images (`images` field = upstream relative paths) are NOT vendored; no hotlinking of
  upstream raw URLs is required for the core feature (MuscleParadise map/illustrations
  are the UI layer, per project decision D-005/M22b).
- Verification: `python scripts/import_exercise_catalog.py --check` recomputes the digest.
