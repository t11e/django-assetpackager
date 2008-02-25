# CSSTidy - CSS Parser and Optimiser
#
# CSS Parser class
#
# This file is part of CSSTidy.
#
# CSSTidy is free software you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation either version 2 of the License, or
# (at your option) any later version.
#
# CSSTidy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CSSTidy if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# @license http://opensource.org/licenses/gpl-license.php GNU Public License
# @package csstidy
# @author Dj Gilcrease (digitalxero at gmail dot com) 2005-2006

from tidyprinter import CSSTidyPrint
from tidyoptimiser import CSSTidyOptimise
from tidydata import *
import re

class CSSTidy(object):
    #Saves the parsed CSS
    css = {}

    #Saves the parsed CSS (raw)
    _tokens = []

    #Printer class
    printer = None

    #Optimiser class
    _optimise = None

    #Saves the CSS charset (@charset)
    _charset = ''

    #Saves all @import URLs
    _import = []

    #Saves the namespace
    _namespace = ''

    #Contains the version of csstidy
    _version = '1.3'

    #Stores the settings
    _settings = {}

    # Saves the parser-status.
    #
    # Possible values:
    # - is = in selector
    # - ip = in property
    # - iv = in value
    # - instr = in string (started at " or ' or ( )
    # - ic = in comment (ignore everything)
    # - at = in @-block
    _status = 'is'

    #Saves the current at rule (@media)
    _at = ''

    #Saves the current selector
    _selector = ''

    #Saves the current property
    _property = ''

    #Saves the position of , in selectors
    _sel_separate = []

    #Saves the current value
    _value = ''

    #Saves the current sub-value
    _sub_value = ''

    #Saves all subvalues for a property.
    _sub_value_arr = []

    #Saves the char which opened the last string
    _str_char = ''
    _cur_string = ''

    #Status from which the parser switched to ic or instr
    _from = ''

    #Variable needed to manage string-in-strings, for example url("foo.png")
    _str_in_str = False

    #=True if in invalid at-rule
    _invalid_at = False

    #=True if something has been added to the current selector
    _added = False

    #Saves the message log
    _log = {}

    #Saves the line number
    _line = 1

    def __init__(self):
        self._settings['remove_bslash'] = True
        self._settings['compress_colors'] = True
        self._settings['compress_font-weight'] = True
        self._settings['lowercase_s'] = False
        self._settings['optimise_shorthands'] = 2
        self._settings['remove_last_'] = False
        self._settings['case_properties'] = 1
        self._settings['sort_properties'] = False
        self._settings['sort_selectors'] = False
        self._settings['merge_selectors'] = 2
        self._settings['discard_invalid_properties'] = False
        self._settings['css_level'] = 'CSS2.1'
        self._settings['preserve_css'] = False
        self._settings['timestamp'] = False

        self.load_template('highest_compression')
        self.printer = CSSTidyPrint(self)
        self._optimise = CSSTidyOptimise(self)

    #Get the value of a setting.
    def get_cfg(self, setting):
        return self._settings.get(setting, False)

    #Set the value of a setting.
    def set_cfg(self, setting, value):
        self._settings[setting] = value
        return True

    #Adds a token to $self._tokens
    def _add_token(self, ttype, data, do=False):
        if self.get_cfg('preserve_css') or do:
            if ttype == COMMENT:
                token = [ttype, data]
            else:
                token = [ttype, data.strip()]

            self._tokens.append(token)

    #Add a message to the message log
    def log(self, message, ttype, line = -1):
        if line == -1:
            line = self._line

        line = int(line)

        add = {'m': message, 't': ttype}
        if not self._log.has_key(line):
            self._log[line] = []
            self._log[line].append(add)
        elif add not in self._log[line]:
            self._log[line].append(add)

    #Parse unicode notations and find a replacement character
    def _unicode(self, string, i):
       #We want to leave unicode alone
       ##FIX##
       return ''

    #Loads a new template
    def load_template(self, content, from_file=True):
        predefined_templates = GLOBALS['csstidy']['predefined_templates']
        if content == 'high_compression' or content == 'default' or content == 'highest_compression' or content == 'low_compression':
            self._template = predefined_templates[content]
            return

        if from_file:
            try:
                f = open(content, "r")
                content = f.read().replace("\r\n", "\n")
            finally:
                f.close()

        self._template = content.split("|")

    #Starts parsing from URL
    def parse_from_url(self, url):
        try:
            if "http" in url.lower() or "https" in url.lower():
                f = urllib.urlopen(url)
            else:
                f = open(url)

            data = f.read()
            return self.parse(data)
        finally:
            f.close()

    #Checks if there is a token at the current position
    def is_token(self, string, i):
        tokens = GLOBALS['csstidy']['tokens']
        return (string[i] in tokens and not self.escaped(string, i))

    #Parses CSS in string. The code is saved as array in self.css
    def parse(self, string):
        all_properties = GLOBALS['csstidy']['all_properties']
        at_rules = GLOBALS['csstidy']['at_rules']

        self.css = {}
        self.printer.input_css = string;
        string = string.replace("\r\n", "\n") + ' '
        cur_comment = '';

        for i in xrange(len(string)):
            if string[i] == "\n" or string[i] == "\r":
                self._line += 1

            if self._status == 'at':
                if self.is_token(string, i):
                    if string[i] == '/' and string[i+1] == '*':
                        self._status = 'ic'
                        i += 1
                        self._from = 'at'

                    elif string[i] == '{':
                        self._status = 'is'
                        self._add_token(AT_START, self._at)

                    elif string[i] == ',':
                        self._at = self._at.strip() + ','

                    elif string[i] == '\\':
                        self._at += self._unicode(string, i)
                else:
                    lastpos = len(self._at)-1
                    if not (self._at[lastpos].isspace() or self.is_token(self._at, lastpos) and self._at[lastpos] == ',') and string[i].isspace():
                        self._at += string[i]

            elif self._status == 'is':
                if self.is_token(string, i):
                    if string[i] == '/' and string[i+1] == '*' and self._selector.strip() == '':
                        self._status = 'ic'
                        i += 1
                        self._from = 'is'
                    elif string[i] == '@' and self._selector.strip() == '':
                        #Check for at-rule
                        self._invalid_at = True
                        for name, ttype in at_rules.iteritems():
                            if string[i+1:len(name)].lower() == name.lower():
                                if ttype == 'at':
                                    self._at = '@' + name
                                else:
                                    self._selector = '@' + name

                                self._status = ttype
                                i += len(name)
                                self._invalid_at = False

                        if self._invalid_at:
                            self._selector = '@'
                            invalid_at_name = ''
                            for j in xrange(i+1, len(string)):
                                if not string[j].isalpha():
                                    break;

                                invalid_at_name += string[j]

                            self.log('Invalid @-rule: ' + invalid_at_name + ' (removed)', 'Warning')

                    elif string[i] == '"' or string[i] == "'":
                        self._cur_string = string[i]
                        self._status = 'instr'
                        self._str_char = string[i]
                        self._from = 'is'

                    elif self._invalid_at and string[i] == ';':
                        self._invalid_at = False
                        self._status = 'is'

                    elif string[i] == '{':
                        self._status = 'ip'
                        self._add_token(SEL_START, self._selector)
                        self._added = False;

                    elif string[i] == '}':
                        self._add_token(AT_END, self._at)
                        self._at = ''
                        self._selector = ''
                        self._sel_separate = []

                    elif string[i] == ',':
                        self._selector = self._selector.strip() + ','
                        self._sel_separate.append(len(self._selector))

                    elif string[i] == '\\':
                        self._selector += self._unicode(string, i)

                    #remove unnecessary universal selector,  FS#147
                    elif not (string[i] == '*' and string[i+1] in ('.', '#', '[', ':')):
                        self._selector += string[i]

                else:
                    lastpos = len(self._selector)-1

                    if lastpos == -1 or not ((self._selector[lastpos].isspace() or self.is_token(self._selector, lastpos) and self._selector[lastpos] == ',') and string[i].isspace()):
                        self._selector += string[i]

            #/* Case in-property */
            elif self._status == 'ip':
                if self.is_token(string, i):
                    if (string[i] == ':' or string[i] == '=') and self._property != '':
                        self._status = 'iv'
                        if not self.get_cfg('discard_invalid_properties') or self.property_is_valid(self._property):
                            self._add_token(PROPERTY, self._property)

                    elif string[i] == '/' and string[i+1] == '*' and self._property == '':
                        self._status = 'ic'
                        i += 1
                        self._from = 'ip'

                    elif string[i] == '}':
                        self.explode_selectors()
                        self._status = 'is'
                        self._invalid_at = False
                        self._add_token(SEL_END, self._selector)
                        self._selector = ''
                        self._property = ''

                    elif string[i] == ';':
                        self._property = ''

                    elif string[i] == '\\':
                        self._property += self._unicode(string, i)

                elif not string[i].isspace():
                    self._property += string[i]

            #/* Case in-value */
            elif self._status == 'iv':
                pn = (( string[i] == "\n" or string[i] == "\r") and self.property_is_next(string, i+1) or i == len(string)-1)
                if self.is_token(string, i) or pn:
                    if string[i] == '/' and string[i+1] == '*':
                        self._status = 'ic'
                        i += 1
                        self._from = 'iv'

                    elif string[i] == '"' or string[i] == "'" or string[i] == '(':
                        self._cur_string = string[i]
                        if string[i] == '(':
                            self._str_char = ')'
                        else:
                            string[i]

                        self._status = 'instr'
                        self._from = 'iv'

                    elif string[i] == ',':
                        self._sub_value = self._sub_value.strip() + ','

                    elif string[i] == '\\':
                        self._sub_value += self._unicode(string, i)

                    elif string[i] == ';' or pn:
                        if len(self._selector) > 0 and self._selector[0] == '@' and at_rules.has_key(self._selector[1:]) and at_rules[self._selector[1:]] == 'iv':
                            self._sub_value_arr.append(self._sub_value.strip())

                            self._status = 'is'

                            if self._selector == '@charset':
                                self._charset = self._sub_value_arr[0]
                            elif self._selector == '@namespace':
                                self._namespace = ' '.join(self._sub_value_arr)
                            elif self._selector == '@import':
                                self._import.append(' '.join(self._sub_value_arr))


                            self._sub_value_arr = []
                            self._sub_value = ''
                            self._selector = ''
                            self._sel_separate = []

                        else:
                            self._status = 'ip'

                    elif string[i] != '}':
                        self._sub_value += string[i]

                    if (string[i] == '}' or string[i] == ';' or pn) and self._selector != '':
                        if self._at == '':
                            self._at = DEFAULT_AT

                        #case settings
                        if self.get_cfg('lowercase_s'):
                            self._selector = self._selector.lower()

                        self._property = self._property.lower()

                        self._optimise.subvalue()
                        if self._sub_value != '':
                            self._sub_value_arr.append(self._sub_value)
                            self._sub_value = ''

                        self._value = ' '.join(self._sub_value_arr)

                        self._selector = self._selector.strip()

                        self._optimise.value()

                        valid = self.property_is_valid(self._property)

                        if (not self._invalid_at or self.get_cfg('preserve_css')) and (not self.get_cfg('discard_invalid_properties') or valid):
                            self.css_add_property(self._at, self._selector, self._property, self._value)
                            self._add_token(VALUE, self._value)
                            self._optimise.shorthands()

                        if not valid:
                            if self.get_cfg('discard_invalid_properties'):
                                self.log('Removed invalid property: ' + self._property, 'Warning')

                            else:
                                self.log('Invalid property in ' + self.get_cfg('css_level').upper() + ': ' + self._property, 'Warning')

                        self._property = '';
                        self._sub_value_arr = []
                        self._value = ''

                    if string[i] == '}':
                        self.explode_selectors()
                        self._add_token(SEL_END, self._selector)
                        self._status = 'is'
                        self._invalid_at = False
                        self._selector = ''

                elif not pn:
                    self._sub_value += string[i]

                    if string[i].isspace():
                        self._optimise.subvalue()
                        if self._sub_value != '':
                            self._sub_value_arr.append(self._sub_value)
                            self._sub_value = ''


            #/* Case in string */
            elif self._status == 'instr':
                if self._str_char == ')' and (string[i] == '"' or string[i] == '\'') and not self._str_in_str and not self.escaped(string, i):
                    self._str_in_str = True

                elif (self._str_char == ')' and string[i] == '"' or string[i] == '\'') and self._str_in_str and not self.escaped(string, i):
                    self._str_in_str = False

                temp_add = string[i] # ...and no not-escaped backslash at the previous position
                if (string[i] == "\n" or string[i] == "\r") and not (string[i-1] == '\\' and not self.escaped(string, i-1)):
                    temp_add = "\\A "
                    self.log('Fixed incorrect newline in string', 'Warning')

                if not (self._str_char == ')' and string[i] in GLOBALS['csstidy']['whitespace']):
                    self._cur_string += temp_add

                if string[i] == self._str_char and not self.escaped(string, i) and not self._str_in_str:
                    self._status = self._from
                    regex = re.compile(r'([\s]+)', re.I | re.U | re.S)
                    if regex.match(self._cur_string) is None and self._property != 'content':
                        if self._str_char == '"' or self._str_char == '\'':
                            self._cur_string = self._cur_string[1:-1]

                        elif len(self._cur_string) > 3 and (self._cur_string[1] == '"' or self._cur_string[1] == '\''):
                            self._cur_string = self._cur_string[0] + self.cur_string[2:-2] + self._cur_string[-1]

                    if self._from == 'iv':
                        self._sub_value += self._cur_string

                    elif self._from == 'is':
                        self._selector += self._cur_string

            #/* Case in-comment */
            elif self._status == 'ic':
                if string[i] == '*' and string[i+1] == '/':
                    self._status = self._from
                    i += 1
                    self._add_token(COMMENT, cur_comment)
                    cur_comment = ''

                else:
                    cur_comment += string[i]

        self._optimise.postparse()

        self.printer._reset()

        if not (len(self.css) == 0 and len(self._import) == 0 and len(self._charset) == 0 and len(self._tokens) == 0 and len(self._namespace) == 0):
            return self.printer.plain()

        return None

    #Explodes selectors
    def explode_selectors(self):
        #Explode multiple selectors
        if self.get_cfg('merge_selectors') == 1:
            new_sels = []
            lastpos = 0;
            self._sel_separate.append(len(self._selector))

            for num, pos in self._sel_separate.iteritems():
                if num == (len(self._sel_separate)-1):
                    pos += 1

                new_sels.append(self._selector[lastpos:(pos-lastpos-1)])
                lastpos = pos

            if len(new_sels) > 1:
                for selector in new_sels.itervalues():
                    self.erge_css_blocks(self._at, selector, self.css[self._at][self._selector])

                del self.css[self._at][self._selector]

        self._sel_separate = []

    #Checks if a character is escaped (and returns True if it is)
    def escaped(self, string, pos):
        return not (string[pos-1] != '\\' or self.escaped(string, pos-1))

    #Adds a property with value to the existing CSS code
    def css_add_property(self, media, selector, prop, new_val):
        if self.get_cfg('preserve_css') or new_val.strip() == '':
            return

        if not self.css.has_key(media):
            self.css[media] = {}

        if not self.css[media].has_key(selector):
            self.css[media][selector] = {}

        self._added = True
        if self.css[media][selector].has_key(prop):
            if (self.is_important(self.css[media][selector][prop]) and self.is_important(new_val)) or not self.is_important(self.css[media][selector][prop]):
                del self.css[media][selector][prop]
                self.css[media][selector][prop] = new_val.strip()

        else:
            self.css[media][selector][prop] = new_val.strip()

    #Adds CSS to an existing media/selector
    def merge_css_blocks(self, media, selector, css_add):
        for prop, value in css_add.iteritems():
            self.css_add_property(media, selector, prop, value, False)

    #Checks if $value is !important.
    def is_important(self, value):
        return '!important' in value.lower()

    #Returns a value without !important
    def gvw_important(self, value):
        if self.is_important(value):
            ret = value.strip()
            ret = ret[0:-9]
            ret = ret.strip()
            ret = ret[0:-1]
            ret = ret.strip()
            return ret

        return value

    #Checks if the next word in a string from pos is a CSS property
    def property_is_next(self, istring, pos):
        all_properties = GLOBALS['csstidy']['all_properties']
        istring = istring[pos: (len(istring)-pos)]
        pos = istring.find(':')
        if pos == -1:
            return False;

        istring = istring[:pos].strip().lower()
        if all_properties.has_key(istring):
            self.log('Added semicolon to the end of declaration', 'Warning')
            return True

        return False;

    #Checks if a property is valid
    def property_is_valid(self, prop):
        all_properties = GLOBALS['csstidy']['all_properties']
        return (all_properties.has_key(prop) and all_properties[prop].find(self.get_cfg('css_level').upper()) != -1)


if __name__ == '__main__':
    import sys
    inp = sys.argv[1]
    f = open(inp, "r")
    data = f.read()
    f.close()
    tidy = CSSTidy()
    print tidy.parse(data)

