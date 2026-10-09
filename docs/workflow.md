# Workflow

Git is the only way work lands on an integration branch. `dev` is that branch. `main` exists, and the path from `dev` to `main` is not decided. Do not open a pull request to `main`, and do not merge to `main`, until that path is written here.

## Branches

| Kind | Name | Cut from | Lands on |
|---|---|---|---|
| Integration | `dev` | — | — |
| Feature | `feat/<slug>` | `dev` | `dev` |
| Bug fix | `hotfix/<slug>` | `dev` | `dev` |

`<slug>` is short, lowercase, and hyphenated. One branch per feature or fix.

Start each branch from an up-to-date `dev`. Do not commit directly on `dev` or `main`.

There is no release hotfix-from-`main` path yet. Until promotion to `main` is decided, a production bug is still `hotfix/<slug>` from `dev`.

## Sign-off

When the user says **sign-off** or **approve**:

1. Push the current `feat/*` or `hotfix/*` branch.
2. Open a pull request into `dev`.
3. Stop. The user accepts the merge.

Do not merge the pull request. Do not treat a review comment, a green check, or "looks good" as sign-off. Only those two words start this step.

## What a change contains

A feature branch carries one feature. A hotfix branch carries one bug fix. Schema, pipeline, and SQL that belong to that change go on the same branch. Leave unrelated edits off it.
