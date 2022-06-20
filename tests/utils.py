import os
from configparser import ConfigParser

from sflkit.config import Config

config_tmp = 'tmp.ini'


def get_config(path=None, language=None, events=None, predicates=None, working=None,
               exclude=None, runner=None):
    return parse_config(create_config(path, language, events, predicates, working, exclude, runner))


def create_config(path=None, language=None, events=None, predicates=None, working=None,
                  exclude=None, runner=None):
    config = ConfigParser()
    config['target'] = dict()
    config['events'] = dict()
    config['instrumentation'] = dict()
    config['test'] = dict()

    if path:
        config['target']['path'] = path
    if language:
        config['target']['language'] = language
    if events:
        config['events']['events'] = events
    if predicates:
        config['events']['predicates'] = predicates
    if working:
        config['instrumentation']['path'] = working
    if exclude:
        config['instrumentation']['exclude'] = exclude
    if runner:
        config['test']['runner'] = runner

    return config


def parse_config(config_content: ConfigParser):
    with open(config_tmp, 'w') as fp:
        config_content.write(fp)

    config = Config(config_tmp)

    try:
        os.remove(config_tmp)
    except:
        pass

    return config
