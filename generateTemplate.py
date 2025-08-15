import re
from re import sub
import os
import sys

# @TODO: Change on merge!
sys.path.append('../')
from copyparty.copyparty.cfg import flagcats
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

def getConfigKey(line):
    return re.sub('-', '', line.split('"')[1])

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

def createConfigMap():
    with open(COPYPARTY_MAIN) as copyparty:
        yamlContent = '    [global]\n'
        currentGroup = ''
        ansi_escape = re.compile(r'\\033\[[0-?]*[ -/]*[@-~]')
        for line in copyparty.readlines():
            if 'add_argument' in line:
                if  'help sections' in line or '        ap2' in line:
                    pass
                elif 'add_argument_group' in line:
                    currentGroup = re.sub('\W', '_', camelCase((line.split('"')[1])))

                else:
                    entry = ''
                    parsedline = ansi_escape.sub('', line)
                    if 'action="append"' in parsedline:
                        entry = '    {{{{- if .Values.{group}.{value} }}}}\n'.format(group=currentGroup, value=getConfigKey(line))
                        entry += '      {{{{- range .Values.{group}.{value} }}}}\n'.format(group=currentGroup, value=getConfigKey(line))
                        entry += '      {value}: {{{{ . }}}}\n'.format(value=getConfigKey(line))
                        entry += '    {{- end }}\n'
                    elif 'action="store_true"' in parsedline:
                        entry = '    {{{{- if .Values.{group}.{value} }}}}\n'.format(group=currentGroup, value=getConfigKey(line))
                        entry += '      {value}\n'.format(value=getConfigKey(line))
                        entry += '    {{- end }}\n'
                    else: 
                        entry = '    {{{{- if .Values.{group}.{value} }}}}\n'.format(group=currentGroup, value=getConfigKey(line))
                        entry += '      {value}: {{{{ .Values.{group}.{value} }}}}\n'.format(group=currentGroup, value=getConfigKey(line))
                        entry += '    {{- end }}\n'
                    yamlContent
                    
                    yamlContent += entry
        yamlContent = """apiVersion: v1
kind: ConfigMap
metadata:
  name: copyparty-configmap
  namespace: {{ include "common.names.namespace" . | quote }}
  labels: {{- include "common.labels.standard" ( dict "customLabels" .Values.commonLabels "context" $ ) | nindent 4 }}
  {{- if .Values.commonAnnotations }}
  annotations: {{- include "common.tplvalues.render" ( dict "value" .Values.commonAnnotations "context" $ ) | nindent 4 }}
  {{- end }}
data:
  copyparty.cfg: |
""" + yamlContent
        with open('configmap.yaml', 'w') as t:
            t.write(yamlContent)

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
                    entry = parseHelp(parsedline, entry)
                    entry = parseMetavar(parsedline, entry)
                    entry = parseDefault(parsedline, entry)
                    entry = parseRepeatable(parsedline, entry)
                    entry = parseConfig(parsedline, entry)
                    
                    yamlContent += entry
        with open('example.yaml', 'w') as t:
            t.write(yamlContent)

def createVolume():
    pass


createValuesYAML()
createConfigMap()
createVolume()
for key in flagcats.keys():
    print(re.sub('\W', '_',camelCase(re.sub('\n.*', '', key))))
    for l2key in flagcats[key].keys():
        print('  ' + l2key)
