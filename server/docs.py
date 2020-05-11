import logging
import os
import re
from pathlib import Path

from flask import (Blueprint, Flask, Response, abort, current_app,
                   render_template, request, safe_join, send_file,
                   send_from_directory, url_for, redirect)
from jinja2 import TemplateNotFound
from werkzeug.exceptions import BadRequest, NotFound


def blueprint(paths, max_depth=-1):

    docs = Blueprint('docs', __name__, template_folder='templates')

    @docs.route('/')
    def overview():
        return render_template("docs_index.html", paths=paths)

    @docs.route('/tree/<doctype>/')
    def overview_doctype(doctype):
        if len(paths[doctype]) == 1:
            first_folder = list(paths[doctype])[0]
            return redirect(url_for('.show', doctype=doctype, folder=first_folder, path=''))
        return redirect(url_for('.overview'))

    @docs.route('/tree/<doctype>/<string:folder>/', defaults={'path': ''})
    @docs.route('/tree/<doctype>/<string:folder>/<path:path>/')
    def show(doctype, folder, path):
        if (not doctype in ['lib', 'test']) or len(paths[doctype]) == 0 or not folder in paths[doctype]:
            raise NotFound()

        base = url_for('.show', doctype=doctype, folder=folder, path='')
        breadcrumbs = make_breadcrumbs(doctype, folder, path)
        tree = make_tree(doctype, folder, path, max_depth)

        return render_template('docs_tree.html', breadcrumbs=breadcrumbs, base=base, tree=tree, paths=paths)

    @docs.route('/file/<doctype>/<string:folder>/<path:path>')
    def show_file(doctype, folder, path):
        if (not doctype in ['lib', 'test']) or len(paths[doctype]) == 0 or not folder in paths[doctype]:
            raise NotFound()

        breadcrumbs = make_breadcrumbs(doctype, folder, path, True)
        tree = make_tree(doctype, folder, path, max_depth)
        raw_url=url_for('.extract', doctype=doctype, folder=folder, path=path)

        return render_template('rf'+doctype+'_file.html', raw_url=raw_url, breadcrumbs=breadcrumbs, tree=tree, paths=paths)

    @docs.route('/raw/<doctype>/<folder>/<path:path>')
    def raw(doctype, folder, path):
        return send_from_directory(Path(paths[doctype][folder]['output']).absolute(), path)

    @docs.route('/extract/<doctype>/<folder>/<path:path>')
    def extract(doctype, folder, path):
        if (not doctype in ['lib', 'test']) or len(paths[doctype]) == 0 or not folder in paths[doctype]:
            raise NotFound()

        filename = safe_join(paths[doctype][folder]['output'], path)

        if not os.path.isabs(filename):
            filename = Path(filename).absolute()
        try:
            if not os.path.isfile(filename):
                raise NotFound()

            fullhtml = open(filename, 'r', encoding='utf-8')
            rfdoc_extract = re.search(
                "<script type=\"text/javascript\">\n("+doctype+"doc = .*)\n</script>", fullhtml.read(), re.IGNORECASE)

            if rfdoc_extract:
                return Response(rfdoc_extract.group(1), mimetype="text/javascript")

        except (TypeError, ValueError):
            raise BadRequest()
        raise BadRequest()

    def make_breadcrumbs(doctype, folder, path, last_is_file=False):
        breadcrumbs = [{'name': 'Docs %s' % folder, 'url': url_for('.show', doctype=doctype, folder=folder, path='')}]
        levels = path.split('/')
        if levels[0] != '':
            for i in range(len(levels)-1):
                breadcrumbs.append(
                    {'name': levels[i], 'url': url_for('.show', doctype=doctype, folder=folder, path='/'.join(levels[0:i+1]))})

            last_url_endpoint = '.show'
            if last_is_file:
                last_url_endpoint = '.show_file'
            breadcrumbs.append(
                {'name': levels[len(levels)-1], 'active': True, 'url': url_for(last_url_endpoint, doctype=doctype, folder=folder, path='/'.join(levels))})

        return breadcrumbs

    def make_tree(doctype, folder, path, max_depth=-1):
        tree = dict(doctype=doctype, folder=folder, name=os.path.basename(path), path=path, url=url_for('.show', doctype=doctype, folder=folder, path=path), children=[])
        try:
            ospath = os.path.join(paths[doctype][folder]['output'], path)
            lst = os.listdir(ospath)
        except OSError:
            pass  # ignore errors
        else:
            for name in lst:
                oschild = os.path.join(ospath, name)
                child = os.path.join(path, name)
                if os.path.isdir(oschild):
                    if max_depth != 0:
                        tree['children'].append(make_tree(doctype, folder, child, max_depth=max_depth-1))
                    else:
                        tree['children'].append(dict(doctype=doctype, folder=folder, name=name, path=child, url=url_for('.show', doctype=doctype, folder=folder, path=child)))
                else:
                    tree['children'].append(dict(doctype=doctype, folder=folder, name=name, path=child, url=url_for('.show_file', doctype=doctype, folder=folder, path=child)))
        tree['children'] = sorted(tree['children'], key=lambda x: x['name'])
        return tree

    return(docs)
