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
    required_metadata = {'name', 'xpath'}

    def __init__(self, metadata: dict):
        if 'cmd' not in metadata:
            self.cmd = 'set'
            self.element = metadata['element']
        else:
            self.cmd = metadata['cmd']
            self.element = ''

        super().__init__(self.element, metadata)
        self.xpath = self.metadata['xpath']

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

        raise SkilletLoaderException('Invalid metadata configuration')

    def render_metadata(self, context: dict) -> dict:
        """
        Renders each metadata value using the provided context
        :param context: dict containing key value pairs to
        :return:
        """
        meta = dict()
        meta['cmd'] = self.cmd

        for attr in self.metadata:
            if attr != 'cmd' or attr != 'file' or attr != 'when':
                meta[attr] = self.render(self.metadata[attr], context)

        return meta
