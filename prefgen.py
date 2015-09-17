#!/bin/env python
"""Generate preference screens from AsciiDoc input files"""
#
# Copyright (C) 2015 Jon Griffiths (jon_p_griffiths@yahoo.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2.0 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import os
import sys
import string
from argparse import ArgumentParser, FileType

JAVA_KEYWORDS = [ 'abstract', 'assert', 'boolean', 'break', 'byte',
    'case', 'catch', 'char', 'class', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'export', 'extends', 'final', 'finally',
    'float', 'for', 'goto', 'if', 'implements', 'import', 'instanceof',
    'int', 'interface', 'long', 'native', 'new', 'package', 'private',
    'protected', 'public', 'return', 'short', 'static', 'strictfp',
    'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
    'transient', 'try', 'void', 'volatile', 'while' ]

JAVA_KEYWORDS_DICT = {k:'' for k in JAVA_KEYWORDS}


class Parsed:
    def __init__(self, root, strings, linear, keys):
        self.root, self.strings, self.linear, self.keys = root, strings, linear, keys

class Item():
    ATTRS = ['level', 'title', 'key', 'keyName', 'defaultValue', 'type',
             'summary', 'summaryOn', 'summaryOff', 'help', 'dialogLayout',
             'enumValues', 'enabled', 'dependency']
    LEVEL_TOP, LEVEL_SCREEN, LEVEL_CATEGORY, LEVEL_ITEM = 1, 2, 3, 4
    MODE_SEARCHING, MODE_TITLE, MODE_SUMMARY, MODE_HELP = 0, 1, 2, 3
    TYPES = ['', 'PreferenceScreen', 'PreferenceCategory', None]
    BOOLEANS = [ '(Y/N)', '(T/F)', '(ON/OFF)' ]

    def __init__(self, line):
        for attr in self.ATTRS:
            self.__dict__[attr] = ''

        level, title = line.split(' ', 1)
        self.level = len(level)
        self.listItems = []

        self.type = self.TYPES[self.level - 1]
        if self.type is None:
            # FIXME: handle other types
            self.type = 'EditTextPreference'
            for boolean in self.BOOLEANS:
                if title.upper().endswith(boolean):
                    self.type = 'CheckBoxPreference'
                    self.defaultValue = 'false'
                    title = title[0:-len(boolean)].strip()
                    break

        self.title = title
        self.items = []

    def addText(self, mode, line):
        def append(start, end):
            return start + ' ' + end if len(start) > 0 else end

        if mode == self.MODE_TITLE:
            self.title = append(self.title, line)
        elif mode == self.MODE_SUMMARY:
            self.summary = append(self.summary, line)
        elif mode == self.MODE_HELP:
            self.help = append(self.help, line)

    def xmlStringRef(self, s):
        return '@string/' + args.parsed.strings[s]

    def javaStringRef(self, args, s):
        prefix = '' if args.package_name is None else args.package_name + '.'
        return prefix + 'R.string.' + args.parsed.strings[s]

    def pre(self, args, indentStr):

        of = args.layout_file
        if self.type == '':
            of.write('<?xml version="1.0" encoding="utf-8"?>\n')
            of.write('<!-- Generated by prefgen.py - Do not edit by hand! -->\n')
        elif self.type == 'PreferenceScreen':
            of.write('%s<PreferenceScreen\n' % indentStr)
            of.write('%s    xmlns:android="http://schemas.android.com/apk/res/android" >\n' % indentStr)
        elif self.type == 'PreferenceCategory':
            of.write('%s<PreferenceCategory\n' % indentStr)
            of.write('%s    android:title="%s" >\n\n' % (indentStr, self.xmlStringRef(self.title)))
        else:
            of.write('%s<%s\n' % (indentStr, self.type))
            of.write('%s    android:key="%s"\n' % (indentStr, self.key))
            of.write('%s    android:title="%s"' % (indentStr, self.xmlStringRef(self.title)))
            for sType in ['summary', 'summaryOn', 'summaryOff']:
                val = self.__dict__[sType]
                if val != '':
                    of.write('\n%s    android:%s="%s"' % (indentStr, sType, self.xmlStringRef(val)))
            for k in ['defaultValue', 'dialogLayout', 'enabled', 'dependency']:
                if self.__dict__[k] != '':
                    of.write('\n%s    android:%s="%s"' % (indentStr, k, self.__dict__[k]))
            if len(self.listItems):
                of.write('\n%s    android:entries="@array/%s_array"' % (indentStr, self.key))
                of.write('\n%s    android:entryValues="@array/%s_array_values"' % (indentStr, self.key))
            of.write(' />\n\n')


    def post(self, args, indentStr):
        of = args.layout_file
        if self.type in ['PreferenceScreen', 'PreferenceCategory']:
            of.write('%s</%s>\n' % (indentStr, self.type))
            if self.type != 'PreferenceScreen':
                of.write('\n')
        pass

    def outputLayoutXml(self, args, indent):
        indentStr = ' ' * ((indent -1) * 4 if indent > 0 else 0)
        self.pre(args, indentStr)
        for item in self.items:
            item.outputLayoutXml(args, indent + 1)
        self.post(args, indentStr)

