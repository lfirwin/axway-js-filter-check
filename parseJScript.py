import sys
import bs4
from pyjsparser import PyJsParser
import json
import glob
import os
import logging
from optparse import OptionParser
from collections import OrderedDict

class my_option_parser(OptionParser):
    def error(self, msg): # ignore unknown arguments
        pass


def parse_options(copyargs):
   parser = my_option_parser()
   parser.add_option("-f", "--file", dest="primary_store", help="PrimaryStore file name", default="")
   parser.add_option("-e", "--engine", dest="engine_name", help="JavaScript engine name", default="nashorn")
   parser.add_option("-l", "--log", dest="loglevel", help="Logging level", default="INFO")
   (options, args) = parser.parse_args(args=copyargs)
   return options


def parse_js(d, js_vars, depth):
    # Increment code tree depth
    depth += 1

    # Iterate over the outputted data structure from the parse
    for k, v in d.iteritems():
        if isinstance(v, dict):
            if v.get('type', None):
                if v['type'] == 'VariableDeclaration': # variable declaration - "var local_var"
                    js_vars.append(v['kind'] + ' ' + v['declarations'][0]['id']['name'] + ':' + str(depth))
                    logging.debug(v['kind'] + ' ' + v['declarations'][0]['id']['name'] + ':' + str(depth))
                elif v['type'] == 'AssignmentExpression': # assignment - "local_var = another_var"
                    try:
                        js_vars.append(v['left']['name'] + ':' + str(depth - 1))
                        logging.debug(v['left']['name'] + ':' + str(depth - 1))
                    except KeyError, e:
                        pass
                parse_js(v, js_vars, depth)
        elif isinstance(v, list):
            for entry in v:
                if isinstance(entry, dict):
                    if entry.get('type', None):
                        if entry['type'] == 'VariableDeclaration': # variable declaration - "var local_var"
                            js_vars.append(entry['kind'] + ' ' + entry['declarations'][0]['id']['name'] + ':' + str(depth))
                            logging.debug(entry['kind'] + ' ' + entry['declarations'][0]['id']['name'] + ':' + str(depth))
                        elif entry['type'] == 'FunctionDeclaration': # function declaration - "function(some_var)"
                            js_vars.append('function ' + entry['id']['name'] + ':' + str(depth))
                            logging.debug('function ' + entry['id']['name'] + ':' + str(depth))
                            for param in entry['params']:
                                js_vars.append('var ' + param['name'] + ':' + str(depth + 1))
                                logging.debug('var ' + param['name'] + ':' + str(depth + 1))
                        elif entry['type'] == 'IfStatement': # if statement
                            js_vars.append('if statement' + ':' + str(depth))
                            logging.debug('if statement' + ':' + str(depth))
                            parse_js(entry['consequent'], js_vars, depth)
                            if entry.get('alternate',None):
                                parse_js(entry['alternate'], js_vars, depth)
                        elif entry['type'] == 'ForStatement': # if statement
                            js_vars.append('for statement' + ':' + str(depth))
                            logging.debug('for statement' + ':' + str(depth))
                        elif entry['type'] == 'DoWhileStatement': # if statement
                            js_vars.append('dowhile statement' + ':' + str(depth))
                            logging.debug('dowhile statement' + ':' + str(depth))
                        elif entry['type'] == 'WhileStatement': # if statement
                            js_vars.append('while statement' + ':' + str(depth))
                            logging.debug('while statement' + ':' + str(depth))
                        elif entry['type'] == 'AssignmentExpression': # assignment - "local_var = another_var"
                            js_vars.append(entry['left']['name'] + ':' + str(depth - 1))
                            logging.debug(entry['left']['name'] + ':' + str(depth - 1))
                        if not entry['type'] in ['IfStatement']:
                            parse_js(entry, js_vars, depth)


def get_scope(local_vars):
    scopes = local_vars.keys()
    return scopes[-1]


def find_parent(soup, parent_pk):
    # Find the immediate parent entity
    entity = soup.find('entity',attrs={"entityPK":parent_pk})

    # Keep looking until you get to the FilterCircuit for the JavaScript Filter
    while entity['type'] != 'FilterCircuit':
        parent_pk = entity['parent_pk']
        entity = soup.find('entity',attrs={"entityPK":parent_pk})
    return entity.find('fval',attrs={"name":"name"}).value.string


def get_primary_store(file_name):
    # Get the path to this script
    script_path = '/'.join(os.path.realpath(__file__).split('/')[:-1]) + '/'

    # Look in script directory if name not provided
    if not file_name:
        primary_store = glob.glob(script_path + 'PrimaryStore*.xml')
        print primary_store
        if len(primary_store) > 1:
            print "Multiple PrimaryStore XML files found in " + script_path
            return None
        file_name = primary_store[0]
    else:
        # Check file name format
        if not file_name.split('/')[-1].startswith('PrimaryStore') and not file_name.split('/')[-1].lower().endswith('.xml'):
            print "Primary store file name doesn't conform to Axway API Deployment Package standard name"
            return None

    # Look in script directory if no path provided
    if not '/' in file_name:
        file_name = script_path + file_name

    # Check if the file exists
    if not os.path.isfile(file_name):
        print "Primary Store with name '" + file_name + "' does not exist"
        return None

    # Return file name
    return file_name


