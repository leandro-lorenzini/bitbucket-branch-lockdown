#!/usr/bin/env python3
"""
bitbucket_lockdown.py
- Applies branch restrictions to 'main' and 'master' across all repos in a workspace.
- Auth: Atlassian account API token (Basic: email + token).
"""

import os
import sys
import time
import argparse
from typing import Dict, Any, Iterable, List, Optional, Set, Tuple

import requests
from requests.auth import HTTPBasicAuth

# ------------- CONFIG (edit these or use CLI args/envs) -----------------
WORKSPACE = os.getenv("WORKSPACE")
ALLOW_GROUPS = (os.getenv("ALLOW_GROUPS") or "").split(",") # Workspace group slugs
BRANCHES = (os.getenv("BRANCHES") or "").split(",")
BRANCH_TYPES = os.getenv("BRANCH_TYPES", "").strip()
ATLASSIAN_EMAIL = os.getenv("ATLASSIAN_EMAIL")
ATLASSIAN_API_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")
ENFORCE_MERGE_CHECKS = os.getenv("ENFORCE_MERGE_CHECKS", "").lower() in ("1", "true", "yes")
ALLOW_BRANCH_DELETE = os.getenv("ALLOW_BRANCH_DELETE", "").lower() in ("1", "true", "yes")

BASE = "https://api.bitbucket.org/2.0"
PAGELEN = 100
PAUSE = 0.12  # polite pacing between POSTs
# -----------------------------------------------------------------------


