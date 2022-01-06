
from ..models import EnvironmentConfiguration
from .vaults import KeyringVault, AzureKeyVault
from .valueproviders import HostEnvValueProvider, ParamValueProvider, TemplatedValueProvider, SecretValueProvider
from .templatevalueproviders import TemplateValueProviders
from .values import ValueStatus


class EnvironmentLoader():
    def __init__(self, config: EnvironmentConfiguration, force_reload_from_remote=False):
        self.force_reload_from_remote = force_reload_from_remote

        self.config = config
        self.value_providers = TemplateValueProviders()
        self.keyring = None
        if self.config.config and self.config.config.keyring:
            self.keyring = KeyringVault()
        # TODO: rework vault initialization from config
        self.vaults = [AzureKeyVault(name=x.name) for x in self.config.vaults]

        self.host_env_value_provider = HostEnvValueProvider(error_on_missing_value=False)
        self.param_value_provider = ParamValueProvider(templated_value_dict=self.config.parameters,
                                                  value_providers=self.value_providers,
                                                  error_on_missing_value=True)
        self.secret_value_provider = SecretValueProvider(secrets=self.config.secrets,
                                                    value_providers=self.value_providers, 
                                                    keyring=self.keyring,
                                                    vaults=self.vaults,
                                                    force_reload_from_remote=self.force_reload_from_remote,
                                                    error_on_missing_value=True)
        
        # TODO: add value_providers to generate random values (for example, random guid, random string, random value from dictionary, etc.)
        # random values could also have additional parameters as from-to - perhaps specified in separate section VALUE_GENERATORS/RANDOM (similar as for secrets)
        self.value_providers.register(self.host_env_value_provider)
        self.value_providers.register(self.param_value_provider)
        self.value_providers.register(self.secret_value_provider)

        if self.keyring:
            self.keyring.load_from_settings(self.config.config.keyring, value_providers=self.value_providers)

        for i, vault in enumerate(self.vaults):
            vault.load_from_settings(self.config.vaults[i], value_providers=self.value_providers)
        
        self.env_value_provider = TemplatedValueProvider(aliases=[], templated_value_dict=self.config.env, value_providers=self.value_providers)

    def load_envs_and_secrets(self):
        env_dict = {}
        for name, value in self.env_value_provider.values.items():
            env_dict[name] = value.get_value()
        
        remote_secrets = {}
        for name, secret_value in self.secret_value_provider.values.items():
            if secret_value.status == ValueStatus.Loaded and secret_value.id:
                remote_secrets[name] = secret_value.id

        local_only_secrets = {}
        remote_cached_secrets = {}
        for name, secret_value in self.secret_value_provider.values.items():
            value = {"service_name": secret_value.get_service_name(), "name": secret_value.name_in_keyring}
            if secret_value.is_local_only:
                local_only_secrets[name] = value
            else:
                remote_cached_secrets[name] = value

        return env_dict, remote_secrets, local_only_secrets, remote_cached_secrets
