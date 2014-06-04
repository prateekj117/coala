"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from collections import OrderedDict
from codeclib.fillib.util.setting import Setting

import os
import argparse
import shutil
import re


# noinspection PyUnreachableCode
class Settings(OrderedDict):
    @staticmethod
    def __make_value(original):
        working = original.strip().lower()

        # make it an int if possible:
        try:
            working = [int(working)]
            return working
        except ValueError:
            pass

        list = working.replace(';', ',').split(',')
        if len(list) > 1:
            new_list = []
            for elem in list:
                new_list.append(Settings.__make_value(elem))
            return new_list

        # make it bool if possible:
        try:
            if working in ['y', 'yes', 'yeah', 'always', 'sure', 'definitely', 'yup', 'true']:
                return [True]
            elif working in ['n', 'no', 'nope', 'never', 'nah', 'false']:
                return [False]
            elif working in ['', 'None', 'none']:
                return None
        except AttributeError:
            pass

        return [original.strip()]

    def __init__(self, origin_file):
        dict.__init__(self)
        self.origin_file = origin_file
        self.__import_file(origin_file)
        pass

    def __import_file(self, path, import_history=[]):
        # prevent loops
        if path in import_history:
            # TODO log warning about circular dependency
            return
        import_history.append(path)

        if not os.path.isfile(path):
            # TODO log warning notafile
            return

        comments = []
        with open(path, 'r') as lines:
            for line in lines:
                comments = self.__parse_line(line, comments, import_history)

        if  comments != []:
            # add empty comment-only object
            self['comment'] = Setting('', '', import_history, comments)

    def save_to_file(self, path):
        for setting in self:
            # TODO
            # write setting only if its import_history is [origin_file] AND
            # a) it is non-default
            # b) it is default and overwrites a non-default setting with len(import_history) > 1 which does not
            #    get overwritten by a default setting with len(import_history) > 1
            new_lines = setting.generate_lines()
            # TODO add these lines to the new config

    def ensure_settings_available(self, keys):
        for key in keys:
            # since we save Setting objects, get() does not return None if it's set to None!
            if self.get(key, None):
                # TODO ask and store; parse also trailing comments after the value, import_history is [origin_file]
                #      every time
                pass


    def __parse_line(self, line, comments, import_history=[]):
        line = line.strip()
        if line == '':
            comments.append('')
            return comments

        # handle comments - TODO allow \# as non-comment
        line = line.split('#')[0].strip()
        trailing_comment = line[line.find('#')].strip()
        # TODO allow \=!
        parts = line.split('=')
        if (len(parts) == 1):
            comments.append(trailing_comment)
            return comments

        if (len(parts) != 2):
            # TODO log a warning
            return comments

        key = parts[0].strip()
        val = Setting(key,
                      Settings.__make_value(parts[1]),
                      import_history,
                      comments,
                      trailing_comment,
                      self.get(key.lower, None)
        )
        self[key.lower()] = val

        self.__execute_command(val)

        return []

    def __import_command(self, command):
        for config_path in command.value:
            self.__import_file(config_path, command.import_history)

    def __execute_command(self, command):
        return {
            # Import a number of other configuration files
            'configfile': self.__import_command(command)
        }[command.key.lower()]




