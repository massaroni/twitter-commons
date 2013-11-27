import sys
import jsonpickle
import os

from twitter.common import app
from twitter.thrift.text import thrift_json_encoder
from twitter.thrift.descriptors.thrift_parser import ThriftParser
from twitter.thrift.descriptors.thrift_parser_error import ThriftParserError

app.add_option('--input_file', default='', type='string',
               help='The thrift file to generate service code from')
app.add_option('--includes_dir', default='', type='string',
               help='The absolute path to a directory to prepend to thrift includes relative path')
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
    includesDir = options.includes_dir
    angularModule = options.angular_module

    print 'Input file is ', inputfile
    print 'Output path is ', outputPath
    print 'Includes dir is ', includesDir
    print 'Angular Module is ', angularModule

    thriftJSON = parseThriftToJSON(inputfile)

    includesMap = getIncludes(thriftJSON, includesDir)

    if 'services' in thriftJSON.keys():
        for service in thriftJSON['services']:
            writeAngularService(service, thriftJSON, includesMap, outputPath, angularModule)


def parseThriftToJSON(inputfile):
    parser = ThriftParser()
    print('Parsing file %s...' % inputfile)
    program = parser.parse_file(inputfile)
    print('Parse was success.')
    print('decoding to JSON.')
    thriftJson = thrift_json_encoder.thrift_to_json(program)
    # print '!!!!!!!!BEGIN JSON for ' + inputfile
    # print thriftJson
    # print '!!!!!!!!END JSON for ' + inputfile
    unpickled = jsonpickle.decode(thriftJson)
    print('JSON decode was success.')
    return unpickled


def getIncludes(thriftJSON, includesDir):
    includes = {}
    if 'includes' in thriftJSON.keys():
        for include in thriftJSON['includes']:
            includePath = include['path']
            includeJSON = parseThriftToJSON(includesDir + includePath)
            thriftName = includePath.split('.')[0].split('/')[-1]
            includes[thriftName] = includeJSON
    return includes


def writeAngularService(service, thriftJSON, includesMap, outputPath, angularModuleName):
    serviceName = service['name']
    print('writing angular service: ' + serviceName)
    serviceJsFile = createJsFile(outputPath, serviceName + ".js")

    writeServiceDefinition(angularModuleName, serviceJsFile, serviceName)

    serviceVarName = firstLower(serviceName)
    writeServiceInitialization(serviceJsFile, serviceName, serviceVarName)

    for function in service['functions']:
        writeServiceFunction(function, serviceJsFile, serviceVarName, thriftJSON, includesMap)

    serviceJsFile.write("  return " + serviceVarName + ";\n")
    serviceJsFile.write("}]);")
    print('writing angular service: ' + serviceName + ' complete')


def createJsFile(outputPath, filename):
    basedir = os.path.dirname(outputPath)
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    file = open(outputPath + filename, 'w')
    print('Created js file at ' + outputPath + filename + ".js")
    return file


def writeServiceDefinition(angularModuleName, serviceJsFile, serviceName):
    serviceJsFile.write("'use strict';\n")
    serviceJsFile.write("\n")
    serviceJsFile.write("angular.module('" + angularModuleName + "')\n")
    serviceJsFile.write(".service('" + serviceName + "', ['$log', '$q', 'ThriftService', 'UrlRegistry', function ("
                                                     "$log, $q, ThriftService, UrlRegistry) {\n")
    serviceJsFile.write("\n")


def firstLower(s):
    if len(s) == 0:
        return s
    else:
        return s[0].lower() + s[1:]


def writeServiceInitialization(serviceJsFile, serviceName, serviceVarName):
    serviceJsFile.write("  var " + serviceVarName + " = {};\n")
    serviceJsFile.write("\n")
    serviceJsFile.write("  var url = UrlRegistry.getUrl('" + serviceVarName + "');\n")
    serviceJsFile.write("  var client = ThriftService.newClient('" + serviceName + "Client', url);\n")
    serviceJsFile.write("\n")
    serviceJsFile.write("\n")