def die(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def check_required_envs():
    missing = []
    if not WORKSPACE:
        missing.append("WORKSPACE")
    # ALLOW_GROUPS is now optional
    branch_types = [t.strip() for t in BRANCH_TYPES.split(",") if t.strip()]
    branches_set = BRANCHES and BRANCHES != [""] and any(BRANCHES)
    branch_type_set = bool(branch_types)
    # Only require one, not both
    if branches_set and branch_type_set:
        die("Set only one of BRANCHES or BRANCH_TYPES, never both.")
    if not branches_set and not branch_type_set:
        missing.append("BRANCHES or BRANCH_TYPES")
    if not ATLASSIAN_EMAIL:
        missing.append("ATLASSIAN_EMAIL")
    if not ATLASSIAN_API_TOKEN:
        missing.append("ATLASSIAN_API_TOKEN")
    # Optionally: ENFORCE_MERGE_CHECKS is not required
    if missing:
        die(f"Missing required env vars: {', '.join(missing)}")


def http_get(url: str, auth: HTTPBasicAuth, headers: Dict[str, str]) -> requests.Response:
    r = requests.get(url, auth=auth, headers=headers)
    r.raise_for_status()
    return r


def http_post(url: str, auth: HTTPBasicAuth, headers: Dict[str, str], payload: Dict[str, Any]) -> requests.Response:
    r = requests.post(url, auth=auth, headers=headers, json=payload)
    return r


def get_all_repos(workspace: str, auth: HTTPBasicAuth, headers: Dict[str, str]) -> Iterable[Dict[str, Any]]:
    url = f"{BASE}/repositories/{workspace}?pagelen={PAGELEN}"
    while url:
        resp = http_get(url, auth, headers)
        data = resp.json()
        for repo in data.get("values", []):
            yield repo
        url = data.get("next")


def list_branch_restrictions(workspace: str, repo_slug: str,
                             auth: HTTPBasicAuth, headers: Dict[str, str]) -> List[Dict[str, Any]]:
    url = f"{BASE}/repositories/{workspace}/{repo_slug}/branch-restrictions?pagelen={PAGELEN}"
    out: List[Dict[str, Any]] = []
    while url:
        resp = http_get(url, auth, headers)
        j = resp.json()
        out.extend(j.get("values", []))
        url = j.get("next")
    return out


def create_branch_restriction(workspace: str, repo_slug: str, rule: Dict[str, Any],
                              auth: HTTPBasicAuth, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    url = f"{BASE}/repositories/{workspace}/{repo_slug}/branch-restrictions"
    r = http_post(url, auth, headers, rule)

    if r.status_code in (200, 201):
        print(f"   [+] Created: {rule['kind']} on {repo_slug}:{rule.get('pattern') or rule.get('branch_type')}")
        return r.json()

    # Premium-only features or plan restrictions commonly return 403
    if r.status_code == 403:
        print(f"   [WARN] 403 creating {rule['kind']} on {repo_slug}: {r.text.strip()[:400]}")
        return None

    # Anything else -> log succinctly
    print(f"   [ERR ] {r.status_code} creating {rule['kind']} on {repo_slug}: {r.text.strip()[:400]}")
    return None


def get_repo_group_permissions(workspace: str, repo_slug: str, auth: HTTPBasicAuth, headers: Dict[str, str]) -> Set[str]:
    url = f"{BASE}/repositories/{workspace}/{repo_slug}/permissions-config/groups?pagelen={PAGELEN}"
    groups = set()
    while url:
        resp = http_get(url, auth, headers)
        data = resp.json()
        for entry in data.get("values", []):
            group = entry.get("group", {})
            slug = group.get("slug")
            if slug:
                groups.add(slug)
        url = data.get("next")
    return groups


def add_group_to_repo(workspace: str, repo_slug: str, group_slug: str, auth: HTTPBasicAuth, headers: Dict[str, str]) -> None:
    url = f"{BASE}/repositories/{workspace}/{repo_slug}/permissions-config/groups/{group_slug}"
    payload = {"permission": "write"}  # "write" is sufficient for branch restrictions
    r = requests.put(url, auth=auth, headers=headers, json=payload)
    if r.status_code in (200, 201, 204):
        print(f"   [+] Added group '{group_slug}' to repo '{repo_slug}'")
    elif r.status_code == 409:
        print(f"   [=] Group '{group_slug}' already has permission on repo '{repo_slug}'")
    else:
        print(f"   [WARN] Could not add group '{group_slug}' to repo '{repo_slug}': {r.text.strip()[:400]}")


def ensure_groups_in_repo(workspace: str, repo_slug: str, allow_groups: List[str], auth: HTTPBasicAuth, headers: Dict[str, str]) -> None:
    existing_groups = get_repo_group_permissions(workspace, repo_slug, auth, headers)
    for group_slug in allow_groups:
        if group_slug and group_slug not in existing_groups:
            add_group_to_repo(workspace, repo_slug, group_slug, auth, headers)


def ensure_rules_for_branch(workspace: str, repo_slug: str, branch_or_type: str,
                            allow_groups: List[str],
                            auth: HTTPBasicAuth, headers: Dict[str, str],
                            use_branch_type: bool = False) -> None:
    # Ensure all groups are added to the repo before applying restrictions
    # Only ensure groups if any are specified
    if allow_groups:
        ensure_groups_in_repo(workspace, repo_slug, allow_groups, auth, headers)

    if use_branch_type:
        common = {"branch_match_kind": "branching_model", "branch_type": branch_or_type}
    else:
        common = {"branch_match_kind": "glob", "pattern": branch_or_type}

    rules_to_apply: List[Dict[str, Any]] = []
    # 1) Write access: only specific groups can PUSH, or block all if none specified
    if allow_groups:
        rules_to_apply.append({
            "kind": "push",
            **common,
            "groups": [{"slug": g.strip()} for g in allow_groups if g.strip()],
        })
    else:
        # No groups specified: block all non-admins from pushing
        rules_to_apply.append({
            "kind": "push",
            **common,
            "groups": [],
            "users": [],
        })
    # 2) Prevent deleting this branch unless ALLOW_BRANCH_DELETE is set
    if not ALLOW_BRANCH_DELETE:
        rules_to_apply.append({
            "kind": "delete",
            **common,
        })
    # 3) Prevent rewriting branch history (force push)
    rules_to_apply.append({
        "kind": "force",
        **common,
    })
    # 4) Minimum approvals: set to 1
    rules_to_apply.append({
        "kind": "require_approvals_to_merge",
        **common,
        "value": 1,
    })
    # 5) Reset requested changes when source branch is modified
    rules_to_apply.append({
        "kind": "reset_pullrequest_changes_requested_on_change",
        **common,
    })
    if ENFORCE_MERGE_CHECKS:
        rules_to_apply.append({
            "kind": "enforce_merge_checks",
            **common,
        })

    existing = list_branch_restrictions(workspace, repo_slug, auth, headers)
    existing_keys: Set[Tuple[Any, Any, Any, Any]] = {
        (r.get("kind"), r.get("branch_match_kind"), r.get("pattern"), r.get("branch_type")) for r in existing
    }

    for rule in rules_to_apply:
        key = (rule["kind"], rule["branch_match_kind"], rule.get("pattern"), rule.get("branch_type"))
        if key in existing_keys:
            print(f"   [=] Exists:  {rule['kind']} on {repo_slug}:{branch_or_type}")
            continue
        create_branch_restriction(workspace, repo_slug, rule, auth, headers)
        time.sleep(PAUSE)


def delete_branch_restriction(workspace: str, repo_slug: str, restriction_id: str,
                              auth: HTTPBasicAuth, headers: Dict[str, str]) -> None:
    url = f"{BASE}/repositories/{workspace}/{repo_slug}/branch-restrictions/{restriction_id}"
    r = requests.delete(url, auth=auth, headers=headers)
    if r.status_code in (200, 204):
        print(f"   [-] Deleted restriction {restriction_id} on {repo_slug}")
    else:
        print(f"   [ERR ] {r.status_code} deleting restriction {restriction_id} on {repo_slug}: {r.text.strip()[:400]}")


CONFIRM_DELETE_EXISTING_RULES = os.getenv("CONFIRM_DELETE_EXISTING_RULES", "").lower()

def prompt_delete_existing_restrictions(workspace: str, repo_slug: str, auth: HTTPBasicAuth, headers: Dict[str, str]) -> None:
    restrictions = list_branch_restrictions(workspace, repo_slug, auth, headers)
    if restrictions:
        print(f"\n[!] Repository '{repo_slug}' has {len(restrictions)} existing branch restriction(s).")
        if CONFIRM_DELETE_EXISTING_RULES == "yes":
            ans = "y"
        elif CONFIRM_DELETE_EXISTING_RULES == "no":
            ans = "n"
        else:
            ans = input("    Delete all existing restrictions before applying new ones? [y/N]: ").strip().lower()
        if ans == "y":
            for r in restrictions:
                delete_branch_restriction(workspace, repo_slug, r["id"], auth, headers)


def main():
    check_required_envs()
    parser = argparse.ArgumentParser(description="Apply Bitbucket branch restrictions across repos.")
    parser.add_argument("--workspace", default=WORKSPACE, help="Workspace slug")
    parser.add_argument("--branches", default=",".join(BRANCHES),
                        help="Comma-separated list of branches to protect")
    parser.add_argument("--groups", default=",".join(ALLOW_GROUPS),
                        help="Comma-separated workspace group slugs allowed to push/merge")
    parser.add_argument("--branch-type", default=BRANCH_TYPES,
                        help="Comma-separated Bitbucket branch types to protect (e.g. production,development,feature,release,hotfix)")
    parser.add_argument("--only", default="", help="Comma-separated repo slugs to limit scope (optional)")
    args = parser.parse_args()

    workspace = args.workspace.strip()
    branches = [b.strip() for b in args.branches.split(",") if b.strip()]
    allow_groups = [g.strip() for g in args.groups.split(",") if g.strip()]
    only = {r.strip() for r in args.only.split(",") if r.strip()}

    branch_types = [t.strip() for t in args.branch_type.split(",") if t.strip()]
    use_branch_type = bool(branch_types)
    branch_items = branch_types if use_branch_type else branches

    auth = HTTPBasicAuth(ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    print(f"[INFO] Workspace: {workspace}")
    if use_branch_type:
        print(f"[INFO] Branch types: {branch_types}")
    else:
        print(f"[INFO] Branches:  {branches}")
    print(f"[INFO] Groups:    {allow_groups or '(none)'}")
    if only:
        print(f"[INFO] Limiting to repos: {sorted(only)}")

    try:
        for repo in get_all_repos(workspace, auth, headers):
            slug = repo["slug"]
            if only and slug not in only:
                continue
            print(f"\n==> {slug}")
            prompt_delete_existing_restrictions(workspace, slug, auth, headers)
            for br in branch_items:
                ensure_rules_for_branch(workspace, slug, br, allow_groups, auth, headers, use_branch_type)
    except requests.HTTPError as e:
        die(f"[HTTP ERROR] {e} | body={getattr(e.response, 'text', '')[:400]}")
    except KeyboardInterrupt:
        die("\n[ABORTED] by user", 130)


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
