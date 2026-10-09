# Workflow

Git is the only way work lands on a shared branch. `dev` is the integration branch. `main` is the published snapshot of `dev`, and it moves forward only by promotion.

## Branches

| Kind | Name | Cut from | Lands on |
|---|---|---|---|
| Published | `main` | `dev` | — |
| Integration | `dev` | — | `main`, by promotion |
| Feature | `feat/<slug>` | `dev` | `dev` |
| Bug fix | `hotfix/<slug>` | `dev` | `dev` |

`<slug>` is short, lowercase, and hyphenated. One branch per feature or fix.

Start each branch from an up-to-date `dev`. Do not commit directly on `dev` or `main`.

There is no hotfix-from-`main` path. A fix is `hotfix/<slug>` from `dev`, and it reaches `main` when `dev` is promoted.

## Sign-off

When the user says **sign-off** or **approve**:

1. Push the current `feat/*` or `hotfix/*` branch.
2. Open a pull request into `dev`.
3. Stop. The user accepts the merge.

Do not merge the pull request. Do not treat a review comment, a green check, or "looks good" as sign-off. Only those two words start this step. Sign-off never targets `main`.

## Promote

When the user says **promote**:

1. Make sure `dev` on the remote has every merged change.
2. Open a pull request from `dev` into `main`.
3. Stop. The user accepts the merge.

Do not merge that pull request. Only the word promote starts this step.

## What a change contains

A feature branch carries one feature. A hotfix branch carries one bug fix. Schema, pipeline, and SQL that belong to that change go on the same branch. Leave unrelated edits off it.
