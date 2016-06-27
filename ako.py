import discord
import asyncio
import configparser
import json
import time
# Import modules needed to get plugins loaded
import sys
import os
import glob

# Make Plugin folder if it does't exist
if not os.path.isdir('plugins'):
    os.makedirs('plugins')

# Make servers.json if it does't exist
if not os.path.isfile('config/servers.json'):
    f = open('config/servers.json', 'w')
    f.close()

# Load plugins folder to system path for this instance of the bot
sys.path.insert(0, os.path.realpath('plugins'))

# Load main configuration file for the bot (BotConfig.ini in the config folder)
loaded_config = False
# Look for config file
if os.path.isfile('config/BotConfig.ini'):
    # Load config if found
    config = configparser.ConfigParser()
    config.read('config/BotConfig.ini')
    loaded_config = True
else:
    # If file not found check if the config folder exists
    if not os.path.isdir('config'):
        os.makedirs('config')
    loaded_config = False

# Dictionary to store all loaded
pluginModules = {}

# Function to import all python files in the plugins folder to be used as plugins
def import_plugins():
    print('-----------------')
    print('Importing plugins')
    print('-----------------')
    # Make a list of every python file in plugins folder
    pluginsLocation = glob.glob('plugins/*.py')

    # Get plugin module name and import it and save to a dictionary
    global pluginModules
    pluginModules = {}
    if pluginsLocation:
        for plugin in pluginsLocation:
            # Get module name
            path = os.path.realpath(plugin)
            (dirname, filename) = os.path.split(path)
            (name, ext) = os.path.splitext(filename)
            # Load Module
            pluginModules[name] = __import__(name)

# First load of plugin modules before bot is started
import_plugins()

# Class for the bot will hold all information for the bot and commands that the bot can do
class Ako(discord.Client):

    # Create all bot variables and load data into some
    def __init__(self):
        # Load info for discord.Client
        super().__init__()
        # Token so bot can login to discord
        self.token = config['MAIN']['Token']
        # Default commandPrefix for servers when the bot joins
        self.defaultPrefix = config['MAIN']['DefaultPrefix']
        # Plugins
        self.plugins = {}
        # Info/Config for each servers
        self.serverConfig = {}

    # Replace built-in run command to include our bot's token
    def start(self):
        return super().start(self.token)

    # Make each plugin an object for the bot
    def load_plugins(self):
        self.plugins = {}
        if pluginModules:
            for name, plugin in pluginModules.items():
                self.plugins[name] = plugin.LoadPlugin(self)
                print('Loaded plugin: {0}'.format(name))

    # Load server config json file
    def load_server_json(self):
        if os.path.isfile('config/servers.json'):
            try:
                with open('config/servers.json') as data_file:
                    self.serverConfig = json.load(data_file)
            except json.decoder.JSONDecodeError:
                self.serverConfig = {}

    # Save server config json file
    def save_server_json(self):
        with open('config/servers.json', 'w') as data_file:
            json.dump(self.serverConfig, data_file)

    # Add server to json file
    def add_server_json(self, server):
        self.serverConfig.update({server.id: {'Prefix': self.defaultPrefix, 'Welcome': True}})
        self.save_server_json()

    # Print Bot username and ID when ready and load any server info if there is any
    async def on_ready(self):
        # Print Bots Name and ID to console
        print('--------------------')
        print('Name: {}'.format(self.user.name))
        print('ID: {}'.format(self.user.id))
        print('--------------------')
        self.load_plugins()
        self.load_server_json()

    # When bot joins server
    async def on_server_join(self, server):
        # Print to console name and ID of server joined
        print('JOINED SERVER: {0.name} ({0.id})'.format(server))
        self.add_server_json(server)

    # When the bot receives a message
    async def on_message(self, message):
        if message.content.startswith(self.serverConfig[message.server.id]['Prefix']):
            commandfull = message.content[1:]
            # Show setting for the server message was sent in
            if commandfull.lower() == 'settings':
                msg = ':gear: Settings for {0}:\nCommand Prefix: ```{1}```\nWelcome User: ```{2}```'
                await self.send_message(message.channel, msg.format(message.server.name, self.serverConfig[message.server.id]['Prefix'], self.serverConfig[message.server.id]['Welcome']))

            # Command to change servers prefix
            elif commandfull.startswith('setprefix'):
                arg = commandfull.replace('setprefix ', '')
                if len(arg) != 1:
                    await self.send_message(message.channel, ':warning: Invalid number of arguments')
                else:
                    self.serverConfig[message.server.id]['Prefix'] = arg
                    self.save_server_json()
                    await self.send_message(message.channel, ':white_check_mark: Prefix changed to {0}'.format(arg))


# Run Bot if configuration file is loaded
if loaded_config:
    run = True
    while run:
        bot = Ako()
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(bot.start())
        except discord.LoginFailure:
            loop.run_until_complete(bot.logout())
            print('--------------------------------------')
            print('Invalid credentials')
            print('Please check token and re-run script')
            run = False
        except discord.ClientException:
            loop.run_until_complete(bot.logout())
            print('--------------------------------------')
            print('Disconnected')
            print('Will try to reconnect after 20 seconds')
            time.sleep(20)
            run = True
        except discord.DiscordException:
            loop.run_until_complete(bot.logout())
            print('--------------------------------------')
            print('Disconnected')
            print('Will try to reconnect after 20 seconds')
            time.sleep(20)
            run = True
        except ConnectionResetError:
            loop.run_until_complete(bot.logout())
            print('--------------------------------------')
            print('Disconnected')
            print('Will try to reconnect after 20 seconds')
            time.sleep(20)
            run = True
        except KeyboardInterrupt:
            loop.run_until_complete(bot.logout())
            print('--------------------------------------')
            print('Disconnected')
            run = False
        finally:
            if run == False:
                loop.close()
else:
    # Print error message if config is not loaded
    print('Error: Config File not loaded')
    print('The Config File "BotConfig.ini" could not be loaded,')
    print('Please make sure the file is in the config folder and is not corrupt')
