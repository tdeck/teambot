#!/usr/bin/env python

# This code is mostly from the rtmbot project; it handles the lower-level
# details of interacting with the Slack socket API, and imports the bot
# logic from teambot.py. It is also the application entry point.

import sys
sys.dont_write_bytecode = True

import daemon
import logging
import os
import time
import yaml
from argparse import ArgumentParser

from slackclient import SlackClient

import teambot

CONFIG_STRING_KEYS = [
    'SLACK_TOKEN',
    'LOGFILE',
    'TEAM_DB_FILE',
]

CONFIG_FLAGS = [
    'DEBUG',
    'DAEMON',
]

# Globals used by rtmbot
config = {}
debug = False

def dbg(debug_string):
    if debug:
        logging.info(debug_string)

class RtmBot(object):
    def __init__(self, token):
        self.last_ping = 0
        self.token = token
        self.bot_plugins = []
        self.slack_client = None

    def connect(self):
        """Convenience method that creates Server instance"""
        self.slack_client = SlackClient(self.token)
        self.slack_client.rtm_connect()

    def start(self):
        self.connect()
        self.load_plugins()
        while True:
            for reply in self.slack_client.rtm_read():
                self.input(reply)
            self.output()
            self.autoping()
            time.sleep(.1)

    def autoping(self):
        #hardcode the interval to 3 seconds
        now = int(time.time())
        if now > self.last_ping + 3:
            self.slack_client.server.ping()
            self.last_ping = now

    def input(self, data):
        if "type" in data:
            function_name = "process_" + data["type"]
            dbg("got {}".format(function_name))
            for plugin in self.bot_plugins:
                plugin.do(function_name, data)

    def output(self):
        for plugin in self.bot_plugins:
            limiter = False
            for output in plugin.do_output():
                channel = self.slack_client.server.channels.find(output[0])
                if channel != None and output[1] != None:
                    if limiter:
                        time.sleep(.1)
                        limiter = False
                    message = output[1].encode('ascii', 'ignore')
                    channel.send_message("{}".format(message))
                    limiter = True

    def load_plugins(self):
        self.bot_plugins.append(Plugin(teambot, self))

class Plugin(object):
    def __init__(self, module, bot):
        self.module = module
        name = module.__name__
        self.name = name

        self.outputs = []
        if 'setup' in dir(self.module):
            self.module.setup(bot, config)

    def do(self, function_name, data):
        if function_name in dir(self.module):
            # This makes the plugin fail with stack trace in debug mode
            if not debug:
                try:
                    eval("self.module."+function_name)(data)
                except:
                    dbg("problem in module {} {}".format(function_name, data))
            else:
                eval("self.module."+function_name)(data)

        if "catch_all" in dir(self.module):
            try:
                self.module.catch_all(data)
            except:
                dbg("problem in catch all")

    def do_output(self):
        output = []
        while True:
            if 'outputs' in dir(self.module):
                if len(self.module.outputs) > 0:
                    logging.info("output from {}".format(self.module))
                    output.append(self.module.outputs.pop(0))
                else:
                    break
            else:
                self.module.outputs = []
        return output

class UnknownChannel(Exception):
    pass

def main_loop(bot, logfile=None):
    logging_conf = {
        'level': logging.INFO,
        'format': '%(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        'handlers': [logging.StreamHandler()],
    }

    if logfile:
        logging_conf['filename'] = logfile

    logging.basicConfig(**logging_conf)

    try:
        bot.start()
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        logging.exception('OOPS')

def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        help='Full path to config file.',
        metavar='path'
    )
    return parser.parse_args()

def flag_is_true(flag_str):
    """ Checks if a string flag should evaluate to True. """
    flag_str = flag_str.strip().lower()
    return flag_str == 'true' or flag_str == '1'

def invoke():
    """ Starts the bot. The entry point into the app. """
    global config
    global debug

    args = parse_args()

    # Try to load config from a specified file, or rtmbot.conf if
    # it exists in the working directory.
    using_file_config = False
    if args.config:
        using_file_config = True
        config = yaml.load(open(args.config))
    elif os.path.isfile('rtmbot.conf'):
        using_file_config = True
        config = yaml.load(open('rtmbot.conf'))

    # Set or override values with config from the environment

    # String values are copied over as-is
    using_env_config = False
    for k in CONFIG_STRING_KEYS:
        if k in os.environ:
            using_env_config = True
            config[k] = os.environ[k]

    # Sometimes you may want to use a config file and override things
    # during development (e.g. DEBUG). However, this can also be a source
    # of unexpected behavior, so we display a warning.
    if using_file_config and using_env_config:
        print(
            "WARNING: You are using a mixture of configuration "
            "from both the environment\n"
            "and a config file. Check to ensure that this is "
            "what you intend to do."
        )

    # Boolean flags are coerced by checking that they are some
    # variant of the string "true"
    for k in CONFIG_FLAGS:
        if k in os.environ:
            config[k] = flag_is_true(os.environ[k])

    if 'SLACK_TOKEN' not in config:
        print(
            "Missing required config value SLACK_TOKEN."
            " See README.md for details."
        )
        return

    debug = config.get('DEBUG')
    bot = RtmBot(config["SLACK_TOKEN"])
    logfile = config.get('LOGFILE')

    if config.get("DAEMON"):
        with daemon.DaemonContext():
            main_loop(bot, logfile)
            return

    main_loop(bot, logfile)

if __name__ == "__main__":
    invoke()
