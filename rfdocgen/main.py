import argparse
import logging
import os
import re
import sys
from pathlib import Path

import livereload
import tornado.log as tornado
from flask import Flask, render_template, request, send_from_directory, redirect, url_for

from .create_docs import doc_libs, doc_tests
from .server import docs

def split_input_conf(type: str, parameter: str, conf: str) -> (str, dict):
    sconf = conf.split(':')
    if len(sconf) != 3:
        raise ValueError('error, %s expects 3 parameters in the format "%s name:robot/path:docs/path", got %s' % (parameter, parameter, conf))

    if not re.match(r"[A-Za-z0-9-_.]+$", sconf[0]):
        raise ValueError('error, %s expects first parameter to be a name (A-Z, a-z, 0-9, -, _, .)", got %s' % (parameter, sconf[0]))

    input_path = sconf[1]
    if input_path != '-':
        input_path = str(Path(input_path).absolute())
    return sconf[0], dict(folder=sconf[0], input=input_path, output=str(Path(sconf[2]).absolute()))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Generate Docs for Robot Framework libraries and testsuites.')
    inputs = parser.add_argument_group('inputs', 'at least one is needed')
    inputs.add_argument('-l', '--lib', dest='libs', metavar='name:robot/:docs/', action='append', type=str, help='lib to document')
    inputs.add_argument('-t', '--test', dest='tests', metavar='name:robot/:docs/', action='append', type=str, help='test to document')

    server = parser.add_argument_group('server')
    server.add_argument('-s', '--server', dest='server', action='store_true', help='webserver for accessing the docs')
    server.add_argument('-i', '--host', dest='host', metavar='host', type=str, help='host to listen on (default: 127.0.0.1)', default='127.0.0.1')
    server.add_argument('-p', '--port', dest='port', metavar='port', type=int, help='port to listen on (default: 5000)', default='5000')

    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--max-depth', dest='max_depth', metavar='INT', type=int, help='how deep the file tree should be shown, infinite if not set', default=-1)
    args = parser.parse_args()
    if not (args.libs or args.tests):
        parser.error('No action requested, add --libs or --testsuites or both')

    paths = {'lib': {}, 'test': {}}
    if args.libs:
        for l in args.libs:
            name, conf = split_input_conf('lib', '-l', l)
            paths['lib'][name] = conf

    if args.tests:
        for t in args.tests:
            name, conf = split_input_conf('test', '-t', t)
            paths['test'][name] = conf

    print(args)
    print(paths)

    class CodeChangeReloadFilter(logging.Filter):
        def filter(self, record: logging.LogRecord):
            if record.getMessage().find('_reload_on_update') > 0:
                logging.getLogger('rfdocgen').error('error while reloading')
                sys.exit()
                return False
            return True
    logging.getLogger('tornado.application').addFilter(
        CodeChangeReloadFilter())

    logger = logging.getLogger('rfdocgen')
    log_stream = logging.StreamHandler(sys.stdout)
    log_stream.setFormatter(tornado.LogFormatter())
    logger.addHandler(log_stream)
    if args.debug:
        logger.setLevel(logging.DEBUG)

    if paths['lib']:
        for l in paths['lib']:
            if paths['lib'][l]['input'] != '-':
                doc_libs(paths['lib'][l]['output'], paths['lib'][l]['input'])()

    if paths['test']:
        for t in paths['test']:
            if paths['test'][t]['input'] != '-':
                doc_tests(paths['test'][t]['output'], paths['test'][t]['input'])()

    if args.server:
        app = Flask(__name__, static_folder=Path(
            __file__).parent.joinpath('server/static').absolute())
        app.config.update(DEBUG=True)

        app.register_blueprint(docs.blueprint(paths, max_depth=args.max_depth), url_prefix='/docs')

        @app.route('/')
        def index():
            return redirect(url_for('docs.overview'))

        server = livereload.Server(app.wsgi_app)

        if paths['lib']:
            for l in paths['lib']:
                if paths['lib'][l]['input'] != '-':
                    logger.debug('watching %s' % l)
                    server.watch(paths['lib'][l]['input'], doc_libs(paths['lib'][l]['output'], paths['lib'][l]['input']))

        if paths['test']:
            for t in paths['test']:
                if paths['test'][t]['input'] != '-':
                    logger.debug('watching %s' % t)
                    server.watch(paths['test'][t]['input'], doc_tests(paths['test'][t]['output'], paths['test'][t]['input']))

        server.serve(host=args.host, port=args.port)