# OLD STUFF



    @staticmethod
    def default_options():
        # default settings
        defaultValues = {
            'TargetDirectories': [os.getcwd()],
            'IgnoredDirectories': None,
            'FlatDirectories': None,
            'TargetFileTypes': None,
            'IgnoredFileTypes': ['.gitignore'],

            'Filters': None,
            'IgnoredFilters': None,
            'RegexFilters': None,

            'FileOkColor': ['bright red'],
            'FileBadColor': ['bright green'],
            'FilterColor': ['grey'],
            'ErrorResultColor': ['red'],
            'WarningResultColor': ['yellow'],
            'InfoResultColor': ['normal'],
            'DebugResultColor': ['cyan'],

            'LogType': ['CONSOLE'],
            'LogOutput': None,
            'Verbosity': ['INFO'],

            'ConfigFile': ['.codecfile'],
            'Save': None,
            'JobCount': None
        }
        return defaultValues


    @staticmethod
    def parse_args(custom_arg_list = None):
        """
        Parses command line arguments and configures help output.

        :param custom_arg_list: parse_args will parse this list instead of command line arguments, if specified
        :returns: parsed arguments in dictionary structure
        """
        # arg_parser reads given arguments and presents help on wrong input
        arg_parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=__doc__)

        # -d sets parameter "TargetDirectories" => List of paths to files and/or directories to be (recursively) checked
        arg_parser.add_argument('-d', '--dirs', nargs='+', metavar='DIR', dest='TargetDirectories',
                                help='List of paths to files and/or directories to be (recursively) checked')
        # -id sets parameter "IgnoredDirectories" => List of paths to files and/or directories to be ignored
        arg_parser.add_argument('-id', '--ignored-dirs', nargs='+', metavar='DIR', dest='IgnoredDirectories',
                                help='List of paths to files and/or directories to be ignored')
        # -fd sets parameter "FlatDirectories" => List of paths to directories to be checked excluding sub-directories
        arg_parser.add_argument('-fd', '--flat-dirs', nargs='+', metavar='DIR', dest='FlatDirectories',
                                help='List of paths to directories to be checked excluding sub-directories')
        # -t sets parameter "TargetFileTypes" => List of file endings of files to be checked
        arg_parser.add_argument('-t', '--types', nargs='+', metavar='TYPE', dest='TargetFileTypes',
                                help='List of file endings of files to be checked')
        # -it sets parameter "IgnoredFileTypes" => List of file endings of files to be ignored
        arg_parser.add_argument('-it', '--ignored-types', nargs='+', metavar='TYPE', dest='IgnoredFileTypes',
                                help='List of file endings of files to be ignored')
        # -f sets parameter "Filters" => Names of filters that should be used
        arg_parser.add_argument('-f', '--filters', nargs='+', metavar='FILE', dest='Filters',
                                help='Names of filters that should be used')
        # -if sets parameter "IgnoredFilters" => Names of filters that should be ignored
        arg_parser.add_argument('-if', '--ignored-filters', nargs='+', metavar='FILE', dest='IgnoredFilters',
                                help='Names of filters that should be ignored')
        # -rf sets parameter "RegexFilters" => List of regular expressions for matching filters to be used
        arg_parser.add_argument('-rf', '--regex-filters', nargs='+', metavar='REGEX', dest='RegexFilters',
                                help='List of regular expressions for matching filters to be used')
        # -l sets parameter "LogType" => Enum (CONSOLE/TXT/HTML) to choose type of logging
        arg_parser.add_argument('-l', '--log', nargs=1, choices=['CONSOLE', 'TXT', 'HTML'], metavar='LEVEL',
                                dest='LogType', help='Enum (CONSOLE/TXT/HTML) to choose type of logging')
        # -o sets parameter "LogOutput" => File path to where logging output should be saved
        arg_parser.add_argument('-o', '--output', nargs=1, metavar='FILE', dest='LogOutput',
                                help='File path to where logging output should be saved')
        # -v sets parameter "Verbosity" => Enum (ERR/WARN/INFO/DEBUG) to choose level of verbosity
        arg_parser.add_argument('-v', '--verbose', nargs=1, choices=['ERR', 'WARN', 'INFO', 'DEBUG'], metavar='LEVEL',
                                dest='Verbosity', help='Enum (ERR/WARN/INFO/DEBUG) to choose level of verbosity')
        # -c sets parameter "ConfigFile" => File path of configuration file to be used
        arg_parser.add_argument('-c', '--config', nargs=1, metavar='FILE', dest='ConfigFile',
                                help='File path of configuration file to be used')
        # -s sets parameter "Save" => Filename of file to be saved to, defaults to config file
        arg_parser.add_argument('-s', '--save', nargs='?', const=True, metavar='FILE', dest='Save',
                                help='Filename of file to be saved to, defaults to config file')
        # -j sets parameter "JobCount" => Number of processes to be allowed to run at once
        arg_parser.add_argument('-j', '--jobs', nargs=1, type=int, metavar='INT', dest='JobCount',
                                help='Number of processes to be allowed to run at once')

        # arg_vars stores parsed arguments in form of a dictionary.
        # it reads custom_arg_string instead of sys.args if custom_arg_string is given.
        if custom_arg_list:
            arg_vars = vars(arg_parser.parse_args(custom_arg_list))
        else:
            arg_vars = vars(arg_parser.parse_args())

        #make -s --save store arguments in a list or None as all parameters do:
        if arg_vars['Save']: arg_vars['Save'] = [arg_vars['Save']]

        return arg_vars

    def __init__(self, custom_arg_list=None):
        # derived from ordered Dict for cleaner configuration files
        # noinspection PyTypeChecker
        dict.__init__(self)

        # default Options dict
        default_conf = Settings.default_options()

        # command line arguments dict
        cli_conf = Settings.parse_args(custom_arg_list)

        # configuration file options dict:
        if cli_conf['ConfigFile']:
            config_file_conf = self.read_conf(cli_conf['ConfigFile'][0])
        else:
            config_file_conf = self.read_conf(default_conf['ConfigFile'][0])

        # generally importance: cli_conf > config_file_conf > default_conf
        # default_conf has all keys and they are needed if not overwritten later
        for setting_name, setting_value in default_conf.items():
            self[setting_name] = setting_value

        # config_file_conf is supposed to be minimal and all values can be taken
        for setting_name, setting_value in config_file_conf.items():
            self[setting_name] = setting_value

        # cli_conf contains all settings, but only the ones that are not None should be taken
        for setting_name, setting_value in cli_conf.items():
            if setting_value:
                self[setting_name] = setting_value

        # save settings if arguments say so
        if self['Save']:
            self.save_conf()


    def read_conf(self, codecfile_path, history_list=None):

        # open file if possible
        with open(codecfile_path,'r') as codecfile:

            # check if config refers to other config file
            codecfile.seek(0)
            for line in codecfile:
                [key, value] = self.parse_line(line)
                if key == "":
                    continue

                if key == 'configfile':
                    #append codecfile_path to history_list so it can't be called again:
                    history_list.append(value)

                    #populate config_dict with data from inner config:
                    config_dict = self.read_conf(value, history_list)
                    continue

                config_dict[key] = value

            # all lines have been read. config_dict can be returned
            return config_dict

        # configuration file could not be read, probably because of missing permission or wrong file format
        #TODO: log warning!
        return {}  # this is indeed reachable...

    def save_conf(self):

        # sane default, mind that in some cases the config will be written to another directory
        save_location = self['ConfigFile'][0]

        # In this case, the config file will be saved to a file different from the config file
        # therefore the config file will be copied to that location if it exists
        # the following routine is then always the same
        if not (self['Save'] == [True] or self['Save'] is None or self['Save'][0] == self['ConfigFile'][0]):
            try:
                shutil.copyfile(self['ConfigFile'][0],self['Save'][0]) # remember that self[*] contains lists
                save_location = self['Save'][0]
            except IOError:
                # Possible errors:
                # - there is no config file at self['ConfigFile']
                # - It is not permitted to read self['ConfigFile']
                # - It is not permitted to write self['save']
                # If self['save'] exists, it will be overwritten without raising this error!
                #TODO: find out what happened and log a warning?
                pass

        # the config should be minimal, none of these defaults should be written:
        default_settings = Settings.default_options()

        # the config should be minimal, no setting should be written that is already defined through it
        current_conf_settings = self.read_conf(save_location)

        # list of settings that should be written to the config
        # keep them lowercase to find matches!
        settings_to_write = []

        #list of settings that should be deleted from the config (before new values are written)
        # keep them lowercase to find matches!
        settings_to_delete = []

        # make sure all settings get saved if not for one of the above reasons
        for setting, value in self.items():

            if setting in default_settings and self[setting] == default_settings[setting]:
                # setting is a default and should not be written
                # it should even be deleted from the config if it was spedified there
                settings_to_delete.append(setting.lower())

            elif setting in current_conf_settings and self[setting] == current_conf_settings[setting]:
                # setting is already specified as is
                pass
            else:
                if not setting == 'ConfigFile':
                    # configFile should never be overwritten because:
                    # in config files this is only useful to chain configs
                    # at runtime this is not useful
                    # current chains should be kept, though.
                    settings_to_write.append(setting.lower())
                    settings_to_delete.append(setting.lower()) # should be deleted and re-added to prevent contradictions

        # delete config settings that are not current settings:
        for setting, value in current_conf_settings.items():
            if setting not in self:
                settings_to_delete.append(setting.lower())

        # make new config
        new_config = ""
        try:
            with open(save_location,'r') as new_config_file:
                new_config = new_config_file.readlines()

        except IOError:
            pass

        new_config = list(new_config) # it was immutable an immutable tuple, it's a list now

        with open(save_location,'w') as new_config_file:

            # this list saves which settings could actually be removed from the direct configuration file
            removed_settings = []
            # remove lines to be removed
            for line in new_config:
                if line.split('=')[0].lower().strip() in settings_to_delete:
                    new_config.remove(line)
                    removed_settings.append(line.split('=')[0].lower().strip())

            # settings that should be removed but were not, might be specified in a nested config
            # they should be overwritten in this one - even if the settings is considered default
            for setting in settings_to_delete:
                if setting not in removed_settings:
                    if setting not in settings_to_write:
                        settings_to_write.append(setting)

            # since self[*] expects settings to be capitalized appropriately, this ugly thing is needed:
            for i in range(len(settings_to_write)):
                settings_to_write[i] = self.__capitalize_setting(settings_to_write[i])

            # add lines to be written
            for setting in settings_to_write:

                # values segregated by comma without quotation marks and brackets
                value_string = ""
                if self[setting]:
                    for value in self[setting]:
                        if value_string: value_string += ','
                        value_string += str(value)
                else:
                    value_string = str(self[setting])
                # add lines in the needed format
                # '\n' is actually cross platform because file is opened in text mode
                new_config.append("{} = {}\n".format(setting, value_string))

            # let's finally write the config file:
            for line in new_config:
                new_config_file.write(line)

                #TODO: log successful save, catch failures?

    def fill_settings(self, key_list):

        # remove duplicates
        key_list = list(set(key_list))

        #only do this if there are keys in the list
        if key_list:

            # ask for and add settings, that are not present
            print("At least one filter needs settings that are not available!")
            print("Please enter the values for the following settings:")
            print("If you need several values for one settings, please separate then by commas")

            for key in key_list:
                # capitalize key to match self[*]
                cap_key = self.__capitalize_setting(key)
                if cap_key not in self.keys():
                    # this key is not available
                    value_line = input("{}: ".format(key))
                    value_list = value_line.split(',')
                    # Get values from strings
                    for i in range(len(value_list)):
                        value_list[i] = Settings.__make_value(value_list[i])

                    self[cap_key] = value_list

            # offer to save settings if saving is not set
            if not self['Save']:
                save_now = input("Do you want to save the settings now? (y/n)")
                if Settings.__make_value(save_now) == True:
                    self['Save'] = [True]

            if self['Save']:
                self.save_conf()


if __name__ == "__main__":
    settings=Settings()