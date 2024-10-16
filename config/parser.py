#!/usr/bin/env python
import sys
import os
import configparser
import json
from config.env_vars import *

# Configures how to parse configuration file
config_file_name = "config.conf"
config_file_full_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), config_file_name
)
sys.tracebacklimit = 0  # dont show stack traces in prod mode
config = configparser.ConfigParser()
config.optionxform = str  # maintain capitalization of config keys
config.read(config_file_full_path)


def config_section_map(section):
    "Load the config file into a dictionary"
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            value = config.get(section, option)
            # Attempt to parse JSON for dictionary-like values
            try:
                dict1[option] = json.loads(value)
            except json.JSONDecodeError:
                dict1[option] = value
        except Exception as e:
            print(f"Exception on {option}: {e}")
            dict1[option] = None
    return dict1


def cast(value, type_):
    return type_(value)


def get_config_value(key, config_section, is_mandatory, datatype, default_value=None):
    "Return for each key the corresponding value from the Docker Environment or the Config File"
    if IS_IN_DOCKER:
        config_value = os.environ.get(key)
        if config_value is not None:
            config_value = config_value
        elif is_mandatory:
            print(f"[ ERROR ]: Variable not specified in Docker environment: {key}")
            sys.exit(0)
        else:
            config_value = default_value
    else:
        try:
            config_value = config_section_map(config_section).get(key)
        except configparser.NoSectionError:
            config_value = None
        if config_value is not None:
            config_value = config_value
        elif is_mandatory:
            print(
                f"[ ERROR ]: Mandatory variable not specified in config file, section [{config_section}]: {key} (data type: {datatype.__name__})"
            )
            sys.exit(0)
        else:
            config_value = default_value

    # Apply data type
    try:
        if datatype == bool:
            config_value = eval(str(config_value).capitalize())
        elif datatype == list or datatype == dict:
            if not isinstance(config_value, datatype):
                config_value = json.loads(config_value)
        elif config_value is not None:
            config_value = cast(config_value, datatype)
    except Exception as e:
        print(
            f'[ ERROR ]: The value retrieved for [{config_section}]: {key} is "{config_value}" and cannot be converted to data type {datatype}'
        )
        print(e)
        sys.exit(0)
    return config_value
