# Skill: raise-pr

Invoked when the user is ready to push the current feature branch and open a pull request to master.

## Pre-flight checks

1. **Confirm the current branch** — run `git branch --show-current`. If it is `master` or `main`, stop and tell the user to switch to a feature branch first.

2. **Validate the branch prefix** — the branch name must start with one of:
   - `feat-` — feature / enhancement
   - `bug-` — bug fix
   - `hot-` — hotfix

   If the prefix is missing or wrong, stop and tell the user. Do not rename branches automatically.

3. **Check for uncommitted changes** — run `git status --porcelain`.
   If there are uncommitted changes, ask the user whether to commit them first (and help them do so) or abort.

## Steps

### 1. Push the branch

```bash
git push -u origin <branch-name>
```

### 2. Update README.md (feat- branches only)

For `feat-` branches:
- Read the current `README.md`.
- Identify which roadmap item this PR implements. Use the branch name slug and the PR description as clues. Ask the user to confirm the match if it is ambiguous.
- Change the matching `- [ ]` checkbox to `- [x]`.
- Commit the README change on the feature branch before opening the PR:
  ```bash
  git add README.md
  git commit -m "docs: mark <item> as completed in roadmap"
  git push
  ```

For `bug-` and `hot-` branches, skip the README update.

### 3. Open the pull request

Use `gh pr create` targeting `master`:

```bash
gh pr create \
  --base master \
  --title "<type>: <short description>" \
  --body "$(cat <<'EOF'
## Summary
- <bullet points describing what was implemented>

## Test plan
- [ ] Smoke tests pass (`python3.11 -m pytest`)
- [ ] New tests added for this capability
- [ ] Known-correct fixture case added to eval harness

## Checklist
- [ ] `Result` fields populated (method, summary, values, metadata)
- [ ] Uses `validation/` helpers — no local dtype/assumption logic
- [ ] `store.write_back_column` used for any new columns
- [ ] README roadmap checkbox ticked

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 4. Confirm

Print:
- The PR URL returned by `gh pr create`
- A reminder to request a review if working with collaborators
