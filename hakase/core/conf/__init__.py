"""Core configuration definition

This file is responsible for defining the schema of conf.toml, a file
generated upon first initialization which defines operational settings for Hakase.

    * __VERSION__ - Defines the major version of Hakase
    * __TAG__ - Defines the 'tag' of the version

    * BaseConfig - A base schema which forces order in all inherited schemas
    * LoggingConfigSchema - Schema defining logging configuration
    * ORMConfigSchema - Schema defining configuration for the MVC
    * LavalinkConfigSchema - Schema defining configuration for lavalink
    * VarsConfigSchema - Schema defining a bunch of random settings
    * ConfigSchema - Schema defining the entire configuration
    * Config - Class which constructs the config namespace
"""

import aiofile
import fernet
import os
from marshmallow import Schema, fields, post_load
from types import SimpleNamespace
from pathlib import Path
import toml


from .custom_fields import Timezone, ExistingPath, DiscordUID, LogLevel, TCPIPPort


__VERSION__: str = "0.1.2"
__TAG__: str = "Adaptable Altruist"


class BaseConfig(Schema):
    """BaseConfig simply forces ordering in any subclasses"""
    class Meta:
        ordered = True


class LoggingConfigSchema(BaseConfig):
    """
    Schema defining logging behavior configuration.

    All attributes suffixed with "_level" are enums, essentially,
    and can contain one of 'INFO', 'DEBUG', 'WARNING', or 'CRITICAL'.
    
    Attributes
    ----------
    main_level : str
        The main logging level for the bot.
    hikari_level : str
        The logging level for the Discord API connector.
    mvc_level : str
        The logging level for the model-view controller and HTTP daemon.
    log_format : str
        The format for the logs.
    date_format : str
        The format for dates in logs.
    """
    main_level = LogLevel(dump_default="INFO", required=True)
    hikari_level = LogLevel(dump_default="CRITICAL", required=True)
    mvc_level = LogLevel(dump_default="WARNING", required=True)
    log_format = fields.Str(dump_default='[%(asctime)s][%(levelname)s][%(name)s] %(message)s', required=True)
    date_format = fields.Str(dump_default="%x %X", required=True)


class ORMConfigSchema(BaseConfig):
    """
    Schema defining configuration for the ORM.

    The Object Relational Mapper is the component of the bot which is
    tasked with storing data, but it also controls the model-view controller
    in general.
    
    Attributes
    ----------
    enable_http : boolean
        Whether or not the HTTP daemon should be run.
    fernet_key : str
        The encryption key used to encrypt cookies.
    client_secret : str
        The Discord API client secret used in OAuth2.
    secret_key : str
        The Django secret key used by the MVC.
    host : str
        The host address that the HTTP daemon should bind to.
    port : int
        The TCPIP port that the HTTP daemon should use.
    allowed_hosts : t.List[str]
        A list of "allowed hosts" for the HTTP daemon.
    static_root : str
        A POSIX path indicating the location of HTTP static files.
    upload_root : str
        A POSIX path indicating the location where user file uploads should be stored.
    debug_mode : boolean
        Whether or not the internal MVC should be run in debug mode.
    db_backup_dir : str
        A POSIX path where SQL dump files should be stored during backups.
    db_host : str
        The address of the PostgreSQL server.
    db_port : int
        The TCPIP port of the PostgreSQL server.
    db_user : str
        The PostgreSQL user to use.
    db_pass : str
        The password for the db_user.
    db_name : str
        The name of the database to use.
    """
    enable_http = fields.Boolean(dump_default=True, required=True)
    fernet_key = fields.Str(dump_default=fernet.Fernet.generate_key().decode("utf-8"), required=True)
    client_secret = fields.Str(dump_default="", required=True)
    secret_key = fields.Str(dump_default="", required=True)
    host = fields.Str(dump_default="http://localhost", required=True)
    port = TCPIPPort(dump_default=8080, required=True)
    allowed_hosts = fields.List(fields.Str, required=True)
    static_root = ExistingPath(dump_default=os.path.join(os.getcwd(), "static/"), create=True, required=True)
    upload_root = ExistingPath(dump_default=os.path.join(os.getcwd(), "uploads/"), create=True, required=True)
    debug_mode = fields.Boolean(dump_default=True, required=True)
    db_backup_dir = ExistingPath(dump_default=os.path.join(os.getcwd(), "db_backups/"), create=True, required=True)
    db_host = fields.Str(dump_default="localhost", required=True)
    db_port = fields.Int(dump_default=5432, required=True)
    db_user = fields.Str(dump_default="", required=True)
    db_pass = fields.Str(dump_default="", required=True)
    db_name = fields.Str(dump_default="bot_database", required=True)


class VarsConfigSchema(BaseConfig):
    """
    Variables schema for config files.

    This section of config is dedicated to "miscellaneous" varaibles
    that may be used in commands, but don't fit anywhere else in config.

    Attributes
    ----------
    choose_cmd_expiry_seconds : int
        The amount of time in seconds before an identical /choose command can be run.
    """
    choose_cmd_expiry_seconds = fields.Int(dump_default=3600, required=True)