def writeServiceFunction(function, serviceJsFile, serviceVarName, thriftJSON, includesMap):
    argumentNames = getArgumentNames(function)
    argumentsString = ", ".join(argumentNames)
    functionName = function['name']
    print('writing function ' + functionName)

    serviceJsFile.write("  " + serviceVarName + "." + functionName + " = function (" + argumentsString + ") {\n")

    writeArgumentChecks(function, serviceJsFile, thriftJSON, includesMap)

    serviceJsFile.write('    var deferred = $q.defer();\n')
    serviceJsFile.write('\n')

    writeSuccessCallback(function, functionName, serviceJsFile, thriftJSON)

    writeErrorCallback(functionName, serviceJsFile)

    writeThriftRequest(argumentNames, functionName, serviceJsFile)

    serviceJsFile.write('    return deferred.promise;\n')
    serviceJsFile.write('  };\n')
    serviceJsFile.write('\n')
    print('writing function ' + functionName + ' complete')


def getArgumentNames(function):
    argumentNames = []
    for argument in function["argz"]:
        argumentNames.append(argument['name'])
    return argumentNames


def writeArgumentChecks(function, serviceJsFile, thriftJSON, includesMap):
    for argument in function["argz"]:
        argumentName = argument['name']

        serviceJsFile.write("    if(" + argumentName + " == null")

        argumentTypeId = argument['typeId']
        if isTypeAnObject(argumentTypeId, thriftJSON):
            argumentIsEnum = False
            argumentClass = getTypeClassName(argumentTypeId, thriftJSON)
            # if there is a dot that means its coming from an include
            if '.' in argumentClass:
                argumentClassSplit = argumentClass.split('.')
                argumentIncludeName = argumentClassSplit[0]
                argumentClass = argumentClassSplit[1]
                if argumentIncludeName in includesMap.keys():
                    argumentIsEnum = isEnum(argumentClass, includesMap[argumentIncludeName])
            else:
                argumentIsEnum = isEnum(argumentClass, thriftJSON)

            if argumentIsEnum is False:
                serviceJsFile.write(" || !" + argumentName + " instanceof " + argumentClass)

        serviceJsFile.write(") {\n")
        serviceJsFile.write('      throw "Invalid ' + argumentName + '";\n')
        serviceJsFile.write('    }\n')
    serviceJsFile.write('\n')


def isTypeAnObject(typeId, thriftJSON):
    typesMap = thriftJSON['typeRegistry']['idToType']
    if 'typeref' in typesMap[typeId]['simpleType'].keys():
        return True
    return False


def getTypeClassName(typeId, thriftJSON):
    typesMap = thriftJSON['typeRegistry']['idToType']
    typeRef = typesMap[typeId]['simpleType']['typeref']
    argumentClass = typeRef['typeAlias']
    return argumentClass


def isEnum(argumentClass, thriftJSON):
    if 'enums' in thriftJSON.keys():
        for enum in thriftJSON['enums']:
            if enum['name'] == argumentClass:
                return True

    return False


def writeSuccessCallback(function, functionName, serviceJsFile, thriftJSON):
    typesMap = thriftJSON['typeRegistry']['idToType']
    if 'typeref' in typesMap[function['returnTypeId']]['simpleType'].keys():
        returnObjName = firstLower(typesMap[function['returnTypeId']]['simpleType']['typeref']['typeAlias'])
        if '.' in returnObjName:
            returnObjName = returnObjName.split('.')[1]
    else:
        returnObjName = 'response'
    serviceJsFile.write('    var successCallback = function(' + returnObjName + ') {\n')
    serviceJsFile.write("      $log.debug('" + functionName + " Success!');\n")
    serviceJsFile.write("      deferred.resolve(" + returnObjName + ");\n")
    serviceJsFile.write("    };\n")
    serviceJsFile.write('\n')


def writeErrorCallback(functionName, serviceJsFile):
    serviceJsFile.write('    var errorCallback = function() {\n')
    serviceJsFile.write("      var msg = '" + functionName + " Failed! status:' + status;\n")
    serviceJsFile.write("      deferred.reject(new Error(msg));\n")
    serviceJsFile.write("    };\n")
    serviceJsFile.write('\n')


def writeThriftRequest(argumentNames, functionName, serviceJsFile):
    argumentNames.insert(0, "'" + functionName + "'")
    argumentsString = ", ".join(argumentNames)
    serviceJsFile.write("    var requestPromise = client.makeThriftRequest(" + argumentsString + ");\n")
    serviceJsFile.write('\n')
    serviceJsFile.write("    requestPromise.then(successCallback, errorCallback);\n")
    serviceJsFile.write('\n')


app.main()