def makeKey(s):
    return s.lower().translate(None, string.punctuation).replace(' ', '_')

def makeKeyName(k):
    return 'PREF_' + k.replace('.','_').upper()

def makeStringRef(s):
    s = s.lower().translate(None, string.punctuation)
    s = s.split(' ')
    if len(s) > 5:
        s = s[0:5]
    s = '_'.join(s)
    if s in JAVA_KEYWORDS_DICT:
        return '_' + s + '_'
    return s

# See https://stackoverflow.com/questions/4303492
def makeVar(s, initialLower=True):
    def camelcase(initialLower):
        if initialLower:
            yield str.lower
        while True:
            yield str.capitalize

    c = camelcase(initialLower)
    return ''.join(c.next()(x) if x else '_' for x in s.split('_'))

def stripDot(s):
    if s.endswith('.'):
        return s[0:-1]
    return s

def parseAsciiDoc(args):
    """Parse an AsciiDoc representation of a settings dialog"""
    linear = []
    mode = Item.MODE_SEARCHING
    inComment = False
    keys = {}

    for line in args.input_file.readlines():

        line = line.strip()
        if len(line) == 0:
            if mode > Item.MODE_SEARCHING and mode <= Item.MODE_SUMMARY:
                mode += 1 # Blank line separates sections
            continue # blank line
        elif line.startswith('//'):
            inComment = not inComment
        elif line[0] == '*':
            # A list item
            linear[-1].listItems.append(stripDot(line[1:].strip()))
            linear[-1].type = 'ListPreference'
        elif line[0] == ':':
            # Key/Type name or an AsciiDoc attribute to ignore
            if mode != Item.MODE_SEARCHING:
                if inComment:
                    if line.startswith(':key: '):
                        k = line[len(':key: '):]
                        keys[k] = makeKeyName(k)
                else:
                    for attr in Item.ATTRS:
                        if line.startswith(':' + attr + ':'):
                            linear[-1].__dict__[attr] = line.split(':')[2].strip()
                            break
        elif line[0] in ['=','#']:
            # Section header
            linear.append(Item(line))
            mode = Item.MODE_TITLE
        else:
            linear[-1].addText(mode, line)

    # Nest the parsed representation and fill in any missing members
    root = None
    stack = []
    strings = {}

    for item in linear:
        if item.level != Item.LEVEL_ITEM:
            item.key, item.keyName = '', ''
        else:
            if item.key == '':
                item.key = makeKey(item.title)
            if item.keyName == '':
                item.keyName = makeKeyName(item.key)
            keys[item.key] = item.keyName

        # Android style removes final period from summary
        item.summary = stripDot(item.summary)

        # Remove unused title/summary to avoid generating unused resources
        if item.type in ['', 'PreferenceScreen', 'PreferenceCategory']:
            item.summary = ''
            if item.type != 'PreferenceCategory':
                item.title = ''
        elif item.type == 'CheckBoxPreference':
            if item.summary.find('/') != -1:
                item.summaryOn, item.summaryOff = item.summary.split('/')
                item.summary = ''

        for s in [item.title, item.summary, item.summaryOn, item.summaryOff]:
            if s != '':
                strings[s] = makeStringRef(s)

        if len(item.listItems) > 0:
            item.defaultValue = '0'
            n = 0
            for li in item.listItems:
                if li.endswith('(default)'):
                    item.defaultValue = str(n)
                    item.listItems[n] = item.listItems[n][0:-len('(default)')].strip()
                    break

        if item.enumValues != '':
            item.enumValues = [x.strip() for x in item.enumValues.split(',')]
            item.enumName = makeVar(item.title.replace(' ', '_'), False) + 'Enum'

        if root is None:
            root = item
            stack.append(item)
            continue

        while item.level <= stack[-1].level:
            stack.pop()

        if item.level >= stack[-1].level:
            stack[-1].items.append(item)
            if item.level > stack[-1].level and item.level < item.LEVEL_ITEM:
                stack.append(item)

    return Parsed(root, strings, linear, keys)

def escapeXml(s):
    # Add escapes for a string to be placed in resources
    # (saxutils doesn't work if our string already contains entity refs)
    for k, v in (('"', '\\"'), (' & ', ' &amp; '), ("'", "\\'"), ('<', '&lt;')):
        s = s.replace(k, v)
    return s

