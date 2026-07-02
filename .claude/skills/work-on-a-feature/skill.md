# Skill: work-on-a-feature

Invoked when the user wants to start working on a new feature, bug fix, or hotfix.
The user provides a description of the work; this skill handles all the git setup.

## Steps

### 1. Clarify the branch type (if not obvious from the description)

Determine which prefix applies:
- `feat-` — new capability or enhancement
- `bug-` — bug fix
- `hot-` — hotfix (urgent production fix)

If the description is ambiguous, ask the user to confirm which prefix before continuing.

### 2. Fetch and update master

```bash
git fetch origin
git checkout master
git pull origin master
```

If there are local commits on master that haven't been pushed, warn the user before pulling.

### 3. Derive the branch name

Convert the feature description into a short, kebab-case slug (3–6 words max).
Prepend the correct prefix. Examples:
- "add column profiling" → `feat-add-column-profiling`
- "fix outlier detection crash" → `bug-fix-outlier-detection-crash`
- "hotfix incorrect p-value" → `hot-fix-incorrect-p-value`

Show the proposed branch name to the user and confirm before creating it.

### 4. Check the main worktree for uncommitted or staged changes

Run `git status --porcelain` in the main worktree.

**If the worktree is clean** (no output):
- Create and check out the branch directly in the main worktree:
  ```bash
  git checkout -b <branch-name>
  ```

**If the worktree has uncommitted or staged changes** (output is non-empty):
- Do NOT touch the main worktree.
- Create a new linked worktree in a sibling directory named after the branch:
  ```bash
  git worktree add ../<branch-name> -b <branch-name>
  ```
- Open the new worktree in VSCode:
  ```bash
  code ../<branch-name>
  ```
- Inform the user that the new worktree is open in VSCode and the main worktree is untouched.

### 5. Confirm

Print a short summary:
- Branch name created
- Whether work is in the main worktree or a new worktree
- The path to work in
- Reminder: when ready to ship, run `/raise-pr`
