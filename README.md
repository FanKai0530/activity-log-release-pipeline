# Activity Log Release Pipeline

This repository extends my [earlier README activity assignment](https://github.com/FanKai0530/devops-readme-activity-a3). The Python program turns recent Git commits into a safe, bounded README section. The release pipeline tests and packages that program once, then promotes the same ZIP through `dev`, `staging`, and `production` GitHub environments.

The activity-log idea comes from [TheDanniCraft/activity-log](https://github.com/TheDanniCraft/activity-log). This repository uses my earlier Python implementation as its software base rather than copying that project's JavaScript source.

## Pipeline

A push to `main` or **Run workflow** starts:

1. `build`: read the highest release tag among `dev-v*`, `staging-v*`, and `prod-v*`, increment the patch, package one ZIP, and record its SHA-256 digest.
2. `test-unit`: after build, Python 3.11, 3.12, and 3.13 each download and verify the ZIP, run real unit tests, enforce at least 80% coverage of the updater and builder, and upload JUnit plus coverage XML reports.
3. `test-integration`: after all unit matrix jobs pass, staging and prod configurations each download the same ZIP and run tests against its checksum, contents, version, and packaged CLI. JUnit reports are uploaded.
4. `deploy-dev`: runs only after both test phases pass and creates a prerelease from the tested ZIP.
5. `deploy-staging`: promotes the same ZIP to a staging prerelease.
6. `ai-release-review`: a read-only OpenAI agent lists commits and inspects allowlisted diffs. Its draft is saved as an Actions artifact and job summary.
7. `deploy-production`: waits for the required reviewer, verifies the ZIP digest, and publishes the production release with the AI draft attached.

Each stage uses a tag such as `dev-v1.0.0`, `staging-v1.0.0`, or `prod-v1.0.0`. The next successful production run automatically chooses `1.0.1`. A failed release creation is cleaned up; an existing release is never overwritten.

For a controlled proof of the release gate, manually dispatch the workflow with `demonstrate_failed_test=true`. The integration job runs a clearly labeled intentional failing test after the real integration tests. The job fails and all three release jobs must show **skipped**. This option is false for pushes and ordinary manual runs.

## Required repository settings

In **Settings → Environments**, create these environments and variables:

| Environment | `BUILD_TAG` | `RELEASE_NOTE` | Other setting |
| --- | --- | --- | --- |
| `dev` | `dev` | `Development build for early testing` | none |
| `staging` | `staging` | `Testing pre-production release` | secret `OPENAI_API_KEY`; variable `AI_MODEL=gpt-5.4-mini` |
| `production` | `prod` | `Approved production simulation` | required reviewer: repository owner |

The repository keeps the default **read-only** workflow token setting. Release jobs explicitly request `contents: write`; test, build, and AI jobs have read-only access. Do not add an API key to repository secrets, code, logs, or slides. Create a dedicated OpenAI API key and save it as the **staging environment secret** `OPENAI_API_KEY`.

The repository owner is currently the required production reviewer because no second reviewer is available. GitHub still pauses the job until the owner manually approves it; administrator bypass is disabled. The reviewer should open the `ai-release-review` job summary and download the `ai-review` artifact before approving. If a teammate or instructor becomes available, add that person as the required reviewer and enable **Prevent self-review**. The AI agent cannot create releases or approve deployments.

## Running locally

```sh
python -m unittest tests.test_update_readme tests.test_build_release -v
python scripts/update_readme.py --repository FanKai0530/activity-log-release-pipeline --check
python scripts/build_release.py
# After creating release-bundle.sha256 and setting TEST_ENV=staging:
python -m unittest tests.test_integration -v
```

## AI agent safety and evaluation

The prompt is in [`scripts/release_review_agent.py`](scripts/release_review_agent.py). The agent can call only `list_commits` and `show_diff`. Diff requests must name a commit in the bounded release list. The job permits at most four tool calls and gives the GitHub token only `contents: read`. Commit and issue text is treated as untrusted input; the agent's output is a draft for a person, never a deployment decision.

To judge whether the agent helps, compare reviewer time and missed or false risk flags across several releases. Record any incorrect statement and the human correction in the report. A successful API call alone is not evidence of useful review.

## Submission evidence

The PDF report should include genuine screenshots of a passing run, unit and integration test logs, the coverage and JUnit artifacts, a deliberately failing run with skipped releases, the three environment pages, production reviewer rule, the **Waiting for review** state before approval, approval event, and all three release pages. Show each release job downloading the same named build artifact. No production success should be claimed until the reviewer has approved the pending job. The in-class quiz will ask about the choices made here.

## Recent activity

<!-- activity:start -->
_No activity has been published in this new repository yet._
<!-- activity:end -->
