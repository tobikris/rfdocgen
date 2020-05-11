import errno
import logging
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path
from threading import Thread

from robot import libdoc, testdoc


def paths(path: Path, input_base: Path, docs_base: Path) -> (str, str, str, str):
    input_path = str(path)
    name = '/'.join(input_path.replace('%s/' % str(input_base), '').split('/'))
    docs_path = '%s.html' % (input_path.replace(
        str(input_base), str(docs_base)))
    docs_dir = Path(docs_path).parent
    docs_dir.mkdir(parents=True, exist_ok=True)
    version = "dev"
    return input_path, docs_path, name, version

def libs(pathlist, input_base: Path, docs_base: Path):
    for path in pathlist:
        input_path, docs_path, name, version = paths(path, input_base, docs_base)
        if is_input_newer(input_path, docs_path):
            logging.getLogger('rfdocgen').debug('lib: %s\n\t%s\n\t=> %s' % (name, input_path, docs_path))
            with redirect_stdout(None):
                libdoc.libdoc(input_path, docs_path, name=name, version=version)


def tests(pathlist, input_base: Path, docs_base: Path):
    for path in pathlist:
        input_path, docs_path, name, version = paths(path, input_base, docs_base)
        if is_input_newer(input_path, docs_path):
            logging.getLogger('rfdocgen').debug('tests: %s\n\t%s\n\t=> %s' % (name, input_path, docs_path))
            with redirect_stdout(None):
                testdoc.testdoc(input_path, docs_path, name=name, version=version)

def is_input_newer(input_path: str, docs_path: str) -> bool:
    if not Path(docs_path).exists():
        return True
    return os.stat(input_path).st_mtime > os.stat(docs_path).st_mtime

def remove_old(docs_base: str, input_base: str):
    logging.getLogger('rfdocgen').debug('remove_old(%s, %s)' % (docs_base, input_base))
    if Path(docs_base).is_dir():
        for path in Path(docs_base).rglob('*'):
            input_path = str(path).replace(docs_base, input_base).replace('.html', '')
            if not Path(input_path).exists():
                remove_old(str(path), str(path).replace(docs_base, input_base))
        if not Path(input_base).exists():
            try:
                Path(docs_base).rmdir()
            except OSError as ex:
                if ex.errno == errno.ENOTEMPTY:
                    logging.getLogger('rfdocgen').debug('not deleting dir %s, not empty' % (str(docs_base)))

    elif os.path.basename(docs_base).endswith('.html'):
        input_path = docs_base.replace(docs_base, input_base).replace('.html', '')
        logging.getLogger('rfdocgen').debug('removing file %s' % (docs_base))
        Path(docs_base).unlink()
    else:
        logging.getLogger('rfdocgen').debug('not deleting %s, not a dir or html-file - we probably did\'nt create it' % (str(docs_base)))

def doc_libs(docs_path: str, libs_path: str):
    def doc():
        logging.getLogger('rfdocgen').debug('executing doc_libs')
        libs(Path(libs_path).rglob('**/*.robot'), libs_path, docs_path)
        libs(Path(libs_path).rglob('**/*.py'), libs_path, docs_path)
        remove_old(docs_path, libs_path)

    return doc

def doc_tests(docs_path: str, testsuites_path: str):
    def doc():
        logging.getLogger('rfdocgen').debug('executing doc_tests')
        tests(Path(testsuites_path).rglob('**/*.robot'), testsuites_path, docs_path)
        remove_old(docs_path, testsuites_path)

    return doc
