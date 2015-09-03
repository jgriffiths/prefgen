# prefgen, A Preferences Generator

Create Android preference (settings) dialogs from AsciiDoc files.

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
It would also be nice to be able to add new settings by only changing a
single file.

## Implementation

The script `prefgen.py` takes as input an AsciiDoc file documenting the
desired preferences and outputs the various source files needed to add that
preference dialog to an application. The source documentation can either be
read as a text file and/or converted to documentation for the settings
using [AsciiDoc](http://www.methods.co.nz/asciidoc/). In this way each setting
can include more detailed documentation.

## Status

Current functionality is fairly basic; Please see the [Examples](./examples/)
to see example input files.

Patches, pull requests, bug reports and feature requests are welcome.

## License

GPL v2. Please see the file [LICENSE](./LICENSE) for more details and/or see the
[source](https://github.com/jgriffiths/prefgen).

### Usage

```
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
```

## Config file

Rather than being placed on the command line, arguments can be given in
a config file which may be more convenient. in this case each argument
should be in the file in the form `--option_name=option_value`, with
one such option per line. The `input_file` option is the exception, if
in the file it should simply be given on a line of its own.

To pass the config file use "@", e.g. `prefgen.py @file_name`.

## Arguments

`input_file` Is the input AsciiDoc file to generate code from. The supported
formatting convention is described below. It is likely that Markdown files
will also process correctly although this isn't explicitly supported.

`resource_file` Is the destination string XML resource file. It should
normally be placed in the `res/values/` directory of your Android project
as it is translatable.

`layout_file` Is the destination layout XML. It should normally be placed in
the `res/xml/` directory of your Android project since it is not translatable.

`settings_file` Is the destination settings Java source file. This is a Java
class which can read and write the settings value so you can access them in
your source code. The name of the class is taken from the file name.

`activity_file` Is the destination activity Java source file. This file
contains an
[Activity](https://developer.android.com/reference/android/preference/PreferenceActivity.html)
which is used to show the preferences dialog. The name of the class is taken
from the file name.

`package_name` Is the name of a package to place the settings and activity
Java classes into, e.g. `com.example.myapp`. If you wish each class to be
in a different package then you may give the settings and action packages
repectively, separated by a comma,
e.g. `--package_name=com.example.myapp,com.example.myapp.ui`.

Note that currently the generated settings class must be in the same package
as the apps resources. This may change in a future version.

## Format

The input file format is constrained to make parsing as simple as possible.
The header levels of the document split the various preferences into
preference screens and categories. Each preference should then have a one
line summary at a minimum. All other documentation will be used in the
AsciiDoc output but unused by the code generation machinery.

Some features can be overridden using AsciiDoc attributes for finer control;
For example changing the preference key and using custom Dialog classes.

The [Example Settings File](./examples/formatting.asciidoc) documents the
features currently supported. Or, you may wish to start with a
[Minimal Example](./examples/minimal.asciidoc) for adding to your app.

## Integrating Into Your Project

### Resource Files
The generated string and layout resources should be placed within your apps
`res/` folder so that they are compiled into the application.

### Activity Class
The activity class should be placed with your java source tree in accordance
with the package name you gave it.

To show the settings dialog, you need to add an activity for it to you
`AndroidManifest.xml` file under `manifest/application`, as follows:

```XML
        <activity
            android:name="com.example.myapp.ui.SettingsActivity"
            android:label="@string/settings_activity_name" >
        </activity>
```

Then from any activity in your app, use the following code to show the
settings dialog:

```Java
import android.content.Intent;
import com.example.myapp.ui.SettingsActivity;

    // ...

    startActivity(new Intent(this, SettingsActivity.class));
```

In most cases you would do this when a menu choice is made.

### Settings Class
The settings class should be placed with your java source tree in accordance
with the package name you gave it.

Once integrated, this class can be used by your code to get and set
preferences values. There are specific methods for each preference, or you
can use the more general type-based methods (`getBoolean()`, `getString()` etc)
and pass in the preference keys you wish to use. See the generated java file
for more details.

The settings class must be constructed with a `SharedPreferences` instance.
In many cases it is best to store an instance of this class in your main
activity and provide an accessor for it, i.e.:

```Java
import com.example.myapp.MySettings;
import android.preference.PreferenceManager;

public class MyMainActivity // ...
{
    private MySettings mSettings;

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // ...
        mSettings = new MySettings(PreferenceManager.getDefaultSharedPreferences(this));
    }

    public MySettings getSettings() {
        return mSettings;
    }
}
````

