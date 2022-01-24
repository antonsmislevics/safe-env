from typing import Callable
from ..models import EnvironmentConfiguration, VaultConfig, ResourceConfig, SecretConfig
from .vaults import KeyringVault, DelayedLoadVault
from .valueproviders import HostEnvValueProvider, ParamValueProvider, TemplatedValueProvider, SecretValueProvider, ResourceValueProvider
from .templatevalueproviders import TemplateValueProviders
from .values import ValueStatus


class EnvironmentLoader():
    def __init__(self,
                 config: EnvironmentConfiguration,
                 get_resource_template_delegate: Callable,
                 force_reload_from_remote: bool=False,
                 force_reload_secrets: bool = False,
                 force_reload_resources: bool = False,
                 do_not_cache_resources: bool = False, 
                 do_not_cache_secrets: bool = False):
        self.force_reload_from_remote = force_reload_from_remote
        self.force_reload_secrets = force_reload_secrets
        self.force_reload_resources = force_reload_resources
        self.do_not_cache_resources = do_not_cache_resources
        self.do_not_cache_secrets = do_not_cache_secrets

        self.config = config
        self.value_providers = TemplateValueProviders()
        self.keyring = None
        if self.config.config and self.config.config.keyring:
            self.keyring = KeyringVault.load_from_config(settings=self.config.config.keyring, value_providers=self.value_providers)

        self.vaults = [DelayedLoadVault.load_from_config(settings=VaultConfig(name=key, **value.dict()),
                                                         value_providers=self.value_providers)
                       for key, value in self.config.vaults.items()]

        self.host_env_value_provider = HostEnvValueProvider(error_on_missing_value=False)
        self.value_providers.register(self.host_env_value_provider)

        self.param_value_provider = ParamValueProvider(templated_value_dict=self.config.parameters,
                                                       value_providers=self.value_providers,
                                                       error_on_missing_value=True)
        self.value_providers.register(self.param_value_provider)

        self.secret_value_provider = SecretValueProvider(secrets=[SecretConfig(name=key, **value.dict()) for key, value in self.config.secrets.items()],
                                                         value_providers=self.value_providers, 
                                                         keyring=self.keyring,
                                                         vaults=self.vaults,
                                                         force_reload_from_remote=(self.force_reload_from_remote or self.force_reload_secrets),
                                                         do_not_cache=self.do_not_cache_secrets,
                                                         error_on_missing_value=True)
        self.value_providers.register(self.secret_value_provider)

        self.resource_value_provider = ResourceValueProvider(resources=[ResourceConfig(name=key, **value.dict()) for key, value in self.config.resources.items()],
                                                             secret_values=self.secret_value_provider.values,
                                                             get_resource_template_delegate=get_resource_template_delegate,
                                                             value_providers=self.value_providers,
                                                             force_reload_from_remote=(self.force_reload_from_remote or self.force_reload_resources),
                                                             do_not_cache=self.do_not_cache_resources,
                                                             error_on_missing_value=True)
        self.value_providers.register(self.resource_value_provider)

        # TODO: add value_providers to generate random values (for example, random guid, random string, random value from dictionary, etc.)
        # random values could also have additional parameters as from-to - perhaps specified in separate section VALUE_GENERATORS/RANDOM (similar as for secrets)

        
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
