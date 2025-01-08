from .. import cache_providers

KNOWN_CACHE_CLASSES = {
    "memory": cache_providers.MemoryCache,
    "keyring": cache_providers.KeyringCache,
    "azure.keyvault": cache_providers.AzureKeyVaultSecretCache
}