def outputResourceStringsXml(args):
    of = args.resource_file
    of.write('<?xml version="1.0" encoding="utf-8"?>\n')
    of.write('<!-- Generated by prefgen.py - Do not edit by hand! -->\n')
    of.write('<resources>\n')
    strings = []
    for k,v in args.parsed.strings.iteritems():
        strings.append('    <string name="%s">%s</string>\n' %(v, escapeXml(k)))
    for s in sorted(strings):
        of.write(s)
    for item in args.parsed.linear:
        if len(item.listItems):
            of.write('    <string-array name="%s_array">\n' % item.key)
            for li in item.listItems:
                of.write('        <item>%s</item>\n' % escapeXml(li))
            of.write('    </string-array>\n')
            # Can't use integer-array here due to an Android bug from 2009 :-(
            of.write('    <string-array name="%s_array_values" translatable="false">\n' % item.key)
            for i in range(0, len(item.listItems)):
                of.write('        <item>%d</item>\n' % i)
            of.write('    </string-array>\n')
    of.write('</resources>\n')


def outputSettingsClass(args):
    of = args.settings_file
    items = [i for i in args.parsed.linear if i.level == i.LEVEL_ITEM]
    className = os.path.split(os.path.splitext(of.name)[0])[1]
    of.write('// Generated by prefgen.py - Do not edit by hand!\n\n')
    if args.package_name is not None:
        of.write('package %s;\n\n' % args.package_name)
    of.write('import android.content.SharedPreferences;\n\n')
    of.write('public class %s {\n' % className)
    # Write key constants
    for key, keyName in sorted(args.parsed.keys.items()):
        of.write('    public static final String %s = "%s";\n' % (keyName, key))

    # Enums
    for i in items:
        if len(i.enumValues) == 0:
            continue
        of.write('    public enum %s {\n' % i.enumName)
        for ev in i.enumValues:
            of.write('        %s,\n' % ev)
        of.write('    }\n')

    # Raw accessors
    of.write('    private final SharedPreferences mPreferences;\n\n')
    of.write('    public %s(SharedPreferences preferences) {\n' % className)
    of.write('        mPreferences = preferences;\n')
    of.write('    }\n\n')
    of.write('    public SharedPreferences getPreferences() {\n')
    of.write('        return mPreferences;\n')
    of.write('    }\n\n')

    accessors = [('int', 'Int', ',', '0'), ('boolean', 'Boolean', '', 'false'),
                 ('String', 'String', '', '""'), ('int', 'EnumInt', '', '')]
    for j, m, name, d in accessors:
        of.write('    public %s get%s(final String key, final %s def) {\n' % (j, m, j))
        if m == 'EnumInt':
            of.write('        return Integer.parseInt(getString(key, String.valueOf(def)));\n')
        else:
            of.write('        return mPreferences.get%s(key, def);\n' % m)
        of.write('    }\n\n')
        if d != '':
            of.write('    public %s get%s(final String key) {\n' % (j, m))
            of.write('        return get%s(key, %s);\n' % (m, d))
            of.write('    }\n\n')
        of.write('    public void put%s(final String key, final %s value) {\n' % (m, j))
        if m == 'EnumInt':
            of.write('        putString(key, String.valueOf(value));\n')
        else:
            of.write('        mPreferences.edit().put%s(key, value).commit();\n' % m)
        of.write('    }\n\n')

    listType = lambda i: (i.enumName, 'EnumInt') if len(i.enumValues) > 0 else ('String', 'String')
    TYPEMAP = { 'EditTextPreference': lambda i: ('String',  'String'),
                'CheckBoxPreference': lambda i: ('boolean', 'Boolean'),
                'ListPreference':     listType}
    for i in items:
        if i.type not in TYPEMAP:
            continue
        isEnum = len(i.enumValues) > 0
        javaType, methodType = TYPEMAP[i.type](i)
        methodKey = i.key.replace('.','_')

        of.write('    public %s %s() {\n' % (javaType, makeVar('get_' + methodKey)))
        wrap = lambda s: s if not isEnum else i.enumName + '.values()[' + s + ']'
        call = wrap('get%s(%s, %s)' % (methodType, i.keyName, i.defaultValue))
        of.write('        return %s;\n' % call)
        of.write('    }\n\n')
        of.write('    public void %s(%s value) {\n' % (makeVar('set_' + methodKey), javaType))
        convertMethod = '.ordinal()' if isEnum else ''
        of.write('        put%s(%s, value%s);\n' % (methodType, i.keyName, convertMethod))
        of.write('    }\n\n')
    of.write('}\n')