if __name__ == "__main__":
    # Parse the input arguments
    options = parse_options(sys.argv[:])

    # Get the PrimaryStore file to parse
    primary_store = get_primary_store(options.primary_store)
    if not primary_store:
        exit(9)

    # Set logging level
    numeric_level = getattr(logging, options.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % options.loglevel)
    logging.basicConfig(level=numeric_level,format='%(levelname)s:%(message)s')

    # Disable charsetprober debug messages during XML parsing
    logging.getLogger('chardet.charsetprober').setLevel(logging.INFO)

    # Open PrimaryStore and parse the XML
    with open(primary_store) as primary_store:
        soup = bs4.BeautifulSoup(primary_store, 'xml')

    # Find all JavaScriptFilter entities
    js_filters = soup.find_all('entity',type='JavaScriptFilter')

    # Initialize variables
    parsed_filters = []

    # Process JavaScript Filters
    for js_filter in js_filters:
        # Initialze the parsed filter dictionary entity key
        parsed_filter = {"entityPK":js_filter['entityPK']}
        logging.debug('Entity Key: ' + parsed_filter['entityPK'])

        # Get the parent key
        parsed_filter['parent_pk'] = js_filter['parentPK']

        # Get filter name
        parsed_filter['name'] = js_filter.find('fval',attrs={"name":"name"}).value.string
        logging.debug('Filter name: ' + parsed_filter['name'])

        # Get the script type
        parsed_filter['script_type'] = js_filter.find('fval',attrs={"name":"engineName"}).value.string
        logging.debug('Engine name: ' + parsed_filter['name'])
        logging.debug('------------------------------------------------------')

        # Get the script
        parsed_filter['script'] = js_filter.find('fval',attrs={"name":"script"}).value.get_text()
        logging.debug(parsed_filter['script'])

        # Initialize empty list of JavaScript variables
        parsed_filter['js_vars'] = []

        # Initialize empty list of alerts
        parsed_filter['alerts'] = []

        # Parse the JavaScript
        p = PyJsParser()
        res = p.parse(parsed_filter['script'])
        #logging.critical(json.dumps(res,indent=4))
        parse_js(res, parsed_filter['js_vars'], -1)
        logging.debug(parsed_filter['js_vars'])

        # Check variables are declared as local
        local_vars = OrderedDict()
        local_vars["script:0"] = []
        for js_var in parsed_filter['js_vars']:
            this_depth = int(js_var.split(':')[1])
            scope = get_scope(local_vars)
            scope_depth = int(scope.split(':')[1])
            scope_name = scope.split(':')[0]
            logging.debug(js_var)
            if this_depth >= scope_depth:
                if this_depth == scope_depth and scope_name.split()[0] == 'function':
                    logging.debug('trigger: ' + js_var)
                    local_vars.popitem()
                    logging.debug(local_vars)
            else: # this_depth < scope_depth
                logging.debug('depth less: ' + js_var)
                popped_scope = local_vars.popitem()
                logging.debug(local_vars)

            if js_var.startswith('var '):
                local_vars[scope].append(js_var.split(':')[0].split()[1])
                logging.debug(local_vars)
            elif js_var.split()[0] == 'function':
                local_vars[js_var] = []
                logging.debug('new local_vars after push:')
                logging.debug(local_vars)
            elif js_var.split()[0] in ['if','dowhile','while','for']:
                continue
            else:
                found = False
                for s, v in local_vars.items():
                    if js_var.split(':')[0] in v:
                        found = True
                if not found:
                    logging.info('Possible Global variable "' + js_var.split(':')[0] + '" in ' + get_scope(local_vars).split(':')[0])
                    parsed_filter['alerts'].append(js_var.split(':')[0] + ':' + get_scope(local_vars).split(':')[0])
        parsed_filters.append(parsed_filter)
        logging.debug('=======================================================\n')

    # Report on issues with JavaScript filters
    alert = False
    for parsed_filter in parsed_filters:
        if parsed_filter['alerts'] or parsed_filter['script_type'] != options.engine_name:
            alert = True
            parent_filter = find_parent(soup, parsed_filter['parent_pk'])
            print "Filter '" + parsed_filter['name'] + "' in '" + parent_filter + "'"
            print '-------------------------------------------------------------------------------------'
            print parsed_filter['script']
            print
            for js_var in parsed_filter['alerts']:
                print 'Possible Global variable "' + js_var.split(':')[0] + '" in ' + js_var.split(':')[1]
            if parsed_filter['script_type'] != 'nashorn':
                print 'JavaScript engine is not nashorn'
            print '=====================================================================================\n'

    # Exit with appropriate return code
    if alert:
        exit(9)

    print "No issues found with JavaScript Filters in this PrimaryStore."
    exit(0)
