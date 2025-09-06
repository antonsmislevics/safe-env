from typing import List, Dict, Any
from keepercommander import api, subfolder
from keepercommander.api import KeeperParams


def get_keeper_secrets(
    login_params: KeeperParams,
    names: List[str] = None
) -> Dict[str, Any]:
    if names is None:
        return None

    result = dict()
    for record_name in names:
        record_uid = None
        record_info = subfolder.try_resolve_path(login_params, record_name)
        if record_info:
            # record_info is a tuple (subfolder.BaseFolderNode, record title)
            folder, record_title = record_info
            # params.subfolder_record_cache holds record uids for every folder
            for uid in login_params.subfolder_record_cache[folder.uid or '']:
                # load a record by record UID
                r = api.get_record(login_params, uid)
                # compare record title with the last component of the full record path
                if r.title.casefold() == record_title.casefold():
                    record_uid = uid
                    break
        if not record_uid:
            raise Exception(f"Cannot retrieve Keeper Record UID for '{record_name}'")
        else:
            record = api.get_record(login_params, record_uid)
            result[record_name] = record.to_dictionary()
    return result


def get_keeper_secrets_by_uids(
    login_params: KeeperParams,
    uids: List[str] = None
) -> Dict[str, Any]:
    if uids is None:
        return None

    result = dict()
    for record_uid in uids:
        record = api.get_record(login_params, record_uid)
        result[record_uid] = record.to_dictionary()
    return result
