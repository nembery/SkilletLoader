from xml.etree import ElementTree

from jinja2 import BaseLoader
from jinja2 import Environment
from passlib.hash import md5_crypt


class Snippet:
    """
    Snippet represents an XML blob along with some metadata such as xpath and required variables
    """

    def __init__(self, name, xpath, xmlstr):
        self.xpath = xpath
        self.xmlstr = xmlstr
        self.metadata = {}
        self.name = name

        self.rendered_xpath = ""
        self.rendered_xmlstr = ""

    def get_xpath(self):
        return self.xpath

    def set_metadata(self, metadata):
        self.metadata = metadata

    def template(self, context) -> tuple:
        if not context:
            context = {}
            variables = self.metadata['variables']
            for snippet_var in variables:
                context[snippet_var['name']] = snippet_var['default']

        e = Environment(loader=BaseLoader)
        e.filters["md5_hash"] = self.md5_hash

        t = e.from_string(self.xpath)
        self.rendered_xpath = t.render(context)

        t = e.from_string(self.xmlstr)
        self.rendered_xmlstr = t.render(context)

        return self.rendered_xpath, self.rendered_xmlstr

    def copy(self):
        s = Snippet(self.xpath, self.xmlstr)
        s.rendered_xmlstr = self.rendered_xmlstr
        s.rendered_xpath = self.rendered_xpath
        return s

    def select_entry(self, name):
        if not name:
            return
        snippet_string = "<root>" + self.rendered_xmlstr + "</root>"
        root = ElementTree.fromstring(snippet_string)
        elems = root.find("./entry[@name='{}']".format(name))

        if not elems:
            print("Entry with name {} not found in {}!".format(name, self.name))
            exit(1)
        xmlstr = ElementTree.tostring(elems)
        xmlstr = xmlstr.decode("utf-8")
        self.rendered_xmlstr = xmlstr

    def print_entries(self):
        snippet_string = "<root>" + self.xmlstr + "</root>"
        root = ElementTree.fromstring(snippet_string)
        elems = root.findall("./entry")

        if not elems:
            return

        for e in elems:
            print("      " + e.attrib["name"])

    # define functions for custom jinja filters
    def md5_hash(txt):
        '''
        Returns the MD5 Hashed secret for use as a password hash in the PanOS configuration
        :param txt: text to be hashed
        :return: password hash of the string with salt and configuration information. Suitable to place in the phash field
        in the configurations
        '''

        return md5_crypt.hash(txt)
