import logging.config
import os
import pathlib

import yaml

parent_directory = pathlib.Path(__file__).parent

with open(str(parent_directory) + os.sep + 'logging.yml') as f:
    logging_config = yaml.safe_load(f)

logging.config.dictConfig(logging_config)
