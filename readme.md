# Bitbucket Branch Lockdown Automation

A tool to automate the setup of branch protection rules across all repositories in a Bitbucket workspace.

## Getting Started

### Step 1: Create an Atlassian API Token

1. Go to [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Set a name and expiry date for the token
4. Select **Bitbucket** as the product
5. Select the following scopes:
   - `read:repository:bitbucket`
   - `write:repository:bitbucket`
   - `admin:repository:bitbucket`
6. Create the token and **copy it immediately** (you won't be able to see it again)

### Step 2: Gather Required Information

Before running the tool, you'll need:

- **Atlassian Email**: Your Atlassian account email
- **API Token**: The token you just created
- **Workspace Slug**: Your Bitbucket workspace name (found in your workspace URL)
- **Group Names**: Workspace groups that should have push access to protected branches

### Step 3: Download and Run

1. Download the latest binary for your platform from the [Releases page](../../releases/latest):
   - **Windows**: `bitbucket-branch-lockdown-windows-amd64.exe`
   - **macOS**: `bitbucket-branch-lockdown-macos-amd64` or `bitbucket-branch-lockdown-macos-arm64`
   - **Linux**: `bitbucket-branch-lockdown-linux-amd64`

2. Make the binary executable (Linux/macOS only):

   ```bash
   chmod +x bitbucket-branch-lockdown-*
   ```

3. Set environment variables and run:

**Linux/macOS:**

```bash
export ATLASSIAN_EMAIL="your-email@example.com"
export ATLASSIAN_API_TOKEN="your_api_token_here"
export WORKSPACE="your-workspace-slug"
export ALLOW_GROUPS="managers,senior-developers"
export BRANCH_TYPES="production,development"

# Run the tool
./bitbucket-branch-lockdown-linux-amd64
# or for macOS: ./bitbucket-branch-lockdown-macos-amd64 or bitbucket-branch-lockdown-macos-arm64
```

**Windows (Command Prompt):**
```cmd
set ATLASSIAN_EMAIL=your-email@example.com
set ATLASSIAN_API_TOKEN=your_api_token_here
set WORKSPACE=your-workspace-slug
set ALLOW_GROUPS=managers,senior-developers
set BRANCH_TYPES=production,development

bitbucket-branch-lockdown-windows-amd64.exe
```

**Windows (PowerShell):**
```powershell
$env:ATLASSIAN_EMAIL="your-email@example.com"
$env:ATLASSIAN_API_TOKEN="your_api_token_here"
$env:WORKSPACE="your-workspace-slug"
$env:ALLOW_GROUPS="managers,senior-developers"
$env:BRANCH_TYPES="production,development"

.\bitbucket-branch-lockdown-windows-amd64.exe
```

## Recommended Workflow

This tool helps you implement a secure branching strategy across all repositories in your workspace. Here's what it does:

1. **Protects critical branches** (production, development, etc.)
2. **Requires approvals** before merging pull requests
3. **Prevents force pushes** and history rewriting
4. **Controls who can delete** protected branches
5. **Ensures only authorized groups** can push directly

### Basic Configuration

The most common setup protects production and development branches:

```bash
# Required settings
export ATLASSIAN_EMAIL="your-email@example.com"
export ATLASSIAN_API_TOKEN="your_api_token"
export WORKSPACE="your-workspace-slug"
export ALLOW_GROUPS="managers"
export BRANCH_TYPES="production,development"

# Optional settings
export ALLOW_BRANCH_DELETE="no"                    # Prevent branch deletion
export CONFIRM_DELETE_EXISTING_RULES="yes"         # Auto-confirm rule cleanup
export ENFORCE_MERGE_CHECKS="yes"                  # Requires Bitbucket Premium
```

### Advanced Configuration

You can also protect specific branch patterns instead of branch types:

```bash
export BRANCHES="main,master,release/*,hotfix/*"   # Use this instead of BRANCH_TYPES
```

## Configuration Reference

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `ATLASSIAN_EMAIL` | Your Atlassian account email | Yes | `user@company.com` |
| `ATLASSIAN_API_TOKEN` | Your Atlassian API token | Yes | `ATB...xyz` |
| `WORKSPACE` | Bitbucket workspace slug | Yes | `my-company` |
| `ALLOW_GROUPS` | Groups allowed to push (comma-separated) | Yes | `managers,leads` |
| `BRANCH_TYPES` | Branch types to protect | Either this or `BRANCHES` | `production,development` |
| `BRANCHES` | Specific branches/patterns to protect | Either this or `BRANCH_TYPES` | `main,release/*` |
| `ALLOW_BRANCH_DELETE` | Allow deleting protected branches | No | `yes` or `no` (default: `no`) |
| `ENFORCE_MERGE_CHECKS` | Enforce merge checks (Premium only) | No | `yes` or `no` (default: `no`) |
| `CONFIRM_DELETE_EXISTING_RULES` | Auto-confirm rule deletion | No | `yes`, `no`, or unset for prompt |

## Development Setup

If you want to modify the tool or run it from source:

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/leandro-lorenzini/bitbucket-branch-lockdown.git
   cd bitbucket-branch-lockdown
   ```

2. Create and activate a virtual environment:

   **Linux/macOS:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **Windows:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run from source:
   ```bash
   python main.py
   ```

### Building Binaries

To build your own binaries:

```bash
pip install pyinstaller
pyinstaller --onefile --name bitbucket-branch-lockdown main.py
```

The binary will be created in the `dist/` directory.

### Creating Releases

New releases with pre-built binaries are automatically created when you push a version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This triggers a GitHub Actions workflow that builds binaries for all platforms and creates a release.
