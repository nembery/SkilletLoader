# Copyright (c) 2018, Palo Alto Networks
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Authors: Adam Baumeister, Nathan Embery


from utils.exceptions import SkilletLoaderException
from .base import Snippet


class PanosSnippet(Snippet):
    required_metadata = {'name'}

    def __init__(self, metadata: dict):
        if 'cmd' not in metadata:
            self.cmd = 'set'
            # ensure xpath is present when cmd == set
            self.required_metadata = {'name', 'xpath'}
        elif metadata['cmd'] == 'op':
            self.cmd = metadata['cmd']
            self.required_metadata = {'name', 'cmd_str'}
        else:
            self.cmd = metadata['cmd']

        # element should be the 'file' attribute read in as a str
        self.element = metadata.get('element', '')
        super().__init__(self.element, metadata)

    def sanitize_metadata(self, metadata: dict) -> dict:
        """
        Ensure all required keys are present in the snippet definition
        :param metadata: dict
        :return: bool
        """
        if self.cmd in ('set', 'edit', 'override'):
            if {'xpath', 'file', 'element'}.issubset(metadata):
                return metadata
        elif self.cmd == 'move':
            if 'where' in metadata:
                return metadata
        elif self.cmd in ('rename', 'clone'):
            if 'new_name' in metadata or 'newname' in metadata:
                return metadata
        elif self.cmd == 'clone':
            if 'xpath_from' in metadata:
                return metadata
        elif self.cmd == 'op':
            if 'cmd_str' in metadata:
                return metadata

        raise SkilletLoaderException('Invalid metadata configuration')

    def render_metadata(self, context: dict) -> dict:
        """
        Renders each metadata value using the provided context
        Currently only renders the xpath attribute - this may render others in the future
        :param context: dict containing key value pairs to
        :return: dict containing the snippet definition metadata with the attribute values rendered accordingly
        """
        meta = self.metadata
        if 'xpath' in self.metadata:
            try:
                meta['xpath'] = self.render(self.metadata['xpath'], context)
            except TypeError as te:
                print(f'Could not render xpath attribute')

        return meta
