from typing import Any, Dict, List

import keyring


def get_keyring_secrets(
    names: List[str],
    keyring_type: str = None,
    service_name: str = None
) -> Dict[str, Any]:
    # TODO: Currently is using default OS keyring.
    #       Implement custom keyrings with keyring.set_keyring() with correct keyring type.
    if names is None:
        return None
    
    result = dict()
    for name in names:
        value = keyring.get_password(service_name, name)
        result[name] = value

    return result
