# Image digest lock files

CI writes one `.env` file per git tag (e.g. `v0.4.0.env`) containing `sha256`-pinned image references for every published service.

**On Pi:**

```bash
cp deploy/locks/v0.4.0.env deploy/locks/current.env
```

`scripts/harbor-pull.sh` reads `deploy/locks/current.env`.

Lock files for releases are committed to git. `current.env` is local state (gitignored via `.env` rules — use `deploy/locks/current.env` pattern or symlink).
