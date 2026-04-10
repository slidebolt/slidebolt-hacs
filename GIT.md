# Git Workflow for slidebolt-hacs

This repository contains the Slidebolt Home Assistant Custom Component, which allows Home Assistant to discover and control Slidebolt entities.

## Dependencies
- **Internal:** Implicitly depends on the WebSocket API provided by `plugin-homeassistant` (Go).
- **External:** 
  - Home Assistant (Core / OS / Supervised).
  - Python 3.12+.

## Build Process
- **Type:** Home Assistant Integration (Custom Component).
- **Consumption:** Installed into the `custom_components/slidebolt/` directory of a Home Assistant instance.
- **Artifacts:** Python source files, `manifest.json`, and static assets.
- **Validation:** 
  - Validated through Home Assistant's internal component loading and configuration flow.
  - Integration-tested via the BDD features in the `plugin-homeassistant` repository.

## Pre-requisites & Publishing
This component should be updated whenever the communication protocol or supported entity types in `plugin-homeassistant` are changed.

**Before publishing:**
1. Determine current tag: `git tag | sort -V | tail -n 1`
2. Ensure `manifest.json` version matches the intended release.
3. Verify compatibility with the latest `plugin-homeassistant`.

**Publishing Order:**
1. Update Python source and metadata.
2. Determine next semantic version (e.g., `v1.0.4`).
3. Commit and push the changes to `main`.
4. Tag the repository: `git tag v1.0.4`.
5. Push the tag: `git push origin main v1.0.4`.

## Update Workflow & Verification
1. **Modify:** Update entity logic in `custom_components/slidebolt/*.py`.
2. **Verify Local:**
   - Use the `mock/` server to simulate Slidebolt for basic connectivity tests.
   - Run Home Assistant with the custom component enabled.
3. **Commit:** Ensure the commit message describes the new HA features or fixes.
4. **Tag & Push:** (Follow the Publishing Order above).
