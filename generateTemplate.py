from re import sub
import re
import os

COPYPARTY_MAIN = os.getcwd() + '/../copyparty/copyparty/__main__.py'

def camelCase(s):
    # Use regular expression substitution to replace underscores and hyphens with spaces,
    # then title case the string (capitalize the first letter of each word), and remove spaces
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    
    # Join the string, ensuring the first letter is lowercase
    return ''.join([s[0].lower(), s[1:]])

# awk -F\" '/add_argument\("-[^-]/{print(substr($2,2))}' copyparty/__main__.py | sort | tr '\n' ' '

def parseHelp(line, entry):
    helpOption = re.search(r'(?<=help=")[^"]*', line)
    if helpOption is not None:
        return entry + '  # ' + helpOption[0] + '\n'
    else:
        return entry

def parseConfig(line, entry):
    configOption = '  ' + re.sub('-', '', line.split('"')[1]) + ':\n'
    return entry + configOption

def parseMetavar(line, entry):
    metavar = re.search(r'(?<=metavar=")[^"]*', line)
    if metavar is not None:
        return entry + '  # type: ' + metavar[0] + '\n'
    elif 'store_true' in line:
        return entry + '  # type: BOOLEAN\n'
    else:
        return entry

def parseRepeatable(line, entry):
    if 'action="append"' in line:
        return entry + '  # REPEATABLE: YES (use YAML array) ' + '\n'
    else:
        return entry

def parseDefault(line, entry):
    default = re.search(r'(?<=default=")[^"]*', line)
    if default is not None:
        if default[0] == '':
            return entry + '  # default: [empty string] \n'
        return entry + '  # default: ' + default[0] + '\n'
    else:
        return entry

def createValuesYAML():
    with open(COPYPARTY_MAIN) as copyparty:
        yamlContent = ''
        ansi_escape = re.compile(r'\\033\[[0-?]*[ -/]*[@-~]')
        for line in copyparty.readlines():
            if 'add_argument' in line:
                if  'help sections' in line or '        ap2' in line:
                    pass
                elif 'add_argument_group' in line:
                    yamlContent += '\n' + re.sub('\W', '_', camelCase((line.split('"')[1]))) + ':\n'
                else:
                    entry = ''
                    parsedline = ansi_escape.sub('', line)
                    # print(parsedline)
                    entry = parseHelp(parsedline, entry)
                    entry = parseMetavar(parsedline, entry)
                    entry = parseDefault(parsedline, entry)
                    entry = parseRepeatable(parsedline, entry)
                    entry = parseConfig(parsedline, entry)
                    
                    yamlContent += entry
        with open('example.yaml', 'w') as t:
            t.write(yamlContent)


createValuesYAML()
