import posixpath

from docutils import nodes
from docutils.frontend import OptionParser

from sphinx import addnodes
from sphinx.parsers import RSTParser
from sphinx.util.docutils import SphinxDirective, new_document


class schema_def(nodes.comment):
    pass


class AsdfSchemas(SphinxDirective):

    required_arguments = 0
    optional_arguments = 0
    has_content = True

    def _process_asdf_toctree(self):

        dirname = posixpath.dirname(self.env.docname)
        schema_path = self.state.document.settings.env.config.asdf_schema_path

        schemas = [x.strip().split()[0] for x in self.content]

        source_path = posixpath.join(dirname, 'hello')

        tocnode = addnodes.toctree()
        tocnode['includefiles'] = [source_path]
        tocnode['entries'] = [(name, source_path) for name in schemas]
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


def find_autoasdf_directives(env, filename):

    parser = RSTParser()
    settings = OptionParser(components=(RSTParser,)).get_default_values()
    settings.env = env
    document = new_document(filename, settings)

    with open(filename) as ff:
        parser.parse(ff.read(), document)

    return [x.children[0].astext() for x in document.traverse()
            if isinstance(x, schema_def)]


def autogenerate_schema_docs(app):

    # Read all source files

    # Look for all 'asdf-schema' directives and parse arguments

    # 

    env = app.env
    env.autoasdf_generate = True

    schema_path = env.config.asdf_schema_path
    schema_path = posixpath.join(env.srcdir, schema_path)

    genfiles = [env.doc2path(x, base=None) for x in env.found_docs
                if posixpath.isfile(env.doc2path(x))]

    if not genfiles:
        return

    ext = list(app.config.source_suffix)
    genfiles = [genfile + (not genfile.endswith(tuple(ext)) and ext[0] or '')
                for genfile in genfiles]

    schemas = set()
    for fn in genfiles:
        # Look for asdf-schema directive
        # Create documentation files based on contents of such directives
        path = posixpath.join(env.srcdir, fn)
        app.env.temp_data['docname'] = env.path2doc(path)
        schemas = schemas.union(find_autoasdf_directives(app.env, path))

    with open(posixpath.join(app.srcdir, 'schemas', 'hello.rst'), 'w') as ff:
        ff.write('MY TITLE\n')
        ff.write('========\n')
        ff.write('HEY THERE\n')

    env.autoasdf_generate = False


def setup(app):

    # Describes a path relative to the sphinx source directory
    app.add_config_value('asdf_schema_path', 'schemas', 'env')
    app.add_directive('asdf-schemas', AsdfSchemas)

    app.connect('builder-inited', autogenerate_schema_docs)

    return dict(version='0.1')