def outputActivityClass(args):
    of = args.activity_file
    className = os.path.split(os.path.splitext(of.name)[0])[1]
    listItems = [i for i in args.parsed.linear if i.type == 'ListPreference']

    of.write('// Generated by prefgen.py - Do not edit by hand!\n\n')
    if args.activity_package_name is not None:
        of.write('package %s;\n\n' % args.activity_package_name)

    # FIXME: If settings_file isn't generated, output needed constants
    #        into the activity here instead of including here
    settingsClass = os.path.split(os.path.splitext(args.settings_file.name)[0])[1]
    prefix = '' if args.package_name is None else args.package_name + '.'
    of.write('import %s%s;\n\n' % (prefix, settingsClass))
    of.write('import android.content.SharedPreferences;\n\n')
    of.write('public class %s extends android.preference.PreferenceActivity\n' % className)
    of.write('        implements SharedPreferences.OnSharedPreferenceChangeListener {\n\n')
    of.write('    public %s() {\n        super();\n    }\n\n' % className)
    of.write('    @Override\n')
    of.write('    protected void onCreate(android.os.Bundle savedInstanceState) {\n')
    of.write('        super.onCreate(savedInstanceState);\n')
    # FIXME: Should really be able to specify this package on the command line
    resPackage = '' if args.package_name is None else args.package_name + '.'
    of.write('        addPreferencesFromResource(%sR.xml.settings);\n' % resPackage)
    of.write('    }\n\n')
    of.write('    @Override\n')
    of.write('    public void onSharedPreferenceChanged(SharedPreferences p, String key) {\n')
    of.write('        updatePreferenceText(key);\n')
    of.write('    }\n\n')
    of.write('    protected SharedPreferences getPreferences() {\n')
    of.write('        return getPreferenceScreen().getSharedPreferences();\n')
    of.write('    }\n\n')
    of.write('    protected String createPreferenceText(int id, CharSequence choice) {\n')
    of.write('        return getResources().getString(id) + " (" + choice + ")";\n')
    of.write('    }\n\n')

    prefix = '' if settingsClass is None else settingsClass + '.'

    def mkSwitch(indent, items):
        write = lambda line: of.write(indent + line)
        write('switch (key) {\n')
        for i in items:
            write('    case %s%s:\n' % (prefix, i.keyName))
            write('        resId = %s;\n' % i.javaStringRef(args, i.summary))
            write('        break;\n')
        write('    default:\n')
        write('        return;\n')
        write('}\n')

    of.write('    protected void updatePreferenceText(String key) {\n')
    of.write('        android.preference.Preference p = findPreference(key);\n')
    of.write('        int resId;\n')
    of.write('        if (p instanceof android.preference.ListPreference) {\n')
    mkSwitch('            ', listItems);
    of.write('            CharSequence choice = ((android.preference.ListPreference) p).getEntry();\n')
    of.write('            p.setSummary(createPreferenceText(resId, choice));\n')
    of.write('        }\n')
    of.write('    }\n\n')

    def getPauseResume(p_r, method, updates):
        return """    @Override\n    protected void on%s() {\n        super.on%s();
        getPreferences().%sOnSharedPreferenceChangeListener(this);\n%s    }\n""" % (p_r, p_r, method, updates)
    updates = ''
    for i in listItems:
        updates += '        updatePreferenceText(%s.%s);\n' % (settingsClass, i.keyName)

    of.write(getPauseResume('Resume', 'register', updates))
    of.write(getPauseResume('Pause', 'unregister', ''))
    of.write('}\n')


def parseArgs():
    parser = ArgumentParser(version='1.0', fromfile_prefix_chars='@')
    parser.add_argument('input_file', type=FileType('r'))
    for f in ['layout', 'resource', 'settings', 'activity']:
        parser.add_argument('--%s_file' % f)
    parser.add_argument('--package_name')
    args = parser.parse_args()
    args.activity_package_name = args.package_name
    if args.package_name is not None:
        if ',' in args.package_name:
            args.package_name, args.activity_package_name = args.package_name.split(',')
    for f in ['layout', 'resource', 'settings', 'activity']:
        name = '%s_file' % f
        if getattr(args, name) is not None:
            setattr(args, name, open(getattr(args, name), 'w'))
    return args


if __name__ == '__main__':

    args = parseArgs()

    args.parsed = parseAsciiDoc(args)

    if args.layout_file is not None:
        args.parsed.root.outputLayoutXml(args, 0)
    if args.resource_file is not None:
        outputResourceStringsXml(args)
    if args.settings_file is not None:
        outputSettingsClass(args)
    if args.activity_file is not None:
        outputActivityClass(args)
