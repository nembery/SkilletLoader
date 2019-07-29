from .base import Snippet


class PanosSnippet(Snippet):

    required_metadata = {'name', 'xpath', 'file'}

    def __init__(self, template_str, metadata):
        super().__init__(template_str, metadata)
        self.xpath = self.metadata['xpath']

