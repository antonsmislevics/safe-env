from typing import Dict
from .values import TemplatedValue


class TemplatedConfigurationMixin():
    def __init__(self, templated_args: Dict[str, str], templated_args_value_providers: Dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._templated_args = templated_args
        self._templated_args_value_providers = templated_args_value_providers
        self._is_templated_config_loaded = False


    def ensure_templated_config_loaded(self):
        if not(self._is_templated_config_loaded):
            if self._templated_args:
                for key, value_template in self._templated_args.items():
                    if hasattr(self, key):
                        current_value = getattr(self, key)
                        if current_value is None and value_template:
                            new_value = TemplatedValue(None,
                                                    f"templated_prop_{key}",
                                                    value_template,
                                                    self._templated_args_value_providers).get_value()
                            setattr(self, key, new_value)
            self._is_templated_config_loaded = True
            self.on_templated_config_loaded()


    def on_templated_config_loaded(self):
        pass