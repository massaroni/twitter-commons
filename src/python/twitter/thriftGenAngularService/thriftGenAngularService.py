import sys
import jsonpickle
import os

from twitter.common import app
from twitter.thrift.text import thrift_json_encoder
from twitter.thrift.descriptors.thrift_parser import ThriftParser
from twitter.thrift.descriptors.thrift_parser_error import ThriftParserError

app.add_option('--input_file', default='', type='string',
               help='The thrift file to generate service code from')
app.add_option('--output_path', default='', type='string',
               help='The path to save the generate code to')
app.add_option('--angular_module', default='services', type='string',
               help='The angular module to append the service to')


def main(args, options):
    inputfile = options.input_file
    if inputfile is '':
        print 'Input file is required'
        return
    outputPath = options.output_path
    if outputPath is '':
        print 'Output path is required'
        return
    angularModule = options.angular_module

    print 'Input file is ', inputfile
    print 'Output path is ', outputPath
    print 'Angular Module is ', angularModule

    parser = ThriftParser()
    print('Parsing file %s...' % inputfile)
    program = parser.parse_file(inputfile)
    print('Parse was success.')
    print('decoding to JSON.')
    thriftJson = thrift_json_encoder.thrift_to_json(program)
    unpickled = jsonpickle.decode(thriftJson)
    print('JSON decode was success.')
    if 'services' in unpickled:
        for service in unpickled['services']:
            writeAngularService(outputPath, service, unpickled['typeRegistry']['idToType'], angularModule)


def writeServiceFunction(function, serviceJsFile, serviceVarName, typesMap):
    argumentNames = []
    for argument in function["argz"]:
        argumentNames.append(argument['name'])
    argumentsString = ", ".join(argumentNames)
    functionName = function['name']
    print('writing function ' + functionName)
    serviceJsFile.write("  " + serviceVarName + "." + functionName + " = function (" + argumentsString + ") {\n")
    for argument in function["argz"]:
        argumentName = argument['name']
        argumentTypeId = argument['typeId']
        argumentClass = ''
        if 'typeref' in typesMap[argumentTypeId]['simpleType'].keys():
            typeRef = typesMap[argumentTypeId]['simpleType']['typeref']
            argumentClass = typeRef['typeAlias']
            if '.' in argumentClass:
                argumentClass = argumentClass.split('.')[1]
        serviceJsFile.write("    if(" + argumentName + " == null")
        if argumentClass != '':
            serviceJsFile.write("|| !" + argumentName + " instanceof " + argumentClass)
        serviceJsFile.write(") {\n")
        serviceJsFile.write('      throw "Invalid ' + argumentName + '";\n')
        serviceJsFile.write('    }\n')
    serviceJsFile.write('\n')
    serviceJsFile.write('    var deferred = $q.defer();\n')
    serviceJsFile.write('\n')
    returnObjName = firstLower(typesMap[function['returnTypeId']]['simpleType']['typeref']['typeAlias'])
    if '.' in returnObjName:
        returnObjName = returnObjName.split('.')[1]
    serviceJsFile.write('    var successCallback = function(' + returnObjName + ') {\n')
    serviceJsFile.write("      $log.debug('" + functionName + " Success!');\n")
    serviceJsFile.write("      deferred.resolve(" + returnObjName + ");\n")
    serviceJsFile.write("    };\n")
    serviceJsFile.write('\n')
    serviceJsFile.write('    var errorCallback = function() {\n')
    serviceJsFile.write("      var msg = '" + functionName + " Failed! status:' + status;\n")
    serviceJsFile.write("      deferred.reject(new Error(msg));\n")
    serviceJsFile.write("    };\n")
    serviceJsFile.write('\n')
    serviceJsFile.write("    var requestPromise = client.makeThriftRequest('" + functionName
                        + "', " + argumentsString + ");\n")
    serviceJsFile.write('\n')
    serviceJsFile.write("    requestPromise.then(successCallback, errorCallback);\n")
    serviceJsFile.write('\n')
    serviceJsFile.write('    return deferred.promise;\n')
    serviceJsFile.write('  };\n')
    serviceJsFile.write('\n')
    print('writing function ' + functionName + ' complete')


def firstLower(s):
    if len(s) == 0:
        return s
    else:
        return s[0].lower() + s[1:]


def writeAngularService(outputPath, service, typesMap, angularModuleName):
    serviceName = service['name']
    print('writing angular service: ' + serviceName)
    serviceJsFile = createJsFile(outputPath, serviceName + ".js")
    print('Created js file at ' + outputPath + serviceName + ".js")
    serviceJsFile.write("'use strict';\n")
    serviceJsFile.write("\n")
    serviceJsFile.write("angular.module('" + angularModuleName + "')\n")
    serviceJsFile.write(".service('" + serviceName + "', ['$log', '$q', 'ThriftService', 'UrlRegistry', function ("
                                                     "$log, $q, ThriftService, UrlRegistry) {\n")
    serviceJsFile.write("\n")
    serviceVarName = firstLower(serviceName)
    serviceJsFile.write("  var " + serviceVarName + " = {};\n")
    serviceJsFile.write("\n")
    serviceJsFile.write("  var url = UrlRegistry.getUrl('" + serviceVarName + "');\n")
    serviceJsFile.write("  var client = ThriftService.newClient('" + serviceName + "Client', url);\n")
    serviceJsFile.write("\n")
    serviceJsFile.write("\n")
    for function in service['functions']:
        writeServiceFunction(function, serviceJsFile, serviceVarName, typesMap)
    serviceJsFile.write("  return " + serviceVarName + ";\n")
    serviceJsFile.write("}]);")
    print('writing angular service: ' + serviceName + ' complete')


def createJsFile(outputPath, filename):
    basedir = os.path.dirname(outputPath)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    return open(outputPath + filename, 'w')


app.main()