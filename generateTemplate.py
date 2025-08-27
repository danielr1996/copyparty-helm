import re
import string
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

def escapeAnsi(text):
    return re.compile(r'(?:\\x1b|\\033|\\e)', flags=re.IGNORECASE).sub('', re.compile(r'(?:\\x1b|\\033|\\e)\[[0-?]*[ -/]*[@-~]', flags=re.IGNORECASE).sub('', re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])').sub('', text)))

def parseConfig(line):
    configOption = '  ' + re.sub('-', '', line.split('"')[1]) + ':\n'
    return configOption

def getConfigKey(line):
    return re.sub('-', '', line.split('"')[1])

def parseMetavar(line):
    metavar = re.search(r'(?<=metavar=")[^"]*', line)
    if metavar is not None:
        if 'action="append"' in line:
            return '  # type: ' + metavar[0] + '\n' + '  # type: ARRAY' + '\n'
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
        for line in copyparty.readlines():
            if 'add_argument' in line:
                if  'help sections' in line or '        ap2' in line:
                    pass
                elif 'add_argument_group' in line:
                    currentGroup = re.sub('\W', '_', camelCase((line.split('"')[1])))

                else:
                    entry = ''
                    parsedline = escapeAnsi(line)
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
                    yamlContent += entry
        yamlContent = """apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "copyparty-helm.fullname" . }}-config
  namespace: {{ .Values.namespace | .Release.namespace }}

data:
  copyparty.cfg: |
""" + yamlContent
        with open('templates/configmap.yaml', 'w') as t:
            t.write(yamlContent)

def createValuesYAML():
    with open(COPYPARTY_MAIN) as copyparty:
        yamlContent = '''namespace: copyparty
replicaCount: 1
image:
  repository: copyparty/ac
  pullPolicy: IfNotPresent
  tag: "1.19.1"
imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  automount: true
  annotations: {}
  name: ""

podAnnotations: {}
podLabels: {}

podSecurityContext: {}

securityContext: {}

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  className: ""
  annotations: {}
    # kubernetes.io/ingress.class: nginx
    # kubernetes.io/tls-acme: "true"
  hosts:
    - host: copyparty.local
      paths:
        - path: /
  tls: []
  #  - secretName: copyparty-tls
  #    hosts:
  #      - copyparty.local

resources: {}
  # We usually recommend not to specify default resources and to leave this as a conscious
  # choice for the user. This also increases chances charts run on environments with little
  # resources, such as Minikube. If you do want to specify resources, uncomment the following
  # lines, adjust them as necessary, and remove the curly braces after 'resources:'.
  # limits:
  #   cpu: 100m
  #   memory: 128Mi
  # requests:
  #   cpu: 100m
  #   memory: 128Mi

# This is to setup the liveness and readiness probes more information can be found here: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
livenessProbe:
  httpGet:
    path: /
    port: http
readinessProbe:
  httpGet:
    path: /
    port: http

autoscaling:
  enabled: false
  minReplicas: 1
  # increase ONLY if Copyparty will NOT write to the volumes. Also, accessMode needs to be RWX, not RWO
  maxReplicas: 1
  targetCPUUtilizationPercentage: 100
  # targetMemoryUtilizationPercentage: 80

# Additional volumeMounts on the output Deployment definition.
volumeMounts: []

nodeSelector: {}

tolerations: []

affinity: {}
'''
        for line in copyparty.readlines():
            if 'add_argument' in line:
                if  'help sections' in line or '        ap2' in line:
                    pass
                elif 'add_argument_group' in line:
                    yamlContent += '\n' + re.sub('\W', '_', camelCase((line.split('"')[1]))) + ':\n'
                else:
                    entry = ''
                    parsedline = escapeAnsi(line)
                    entry += parseHelp(parsedline)
                    entry += parseMetavar(parsedline)
                    entry += parseDefault(parsedline)
                    entry += parseRepeatable(parsedline)
                    entry += parseConfig(parsedline)
                    
                    yamlContent += entry
        with open('values.yaml', 'w') as t:
            t.write(yamlContent)


def getVariableInfo(key):
    with open(COPYPARTY_MAIN) as copyparty:
        yamlContent = ''
        for line in copyparty.readlines():
            if 'add_argument' in line:
                if  'help sections' in line or '        ap2' in line:
                    pass
                elif 'add_argument_group' in line:
                    yamlContent += '\n' + re.sub('\W', '_', camelCase((line.split('"')[1]))) + ':\n'
                else:
                    if key in line:
                        entry = ''
                        parsedline = escapeAnsi(line)
                        entry += parseHelp(parsedline)
                        entry += parseMetavar(parsedline)
                        entry += parseDefault(parsedline)
                        entry += parseRepeatable(parsedline)
                        return entry
    return ''

