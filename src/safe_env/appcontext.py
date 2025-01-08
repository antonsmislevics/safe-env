import sys
import logging
from pathlib import Path
from .envmanager import EnvironmentManager

class AppContext():
    def __init__(self, config_dir: Path = None, verbose: bool = False):
        if not(config_dir):
            config_dir = Path("envs")
            
        self.config_dir = config_dir
        self.plugins_dir = config_dir.joinpath("plugins")
        self.verbose = verbose
        self.command_mode = False
        self.envman = None


    def switch_output_to_command_mode(self):
        self.command_mode = True


    def load(self):
        self._configure_logging()
        self._load_env_man()        


    def _load_env_man(self):
        self.envman = EnvironmentManager()
        self.envman.load_from_folder(self.config_dir)
        self.envman.load_plugins(self.plugins_dir)


    def _configure_logging(self):
        if self.command_mode and not(self.verbose):
            # no log messages are written in an output that will be used as command
            logging.disable(level=logging.CRITICAL)
            return
    
        stdout_handler = logging.StreamHandler(sys.stdout)
        handlers = [stdout_handler]

        logging.basicConfig(
            level=logging.INFO if self.verbose else logging.WARNING, 
            # format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )

    GLOBAL_APP_CONTEXT = None # type: AppContext
    def set_as_global_context(self):
        AppContext.GLOBAL_APP_CONTEXT = self
    
    @staticmethod
    def get_global_context():
        return AppContext.GLOBAL_APP_CONTEXT