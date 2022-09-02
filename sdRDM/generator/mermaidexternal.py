from typing import Optional, Dict
from functools import lru_cache


class MermaidExternal:
    def __init__(self, name: str, repo: str, commit: Optional[str] = None):
        self.name = name
        self.fname = name.lower()
        self.repo = repo
        self.commit = commit

    @lru_cache(maxsize=20)
    def get_cls_objs(self) -> Dict:
        """
        Renders a given external source of a data model to code.
        This method will fetch the data model and extract the relevant object.
        """

        from sdRDM.tools.gitutils import build_library_from_git_specs

        # Fetch the API from GitHub
        cls_defs = build_library_from_git_specs(
            url=self.repo, commit=self.commit, raw_files=True
        )

        return cls_defs
