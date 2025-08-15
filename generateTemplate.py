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

def parseHelp(line):
    helpOption = re.search(r'(?<=help=")[^"]*', line)
    if helpOption is not None:
        return '  # ' + helpOption[0] + '\n'
    else:
        return ''

def parseConfig(line):
    configOption = '  ' + re.sub('-', '', line.split('"')[1]) + ':\n'
    return configOption

def getConfigKey(line):
    return re.sub('-', '', line.split('"')[1])

def parseMetavar(line):
    metavar = re.search(r'(?<=metavar=")[^"]*', line)
    if metavar is not None:
        return '  # type: ' + metavar[0] + '\n'
    elif 'store_true' in line:
        return '  # type: BOOLEAN\n'
    else:
        return ''

def parseRepeatable(line):
    if 'action="append"' in line:
        return '  # REPEATABLE: YES (use YAML array) ' + '\n'
    else:
        return ''

def parseDefault(line):
    default = re.search(r'(?<=default=")[^"]*', line)
    if default is not None:
        if default[0] == '':
            return '  # default: [empty string] \n'
        return '  # default: ' + default[0] + '\n'
    else:
        return ''

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
                    entry += parseHelp(parsedline)
                    entry += parseMetavar(parsedline)
                    entry += parseDefault(parsedline)
                    entry += parseRepeatable(parsedline)
                    entry += parseConfig(parsedline)
                    
                    yamlContent += entry
        with open('example.yaml', 'w') as t:
            t.write(yamlContent)


def getVariableType(key):
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
                    if key in line:
                        print('hit')
                        entry = ''
                        parsedline = ansi_escape.sub('', line)
                        entry += parseHelp(parsedline)
                        entry += parseMetavar(parsedline)
                        entry += parseDefault(parsedline)
                        entry += parseRepeatable(parsedline)
                        return entry
    return ''

def createVolume():
    pass


createValuesYAML()
createConfigMap()
createVolume()
volflags = """\n\nvolumes:
  - volumeName1:
    httpURL: /the/url/to/share/this/volume/on/
    mountPath: /the/actual/filesystem/path/
    existingClaim: ""
    storageClass: "longhorn-nvme"
    resources:
      requests:
        storage: 2Gi
      limits:
        # @TODO: Sync with vmaxb
        storage: 3Gi
    # @TODO: Move to config since copyparty can't do RWX anyway (or should not at least)
    accessModes:
      - ReadWriteOnce
    volflags:"""
ansi_escape = re.compile(r'\\033\[[0-?]*[ -/]*[@-~]')

for key in flagcats.keys():
    volflags += "\n      " + re.sub('\W', '_',camelCase(re.sub('\n.*', '', key))) + ':\n'
    for l2key in flagcats[key].keys():
        content = ansi_escape.sub('', flagcats[key][l2key])
        content = re.sub('\n', '', content)
        volflags += '        # ' + content + '\n'
        if '=' in l2key:
            l2key = l2key.split('=')

            volflags += '        # Example: ' + l2key[1] + '\n'
            l2key = l2key[0]
        
        volflags += re.sub('\s{2,6}', '        ', getVariableType(l2key))
        volflags += '        ' + l2key + ':\n'
with open('example.yaml', 'a') as t:
    t.write(volflags)