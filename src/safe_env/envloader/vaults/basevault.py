from abc import abstractmethod

class BaseVault():
    def __init__(self, name: str):
        self._is_ready = True
        self.name = name
        pass

    @property
    def is_ready(self):
        return self._is_ready
    
    @is_ready.setter
    def is_ready(self, value: bool):
        self._is_ready = value

    def get(self, name: str, service_name: str=None) -> str:
        if not(self.is_ready):
            raise Exception(f"Attempted to get value from the vault that is not yet ready. Vault name: {self.name}.")
        return self._get(name, service_name)

    @abstractmethod
    def _get(self, name: str, service_name: str=None) -> str:
        pass

    def set(self, name: str, value: str, service_name: str=None) -> str:
        if not(self.is_ready):
            raise Exception(f"Attempted to set value in the vault that is not yet ready. Vault name: {self.name}.")
        return self._set(name, value, service_name)

    @abstractmethod
    def _set(self, name: str, value: str, service_name: str=None):
        pass

    def delete(self, name: str, service_name: str=None) -> str:
        if not(self.is_ready):
            raise Exception(f"Attempted to delete value from the vault that is not yet ready. Vault name: {self.name}.")
        return self._delete(name, service_name)

    @abstractmethod
    def _delete(self, name: str, service_name: str=None):
        pass
