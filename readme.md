# Bitbucket Branch lockdown automation

A script to automate the setup of branch protection rules in Bitbucket repositories.

## Prerequisites

- Python 3.x
- Atlassian API token with appropriate permissions
- Virtual environment

### Creating an API token

1. Go to API tokens: <https://id.atlassian.com/manage-profile/security/api-tokens>
2. Create API token with scopes
3. Set a name and an expiry date for it
4. On the next step, select Bitbucket
5. On the next step, select the following scopes:
    1. read:repository:bitbucket
    2. write:repository:bitbucket
    3. admin:repository:bitbucket
    4. write:permission:bitbucket
6. Confirm and create the token
7. Copy the API token and store it securely, as you won't be able to see it again.

### Setting up a virtual environment

After cloning this repository, set up a virtual environment and install the required packages.

#### On Linux or macOS

```bash
git clone https://github.com/leandro-lorenzini/bitbucket-branch-lockdown.git
cd bitbucket-branch-lockdown
python3 -m venv .
source bin/activate
pip install -r requirements.txt
```

#### On Windows (PowerShell)

```powershell
git clone https://github.com/leandro-lorenzini/bitbucket-branch-lockdown.git
cd bitbucket-branch-lockdown
python -m venv .
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\Scripts\activate
pip install -r requirements.txt
```

## Usage

You can run the script non-interactively by setting environment variables, or interactively and be prompted for missing values.

### Non-interactive usage (recommended for automation)

Set the required environment variables before running the script. If any are missing, you will be prompted interactively.

#### On Linux or macOS

```bash
export ATLASSIAN_EMAIL="you@example.com"
export ATLASSIAN_API_TOKEN="your_api_token"
export WORKSPACE="your-workspace-slug"
export BRANCHES="main,release/*"
export BRANCH_TYPES="production,development"
export ALLOW_GROUPS="managers"
export ALLOW_BRANCH_DELETE="no"
export ENFORCE_MERGE_CHECKS="yes"
export RESET_APPROVALS_ON_CHANGE="yes"
export CONFIRM_DELETE_EXISTING_RULES="yes"
export REPOSITORIES="repo1,repo2"
export WRITE_ACCESS_MODE="groups"
export MERGE_ACCESS_MODE="groups"
python3 main.py
```

#### On Windows (PowerShell)

```powershell
$env:ATLASSIAN_EMAIL = "you@example.com"
$env:ATLASSIAN_API_TOKEN = "your_api_token"
$env:WORKSPACE = "your-workspace-slug"
$env:BRANCHES = "main,release/*"
$env:BRANCH_TYPES = "production,development"
$env:ALLOW_GROUPS = "managers"
$env:ALLOW_BRANCH_DELETE = "no"
$env:ENFORCE_MERGE_CHECKS = "yes"
$env:RESET_APPROVALS_ON_CHANGE = "yes"
$env:CONFIRM_DELETE_EXISTING_RULES = "yes"
$env:REPOSITORIES = "repo1,repo2"
$env:WRITE_ACCESS_MODE = "groups"
$env:MERGE_ACCESS_MODE = "groups"
python main.py
```

### Interactive usage

If any required environment variable is missing, the script will prompt you for it interactively. You will be asked for:

- Workspace slug
- Atlassian email and API token
- Branches or branch types to protect
- Repository slugs (or leave blank for all)
- Whether to enforce merge checks
- Whether to allow protected branch deletion
- Whether to reset approvals on source branch changes
- Write and merge access modes (`everyone` or `groups`)
- Allowed group slugs (if access mode is `groups`)
- Whether to delete existing branch restrictions before applying new ones

## Environment variables

| Environment Variable               | Description                                                                                     | Required | Default Value |
|------------------------------------|-------------------------------------------------------------------------------------------------|----------|----------------|
| ATLASSIAN_EMAIL                    | Your Atlassian email address used for authentication                                            | Yes      | None           |
| ATLASSIAN_API_TOKEN                | Your Atlassian API token used for authentication                                                | Yes      | None           |
| WORKSPACE                          | Your Bitbucket workspace slug                                                                   | Yes      | None           |
| ALLOW_GROUPS                       | Comma-separated list of groups allowed to push/merge to protected branches                      | Required if WRITE_ACCESS_MODE or MERGE_ACCESS_MODE is "groups" | None |
| BRANCHES                           | Comma-separated list of branches or branch patterns to protect (e.g., `main,release/*`)         | Either BRANCHES or BRANCH_TYPES | None |
| BRANCH_TYPES                       | Comma-separated list of branch types (production, development, feature, release, hotfix)        | Either BRANCHES or BRANCH_TYPES | None |
| ALLOW_BRANCH_DELETE                | Set to "yes" to allow deleting protected branches, "no" to prevent deletion                     | No       | no             |
| ENFORCE_MERGE_CHECKS               | Set to "yes" to enforce merge checks, only available for Bitbucket Premium plans                | No       | no             |
| RESET_APPROVALS_ON_CHANGE          | Set to "yes" to reset approvals after changes in source branch                                  | No       | None           |
| CONFIRM_DELETE_EXISTING_RULES      | Set to "yes" to always delete existing branch restrictions, "no" to always keep them, unset for interactive prompt | No       | None |
| REPOSITORIES                       | Comma-separated list of repositories that you want to run this script for                       | No       | None           |
| WRITE_ACCESS_MODE                  | Who can push to protected branches: "everyone" or "groups"                                     | No       | everyone       |
| MERGE_ACCESS_MODE                  | Who can merge to protected branches: "everyone" or "groups"                                    | No       | everyone       |

## Notes

- If both `BRANCHES` and `BRANCH_TYPES` are set, the script will exit with an error.
- If `WRITE_ACCESS_MODE` or `MERGE_ACCESS_MODE` is set to "groups", `ALLOW_GROUPS` must be provided.
- The script will prompt for any missing required values.
- Existing branch restrictions can be deleted interactively or automatically based on `CONFIRM_DELETE_EXISTING_RULES`.

## Example workflow

1. Set environment variables as needed.
2. Run the script: `python3 main.py`
3. Follow prompts if any required values are missing.
