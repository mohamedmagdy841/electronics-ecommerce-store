def move_auth_to_accounts(result, generator, request, public):
    """
    Force all /api/v1/auth/* endpoints into the 'Accounts' tag.
    """
    for path, path_item in result.get("paths", {}).items():
        if path.startswith("/api/v1/auth/"):
            for method, operation in path_item.items():
                if isinstance(operation, dict):
                    operation["tags"] = ["Accounts"]
    return result