def getVariableType(key):
    with open(COPYPARTY_MAIN) as copyparty:
        yamlContent = ''
        for line in copyparty.readlines():
            if 'add_argument' in line:
                if  'help sections' in line or '        ap2' in line:
                    pass
                elif 'add_argument_group' in line:
                    yamlContent += '\n' + re.sub('\W', '_', camelCase((line.split('"')[1]))) + ':\n'
                else:
                    if key in line:
                        parsedline = escapeAnsi(line)
                        if 'action="append"' in parsedline:
                            return 'ARRAY'
                        elif 'action="store_true"' in parsedline:
                            return 'BOOLEAN'
                        else:
                            return 'ARGUMENT'
    return 'NOTFOUND'

def createVolume():
    volflags = """\n\nvolumes:
  - name: volumeName1
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
    prevkey = ''
    currentkey = ''
    for key in flagcats.keys():
        volflags += "\n      " + re.sub('\W', '_',camelCase(re.sub('\n.*', '', key))) + ':\n'
        for l2key in flagcats[key].keys():
            prevkey = currentkey
            if '=' in l2key:
                currentkey = l2key.split('=')[0]
            else:
                currentkey = l2key
            content = escapeAnsi(flagcats[key][l2key])
            content = re.sub('\n', '', content)
            volflags += '        # ' + content + '\n'
            if '=' in l2key:
                l2key = l2key.split('=')

                volflags += '        # Example: ' + l2key[1] + '\n'
                l2key = l2key[0]
            volflags += re.sub(' {2,6}', '        ', getVariableInfo(l2key))
            if getVariableType(l2key) == 'NOTFOUND':
                volflags += '        # !!!VARIABLE TEMPLATING INFORMATION NOT FOUND IN COPYPARTY CODE!!!\n        # This is expected behavior with some options that are only available as volflags.\n        # Please input the text that should appear in the copyparty config verbatim as this key\'s value.\n        # !!!VARIABLE TEMPLATING INFORMATION NOT FOUND IN COPYPARTY CODE!!!\n'
            if prevkey != currentkey:
                volflags += '        ' + l2key + ':\n'
    with open('values.yaml', 'a') as t:
        t.write(volflags)

def createVolflagConfigMap():
    with open(COPYPARTY_MAIN) as copyparty:
        yamlContent = """    {{- range .Values.volumes }}
        [{{ .httpURL }}]
        {{ .mountPath }}
        accs:
            {{ .permissions }}
        flags:\n"""

        for key in flagcats.keys():
            outerGroup = re.sub('\W', '_',camelCase(re.sub('\n.*', '', key)))
            for l2key in flagcats[key].keys():
                if '=' in l2key:
                    l2key = l2key.split('=')[0]
                variableType = getVariableType(l2key)
                if variableType == 'BOOLEAN':
                    entry = '      {{{{- if .volflags.{group}.{value} }}}}\n'.format(group=outerGroup, value=l2key)
                    entry += '        {value}\n'.format(value=l2key)
                    entry += '      {{- end }}\n'
                elif variableType == 'ARRAY':
                    entry = '      {{{{- if .volflags.{group}.{value} }}}}\n'.format(group=outerGroup, value=l2key)
                    entry += '        {{{{- range .volflags.{group}.{value} }}}}\n'.format(group=outerGroup, value=l2key)
                    entry += '        {value}: {{{{ . }}}}\n'.format(value=l2key)
                    entry += '      {{- end }}\n'
                elif variableType == 'NOTFOUND':
                    entry = '      {{{{- if .volflags.{group}.{value} }}}}\n'.format(group=outerGroup, value=l2key)
                    entry += '        {{{{ .volflags.{group}.{value} }}}}\n'.format(group=outerGroup, value=l2key)
                    entry += '      {{- end }}\n'
                else:
                    entry = '      {{{{- if .volflags.{group}.{value} }}}}\n'.format(group=outerGroup, value=l2key)
                    entry += '        {value}: {{{{ .volflags.{group}.{value} }}}}\n'.format(group=outerGroup, value=l2key)
                    entry += '      {{- end }}\n'
                yamlContent += entry
        yamlContent += '    {{- end }}\n'
        with open('templates/configmap.yaml', 'a') as t:
            t.write(yamlContent)


createValuesYAML()
createConfigMap()
createVolume()
createVolflagConfigMap()
