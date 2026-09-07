#!/usr/bin/env bash
#
# release.sh — cut a release of the vibe-model-skills suite.
#
# The suite is versioned as ONE unit (the skills reference each other with
# sibling-relative paths and hand off through documents, so they ship together).
# Releases follow SemVer, driven by Conventional Commits since the last tag:
#
#   feat!:  / BREAKING CHANGE:  → major   (breaks a skill contract, conventions.yml
#                                          schema, or an inter-skill handoff doc)
#   feat:                       → minor   (new skill / variant / capability, additive)
#   fix: / docs: / everything   → patch   (corrected or clarified guidance)
#
# What a release does, in order:
#   1. Verify a clean tree on `main`.
#   2. Resolve the next version (from an explicit arg, a bump keyword, or by
#      reading the commits since the last tag).
#   3. Regenerate CHANGELOG.md from those commits (Keep a Changelog format).
#   4. Stamp the version into VERSION.
#   5. Rebuild a clean skills.zip (no .DS_Store / __MACOSX cruft).
#   6. Commit `chore(release): vX.Y.Z`, tag `vX.Y.Z`.
#   7. Push the commit + tag and publish a GitHub Release with skills.zip attached.
#
# Usage:
#   scripts/release.sh                 # auto-detect the bump from commits
#   scripts/release.sh patch|minor|major
#   scripts/release.sh 0.1.0           # explicit version
#   scripts/release.sh --dry-run       # show what would happen, change nothing
#   scripts/release.sh --draft         # publish the GitHub Release as a draft
#
# Flags can combine, e.g. `scripts/release.sh minor --dry-run`.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

DRY_RUN=false
DRAFT=false
BUMP_ARG=""

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --draft)   DRAFT=true ;;
    patch|minor|major) BUMP_ARG="$arg" ;;
    [0-9]*.[0-9]*.[0-9]*) BUMP_ARG="$arg" ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

say()  { printf '\033[1m%s\033[0m\n' "$*"; }
info() { printf '  %s\n' "$*"; }
run()  { if $DRY_RUN; then echo "  [dry-run] $*"; else eval "$*"; fi; }

# ---------------------------------------------------------------------------
# 1. Preconditions
# ---------------------------------------------------------------------------
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$BRANCH" != "main" ]]; then
  echo "Refusing to release from '$BRANCH' — releases are cut from main." >&2
  echo "(Use --dry-run from any branch to preview.)" >&2
  $DRY_RUN || exit 1
fi

if [[ -n "$(git status --porcelain)" ]] && ! $DRY_RUN; then
  echo "Working tree is not clean. Commit or stash first." >&2
  exit 1
fi

command -v gh >/dev/null || { echo "gh CLI not found (needed to publish the release)." >&2; exit 1; }

# ---------------------------------------------------------------------------
# 2. Resolve current + next version
# ---------------------------------------------------------------------------
LAST_TAG="$(git describe --tags --abbrev=0 --match 'v*' 2>/dev/null || true)"
if [[ -z "$LAST_TAG" ]]; then
  CURRENT="0.0.0"
  RANGE=""                         # first release: consider all history
  FIRST_RELEASE=true
else
  CURRENT="${LAST_TAG#v}"
  RANGE="${LAST_TAG}..HEAD"
  FIRST_RELEASE=false
fi

IFS='.' read -r MAJ MIN PAT <<<"$CURRENT"

detect_bump() {
  # Inspect commit subjects (+ bodies) since the last tag for Conventional Commit intent.
  local subjects; subjects="$(git log ${RANGE:+$RANGE} --pretty='%s%n%b')"
  if grep -qiE '(^|\s)BREAKING CHANGE' <<<"$subjects" || grep -qE '^[a-z]+(\(.+\))?!:' <<<"$subjects"; then
    echo major; return
  fi
  if grep -qE '^feat(\(.+\))?:' <<<"$subjects"; then echo minor; return; fi
  echo patch
}

if [[ -z "$BUMP_ARG" ]]; then
  if $FIRST_RELEASE; then
    NEXT="0.1.0"                    # first public release starts at 0.1.0
    info "No tags yet → defaulting first release to 0.1.0."
  else
    BUMP_ARG="$(detect_bump)"
    info "Auto-detected bump from commits: $BUMP_ARG"
  fi
fi

if [[ -z "${NEXT:-}" ]]; then
  case "$BUMP_ARG" in
    major) NEXT="$((MAJ+1)).0.0" ;;
    minor) NEXT="${MAJ}.$((MIN+1)).0" ;;
    patch) NEXT="${MAJ}.${MIN}.$((PAT+1))" ;;
    [0-9]*.[0-9]*.[0-9]*) NEXT="$BUMP_ARG" ;;
  esac
