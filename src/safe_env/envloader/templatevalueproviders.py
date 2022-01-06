from typing import List
from .valueproviders import BaseValueProvider


class TemplateValueProviders(dict):
    def __init__(self, providers: List[BaseValueProvider] = None):
        if not(providers):
            providers = []
        self.providers = providers
    
    def register(self, provider: BaseValueProvider):
        self.providers.append(provider)

    def __getitem__(self, item):
        alias = item
        if alias:
            alias = alias.strip().upper()
        provider = next((x for x in self.providers if alias in x.aliases), None)
        if provider:
            return provider
        else:
            raise Exception(f"Unknown value provider alias: '{item}'.")
