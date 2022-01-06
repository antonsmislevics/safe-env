from . import BaseValue
from typing import Dict


class TemplatedValue(BaseValue):
    def __init__(self, type_name: str, name: str, value_template: str, value_providers: Dict):
        super().__init__(type_name, name)
        if value_template is None:
            value_template = ""
        self.value_template = value_template
        self.value_providers = value_providers

    def _get_value(self):
        value = self.value_template.format_map(self.value_providers)
        return value