fi

TAG="v${NEXT}"
DATE="$(date +%Y-%m-%d)"
say "Releasing ${TAG}  (was ${LAST_TAG:-none})"

# ---------------------------------------------------------------------------
# 3. Build the changelog section from commits since the last tag
# ---------------------------------------------------------------------------
section() {                        # $1 = grep pattern, $2 = heading
  local body; body="$(git log ${RANGE:+$RANGE} --no-merges --pretty='%s' \
    | grep -E "$1" | grep -vE '^chore\(release\)' \
    | sed -E "s/^[a-z]+(\(.+\))?!?: //" | sed 's/^/- /' || true)"
  # Use `if` (not `&&`) so an empty section returns 0 — otherwise the last
  # empty section leaks a non-zero status into `NOTES="$(...)"`, which aborts
  # the release under `set -e`.
  if [[ -n "$body" ]]; then printf '### %s\n%s\n\n' "$2" "$body"; fi
}

if $FIRST_RELEASE; then
  # Don't dump all of pre-history into the first entry — curate it. Full history is in git.
  NOTES="### Added
- Initial public release of the vibe-model-skills suite: the four-station modeling loop
  (\`domain-model-assessment\` → \`etl-development-framework\` → \`domain-model-validation\` →
  \`domain-documentation\`) plus the cross-cutting \`autonomous-validation\` and steady-state
  \`domain-sync\` skills, the \`conventions.yml\` config surface with its six \`etl_type\` ×
  \`output_model\` variants, and the runnable Meridian example dataset.
"
else
  NOTES="$(
    section '^feat'                     'Added'
    section '^fix'                      'Fixed'
    section '^docs'                     'Documentation'
    section '^(refactor|perf|chore|style|test|build|ci)' 'Changed'
  )"
  [[ -z "$NOTES" ]] && NOTES="- Release ${TAG}."$'\n'
fi

say "Changelog for ${TAG}:"
printf '%s\n' "$NOTES" | sed 's/^/  /'

# ---------------------------------------------------------------------------
# 4. Write files (CHANGELOG, VERSION)
# ---------------------------------------------------------------------------
write_changelog() {
  local header entry rest
  header='# Changelog

All notable changes to the vibe-model-skills suite are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the suite
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
'
  entry="## [${NEXT}] - ${DATE}
${NOTES}"
  # Preserve prior version entries (everything from the first "## [" onward).
  rest="$( [[ -f CHANGELOG.md ]] && sed -n '/^## \[/,$p' CHANGELOG.md || true )"
  printf '%s\n%s%s\n' "$header" "$entry" "$rest" > CHANGELOG.md
}

if $DRY_RUN; then
  echo "  [dry-run] would rewrite CHANGELOG.md, VERSION"
else
  write_changelog
  echo "$NEXT" > VERSION
fi

# ---------------------------------------------------------------------------
# 5. Rebuild a clean skills.zip (this is the release asset; *.zip is gitignored)
# ---------------------------------------------------------------------------
build_zip() {
  find skills -name '.DS_Store' -delete
  rm -f skills.zip
  zip -q -r -X skills.zip skills -x '*.DS_Store' -x '*/__MACOSX/*'
  info "Built skills.zip ($(du -h skills.zip | cut -f1))."
}
if $DRY_RUN; then echo "  [dry-run] would rebuild skills.zip"; else build_zip; fi

# ---------------------------------------------------------------------------
# 6. Commit + tag
# ---------------------------------------------------------------------------
run "git add CHANGELOG.md VERSION"
run "git commit -m 'chore(release): ${TAG}'"
run "git tag -a '${TAG}' -m '${TAG}'"

# ---------------------------------------------------------------------------
# 7. Push + publish
# ---------------------------------------------------------------------------
if $DRY_RUN; then
  say "Dry run complete — nothing was written, committed, tagged, or pushed."
  exit 0
fi

read -r -p "Push ${TAG} and publish the GitHub Release? [y/N] " reply
if [[ "$reply" != "y" && "$reply" != "Y" ]]; then
  say "Stopped before push. Local commit + tag exist; run:"
  info "git push origin main --follow-tags   # to push"
  info "git tag -d ${TAG} && git reset --hard HEAD~1   # to undo"
  exit 0
fi

git push origin main --follow-tags
GH_ARGS=(release create "$TAG" --title "$TAG" --notes "$NOTES" skills.zip)
$DRAFT && GH_ARGS+=(--draft)
gh "${GH_ARGS[@]}"
say "Published ${TAG}."
