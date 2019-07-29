from pathlib import Path
from typing import List

from utils.snippet.panos import PanosSnippet
from .base import Skillet


class PanosSkillet(Skillet):

    def get_snippets(self) -> List[PanosSnippet]:
        snippet_path_str = self.skillet_dict['snippet_path']
        snippet_path = Path(snippet_path_str)
        snippet_list = list()
        for snippet_def in self.snippet_stack:
            snippet_file = snippet_path.joinpath(snippet_def['file'])
            if snippet_file.exists():
                with open(snippet_file, 'r') as sf:
                    snippet = PanosSnippet(sf.read(), snippet_def)
                    snippet_list.append(snippet)

        return snippet_list
