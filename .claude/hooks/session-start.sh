#!/bin/bash
# Materialize the img2threejs skill submodule.
#
# The skill lives at .claude/skills/img2threejs as a git submodule pinned to a
# commit of https://github.com/img2threejs/img2threejs. A plain `git clone`
# (which is what Claude Code on the web does) leaves that path as an empty
# directory, and an empty directory means the skill never registers.
#
# This runs synchronously on purpose: skills are scanned as the session starts,
# so the checkout has to exist before the scan, not race with it.
set -euo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

# Idempotent: a no-op once the submodule is checked out at the pinned commit.
git submodule update --init --recursive

if [ ! -f .claude/skills/img2threejs/SKILL.md ]; then
  echo "session-start: img2threejs SKILL.md missing after submodule init" >&2
  exit 1
fi

echo "session-start: img2threejs skill ready ($(git -C .claude/skills/img2threejs rev-parse --short HEAD))"
