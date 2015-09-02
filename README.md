# prefgen, A Preferences Generator

This script creates Android preference (settings) dialog files
from an AsciiDoc source file.

## Motivation

Creating a preference dialog by hand can be a lot of work. You have to:

1. Create the actual XML file containing the preferences/layout/key names.
2. Add string, string array and any other resources for translation.
3. Derive an action class to show the preferences.
4. Create an options accessor class or add calls to get/set preferences all
   over the app.
5. Create a listener to update summary text when options change
6. Try to support newer/older/different form factor devices by switching
   between `PreferenceScreen` and `Fragment`, launching with actions versus
   directly, etc, etc.

Even once all this is done, some preferences may be under-documented. A single
line description is often not enough to explain the consequences of a given
setting. So being able to describe these options in more details is desirable.

Finally it would be nice to add a new setting by only changing a single file.

## Implementation

The script +prefgen.py+ takes as input an AsciiDoc file documenting the
desired preferences and outputs the various source files needed to add that
dialog to an application. The source documentation can either be read as
a text file and/or converted to documentation for the settings
using http://www.methods.co.nz/asciidoc/[AsciiDoc]. In this way each setting
can include more detailed documentation.

## Status

Current functionality is fairly basic; Please see the +samples/+ directory
to see example input files. Patches/pull requests are welcome.

## License

GPL v2.1. Please see the file LICENSE for more details and/or see the source
at https://github.com/jgriffiths/prefgen.

### Usage

----
usage: prefgen.py [-h] [-v] [--layout_file LAYOUT_FILE]
                  [--resource_file RESOURCE_FILE]
                  [--settings_file SETTINGS_FILE]
                  [--activity_file ACTIVITY_FILE]
                  [--package_name PACKAGE_NAME]
                  input_file

positional arguments:
  input_file

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  --layout_file LAYOUT_FILE
  --resource_file RESOURCE_FILE
  --settings_file SETTINGS_FILE
  --activity_file ACTIVITY_FILE
  --package_name PACKAGE_NAME
----

## Config file

Rather than being placed on the command line, arguments can be given in
a config file which may be more convenient. in this case each argument
should be in the file in the form *--option_name=option_value*, with
one such option per line. The +input_file+ option is the exception, if
in the file it should simply be given on a line of its own.

To pass the config file use "@", e.g. +prefgen.py @file_name+.

## Arguments

+input_file+ Is the input AsciiDoc file to generate code from. The supported
formatting convention is described below. It is likely that Markdown files
will also process correctly although this isn't explicitly supported.

+resource_file+ Is the destination string XML resource file. It should
normally be placed in the +res/values/+ directory of your Android project
as it is translatable.

+layout_file+ Is the destination layout XML. It should normally be placed in
the +res/xml/+ directory of your Android project since it is not translatable.

+settings_file+ Is the destination settings Java source file. This is a Java
class which can read and write the settings value so you can access them in
your source code.

+activity_file+ Is the destination activity Java source file. This file
contains an
https://developer.android.com/reference/android/preference/PreferenceActivity.html[Activity]
which is used to show the preferences dialog.

## Format

The input file format is constrained to make parsing as simple as possible.

FIXME
