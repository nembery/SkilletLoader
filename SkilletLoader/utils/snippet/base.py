from jinja2 import BaseLoader
from jinja2 import Environment
from passlib.hash import md5_crypt

from utils.exceptions import SkilletLoaderException


class Snippet:
    """
    BaseSnippet implements a basic template object snippet
    """
    required_metadata = {'name', 'file'}

    def __init__(self, template_str, metadata):

        self.metadata = self.sanitize_metadata(metadata)

        self.name = self.metadata['name']
        self.template_str = template_str
        self.rendered_template = ""

    def template(self, context) -> str:
        return self.render(self.template_str, context)

    def render(self, template_str, context) -> str:

        if not context:
            context = {}

        e = Environment(loader=BaseLoader)
        e.filters["md5_hash"] = self.md5_hash

        t = e.from_string(template_str)
        return t.render(context)

    def sanitize_metadata(self, metadata):
        """
        Ensure the configured metadata is valid for this snippet type
        :param metadata: dict
        :return: validated metadata dict
        """
        if not self.required_metadata.issubset(metadata):
            raise SkilletLoaderException('Invalid metadata configuration')

        return metadata

    # define functions for custom jinja filters
    @staticmethod
    def md5_hash(txt):
        """
        Returns the MD5 Hashed secret for use as a password hash in the PAN-OS configuration
        :param txt: text to be hashed
        :return: password hash of the string with salt and configuration information. Suitable to place in the phash field
        in the configurations
        """

        return md5_crypt.hash(txt)
