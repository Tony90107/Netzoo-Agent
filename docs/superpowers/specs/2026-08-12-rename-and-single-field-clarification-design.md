# Rename to `netzoo_agent` and single-field clarification design

## Goal

Rename the project identity from `network-zoo-panda-puma` to `netzoo_agent` while
preserving all supported runtime behavior. Simplify the interactive missing-input
wizard so users provide exactly one unresolved field per reply; it must no longer
advertise or accept batch `field=value` assignments.

## Scope

### Project identity

- Rename the repository directory to `netzoo_agent`.
- Replace the old project identifier in runtime-facing project policy, Docker
  Compose image names, launcher behavior, tests, and current user-facing docs.
- Use `netzoo_agent` as the Compose project name so containers and networks have
  a stable, explicit identity independent of the parent directory.
- Preserve existing Python import/package names (`netzoo_agent_core`), command
  names (`netzoo-chat`), workflow action names, environment variables
  (`NETZOO_*`), persisted state locations (`.netzoo`), and service names. They
  are already part of the functional interface and are not aliases of the old
  project name.

### Clarification wizard

- Remove all user-facing references to "advanced users" and batch
  `field=value` input.
- Parse one answer only for the current missing field. A number still selects a
  displayed candidate; any other answer is interpreted as that field's path.
- Keep LIONESS mode selection unchanged because it is a single, enumerated
  clarification rather than file-path batching.
- Preserve session resume and continuation markers so one-by-one answers still
  return to the same pending workflow.

## Non-goals

- Do not delete old Docker containers, networks, volumes, images, sessions, or
  logs. Docker will create a new `netzoo_agent-*` project namespace after the
  rename.
- Do not change supported NetZoo workflows, tool permissions, recovery, model
  behavior, or execution authorization.
- Do not provide a backward-compatible old-directory launcher or retain the old
  identity in current runtime configuration.

## Implementation design

1. Update the workflow plan clarification text so it states that the wizard
   requests one unresolved input at a time.
2. Narrow `parse_clarification_assignments` to accept only the current target
   field. Remove field-alias/batch assignment parsing and all-missing numeric
   sequences. The conversation loop already calls it with the current field,
   so its state machine remains one-at-a-time.
3. Update clarification errors/prompts and affected tests to assert the
   single-field behavior.
4. Replace every current occurrence of the old project identifier outside
   historical immutable archive/design records where it is needed to preserve
   historical context. Update active README, commands, launch tests, policy,
   Docker image configuration, and current operational guides.
5. Rename the repository root directory to `netzoo_agent` after in-repository
   references have been updated. Set the Compose project name explicitly in the
   active configuration, avoiding a dependency on the renamed directory's
   inferred project name.

## Safety and compatibility

- `docker compose` services, volume names, and network behavior must remain
  functional after the identity change. The explicit Compose name intentionally
  creates new resources under the new project prefix and never removes old
  resources.
- Existing `.netzoo` data remains in the renamed project directory and continues
  to be discovered at the same relative location.
- No normal tool execution is enabled by this work. `/test` and `/execute`
  retain their current behavior.
- Existing user worktree changes are left untouched.

## Verification

- Run targeted clarification, launcher, and text-contract tests after updating
  expectations.
- Run the full test suite from the renamed project root.
- Run a Docker Compose configuration check and start `./netzoo-chat` far enough
  to confirm the launcher uses the `netzoo_agent` Compose namespace and enters
  the normal TEST-mode prompt.
