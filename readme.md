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

## Recommended Workflow

The following workflow will help you set up branch protection for your main branches (e.g., `production`, `development`), requiring approval before merging, and prevents their deletion.

Use this workflow with caution, as it may delete existing branch restrictions based on your confirmation settings.

#### On Linux or macOS

```bash
export ATLASSIAN_EMAIL="you@example.com"
export ATLASSIAN_API_TOKEN="your_api_token"
export WORKSPACE="your-workspace-slug"
export BRANCH_TYPES="production,development"
export ALLOW_BRANCH_DELETE="no"
export CONFIRM_DELETE_EXISTING_RULES="yes"
python3 main.py
```

### On Windows (PowerShell)

```powershell
$env:ATLASSIAN_EMAIL = "you@example.com"
$env:ATLASSIAN_API_TOKEN = "your_api_token"
$env:WORKSPACE = "your-workspace-slug"
$env:ALLOW_GROUPS = "managers"
$env:BRANCH_TYPES = "production,development"
$env:ALLOW_BRANCH_DELETE = "no"
$env:CONFIRM_DELETE_EXISTING_RULES = "yes"
python main.py
```

## Environment variables

| Environment Variable               | Description                                                                                     | Required | Default Value |
|------------------------------------|-------------------------------------------------------------------------------------------------|----------|----------------|
| ATLASSIAN_EMAIL                    | Your Atlassian email address used for authentication                                            | Yes      | None           |
| ATLASSIAN_API_TOKEN                | Your Atlassian API token used for authentication                                                | Yes      | None           |
| WORKSPACE                          | Your Bitbucket workspace slug                                                                   | Yes      | None           |
| ALLOW_GROUPS                       | Comma-separated list of groups allowed to push to protected branches without a merge request    | No       | None           |
| BRANCHES                           | Comma-separated list of branches or branch patterns to protect (e.g., `main,release/*`)         | Either BRANCHES or BRANCH_TYPE | None |
| BRANCH_TYPE                        | Comma-separated list of branch types (production, development, feature, release, hotfix)        | Either BRANCHES or BRANCH_TYPE | None |
| ALLOW_BRANCH_DELETE                | Set to "yes" to allow deleting protected branches, "no" to prevent deletion                     | No       | no             |
| ENFORCE_MERGE_CHECKS               | Set to "yes" to enforce merge checks, only available for Bitbucket Premium plans                | No       | no             |
| CONFIRM_DELETE_EXISTING_RULES      | Set to "yes" to always delete existing branch restrictions, "no" to always keep them, unset for interactive prompt | No       | None |
| REPOSITORIES      | Comma-separated list of repositories that you want to run this script for | No       | None |
| RESET_APPROVALS_ON_CHANGE      | If approvals should be reset on changes in source branch | No       | None |