class ConfigSchema(BaseConfig):
    """
    Top level config schema.

    This section of config is for "core" variables, and also contains
    every other aforementioned schema.

    Attributes
    ----------
    name : str
        The name of the bot.
    timezone : str
        The timezone the bot runs in.
    root : str
        A POSIX path indicating the location of the bot's files.
    temp : str
        A POSIX path to a temp folder which the bot can use for processing.
        It is usually a good idea to set this to a location in /dev/shm, as 
        this allows this location to be entirely in RAM, which is much faster
        than a filesystem location.
    logs : str
        A POSIX path to a location where logs will be stored.
    owner_id : int
        The Discord ID of the user who owns the bot.
    token : str
        The Discord API token of the bot.
    fqdn : str
        The Fully-Qualified Domain Name that the bot runs under. This is used
        to resolve locations in the bot's web server.
    logging : LoggingConfigSchema
        The logging config schema. Don't touch.
    mvc : ORMConfigSchema
        The ORM config schema. Don't touch.
    vars : VarsConfigSchema
        The vars config schema. Don't touch.
    """
    name = fields.Str(dump_default="Hakase", required=True)
    timezone = Timezone(dump_default="UTC", required=True)
    root = ExistingPath(dump_default=os.getcwd(), required=True)
    temp = ExistingPath(dump_default="/dev/shm/hakase", create=True, required=True)
    logs = ExistingPath(dump_default=os.path.join(os.getcwd(), "logs/"), create=True, required=True)
    owner_id = DiscordUID(dump_default=100000000000000000, required=True)
    token = fields.Str(dump_default="", required=True)
    fqdn = fields.Str(dump_default="somesite.com", required=True)
    logging = fields.Nested(LoggingConfigSchema, dump_default=LoggingConfigSchema().dump({}))
    mvc = fields.Nested(ORMConfigSchema, dump_default=ORMConfigSchema().dump({}))
    vars = fields.Nested(VarsConfigSchema, dump_default=VarsConfigSchema().dump({}))

    @post_load
    def make(self, data, **kwargs):
        return Config.from_dict(data)


class Config(SimpleNamespace):
    """
    The config class which defines the config object.

    The object instantiated by this class is accessed around the codebase,
    allowing the variables defined in config to be accessed wherever needed.

    Attributes
    ----------
    version : SimpleNamespace
        The version of the config. Used later to establish the bot's version. 
    daemon : boolean
        Whether or not the bot should run as a daemon. This is overwritten by
        sys.argv later.
    """
    def __init__(self, **entries):
        self.version: SimpleNamespace = SimpleNamespace(**{'number': __VERSION__, 'tag': __TAG__})
        # To be overriden by sys.argv.
        self.daemon: bool = False
        super().__init__(**entries)
    
    @property
    def root_dir(self) -> str:
        """Resolves to the bot's root directory."""
        return Path(__file__).resolve().parent.parent.parent.parent
    
    @property
    def log_dir(self) -> str:
        return self.logs
    
    @property
    def asset_dir(self) -> str:
        """Location where assets are stored."""
        return os.path.join(self.root, "assets/")
    
    @property
    def bin_dir(self) -> str:
        """Location of binary utilities."""
        return os.path.join(self.root, "bin/")

    @property
    def outfacing_url(self) -> str:
        """
        Outfacing URL defined as the first address in allowed_hosts.

        This is kind of a hack, but it works. Allowed hosts will have one of
        the URLs set to the public facing URL, so it's pretty easy to just
        mandate that it must be the first one.
        """
        return self.mvc.allowed_hosts[0]
    
    @classmethod
    def from_dict(cls, d):
        for key, value in d.items():
            if isinstance(value, dict):
                d[key] = cls.from_dict(value)
            elif isinstance(value, list):
                d[key] = cls.from_list(value)
        return cls(**d)
    
    @classmethod
    def from_list(cls, config_list):
        for i, value in enumerate(config_list):
            if isinstance(value, list):
                config_list[i] = cls.from_list(value)
            elif isinstance(value, dict):
                config_list[i] = cls.from_dict(value)
        return config_list
    
    @classmethod
    async def aload(self):
        """
        Asynchronous loading of config.

        Most of the time, this isn't necessary, and load() is used instead.
        """
        try:
            async with aiofile.async_open('conf.toml', mode='r') as config_file:
                contents = await config_file.read()
                return ConfigSchema().load(toml.loads(contents))
        except FileNotFoundError:
            config_dict = ConfigSchema().dump({})
            async with aiofile.async_open('conf.toml', mode='w') as config_file:
                await config_file.write(toml.dump(config_dict, config_file))
            return ConfigSchema().load(config_dict)
    
    @classmethod
    def load(self, orm=False):
        """
        Load the config.

        Classmethod loads the config from the toml file by
        turning it into a Python dict and then passing it to
        ConfigSchema.load(). In the event that no file is found,
        one is created.

        The ORM may also optionally be configured, which is usually
        necessary if the file using the config is going to access the
        database.

        Parameters
        ----------
        orm : boolean
            Whether or not the should also be configured.
        """
        try:
            with open("conf.toml", "r") as config_file:
                conf = ConfigSchema().load(toml.load(config_file))
        except FileNotFoundError:
            config_dict = ConfigSchema().dump({})
            with open("conf.toml", "w") as config_file:
                toml.dump(config_dict, config_file)
            conf = ConfigSchema().load(config_dict)
        
        if orm is True:
            from hakase.mvc.core.settings import configure
            configure()
        return conf
