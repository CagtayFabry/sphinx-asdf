import os
import posixpath

import yaml

from docutils import nodes
from docutils.frontend import OptionParser

from sphinx import addnodes
from sphinx.parsers import RSTParser
from sphinx.util.fileutil import copy_asset
from sphinx.util.docutils import SphinxDirective, new_document

from .nodes import (add_asdf_nodes, schema_title, schema_description,
                    asdf_tree, asdf_tree_item)



class schema_def(nodes.comment):
    pass


class AsdfSchemas(SphinxDirective):

    required_arguments = 0
    optional_arguments = 0
    has_content = True

    def _process_asdf_toctree(self):

        links = []
        for name in self.content:
            if not name:
                continue
            schema = self.env.path2doc(name.strip() + '.rst')
            link = posixpath.join('generated', schema)
            links.append((schema, link))

        tocnode = addnodes.toctree()
        tocnode['includefiles'] = [x[1] for x in links]
        tocnode['entries'] = links
        tocnode['maxdepth'] = -1
        tocnode['glob'] = None

        paragraph = nodes.paragraph(text="Here's where the schemas go")
        return [paragraph, tocnode]


    def run(self):

        # This is the case when we are actually using Sphinx to generate
        # documentation
        if not getattr(self.env, 'autoasdf_generate', False):
            return self._process_asdf_toctree()

        # This case allows us to use docutils to parse input documents during
        # the 'builder-inited' phase so that we can determine which new
        # document need to be created by 'autogenerate_schema_docs'. This seems
        # much cleaner than writing a custom parser to extract the schema
        # information.
        return [schema_def(text=c.strip().split()[0]) for c in self.content]


class AsdfSchema(SphinxDirective):

    has_content = True

    def run(self):

        schema_name = self.content[0]
        schema_dir = self.state.document.settings.env.config.asdf_schema_path
        srcdir = self.state.document.settings.env.srcdir

        schema_file = posixpath.join(srcdir, schema_dir, schema_name) + '.yaml'

        with open(schema_file) as ff:
            content = yaml.safe_load(ff.read())

        title = schema_title(text=content.get('title', ''))

        docnodes = [title]

        description = content.get('description', '')
        if description:
            docnodes.append(schema_description(text=description))

        if 'properties' in content:
            docnodes.append(self._walk_tree(content['properties']))

        return docnodes


    def _walk_tree(self, tree):
        treenodes = asdf_tree()
        for key in tree:
            treenodes.append(asdf_tree_item(text=key))
            if isinstance(tree[key], dict):
                treenodes.append(self._walk_tree(tree[key]))

        return treenodes


def find_autoasdf_directives(env, filename):

    parser = RSTParser()
    settings = OptionParser(components=(RSTParser,)).get_default_values()
    settings.env = env
    document = new_document(filename, settings)

    with open(filename) as ff:
        parser.parse(ff.read(), document)

    return [x.children[0].astext() for x in document.traverse()
            if isinstance(x, schema_def)]


def find_autoschema_references(app, genfiles):

    # We set this environment variable to indicate that the AsdfSchemas
    # directive should be parsed as a simple list of schema references
    # rather than as the toctree that will be generated when the documentation
    # is actually built.
    app.env.autoasdf_generate = True

    schemas = set()
    for fn in genfiles:
        # Create documentation files based on contents of asdf-schema directives
        path = posixpath.join(app.env.srcdir, fn)
        app.env.temp_data['docname'] = app.env.path2doc(path)
        schemas = schemas.union(find_autoasdf_directives(app.env, path))

    # Unset this variable now that we're done.
    app.env.autoasdf_generate = False

    return list(schemas)


def create_schema_docs(app, schemas):

    output_dir = posixpath.join(app.srcdir, 'generated')
    os.makedirs(output_dir, exist_ok=True)

    for schema_name in schemas:
        doc_path = posixpath.join(output_dir, schema_name + '.rst')

        if posixpath.exists(doc_path):
            continue

        os.makedirs(posixpath.dirname(doc_path), exist_ok=True)

        with open(doc_path, 'w') as ff:
            ff.write(schema_name + '\n')
            ff.write('=' * len(schema_name) + '\n\n')
            ff.write('.. asdf-schema::\n\n')
            ff.write('    {}\n'.format(schema_name))


def autogenerate_schema_docs(app):

    env = app.env

    genfiles = [env.doc2path(x, base=None) for x in env.found_docs
                if posixpath.isfile(env.doc2path(x))]

    if not genfiles:
        return

    ext = list(app.config.source_suffix)
    genfiles = [genfile + (not genfile.endswith(tuple(ext)) and ext[0] or '')
                for genfile in genfiles]

    # Read all source documentation files and parse all asdf-schema directives
    schemas = find_autoschema_references(app, genfiles)
    # Create the documentation files that correspond to the schemas listed
    create_schema_docs(app, schemas)


def on_build_finished(app, exc):
    if exc is None:
        src = posixpath.join(posixpath.dirname(__file__), 'asdf_schema.css')
        dst = posixpath.join(app.outdir, '_static')
        copy_asset(src, dst)


def setup(app):

    # Describes a path relative to the sphinx source directory
    app.add_config_value('asdf_schema_path', 'schemas', 'env')
    app.add_directive('asdf-autoschemas', AsdfSchemas)
    app.add_directive('asdf-schema', AsdfSchema)

    add_asdf_nodes(app)

    app.add_css_file('asdf_schema.css')

    app.connect('builder-inited', autogenerate_schema_docs)
    app.connect('build-finished', on_build_finished)

    return dict(version='0.1')
