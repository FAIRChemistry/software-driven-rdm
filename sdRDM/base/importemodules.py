from typing import Dict, Optional


class ImportedModules:
    """Empty class used to store all sub classes"""

    def __init__(self, classes, enums=None, links: Optional[Dict] = None):
        for name, node in classes.items():
            if hasattr(node, "cls"):
                # Add all classes
                setattr(self, name, node.cls)
            elif hasattr(node, "__fields__"):
                # Add classes that are not presented as a node
                setattr(self, name, node)
            elif isinstance(node, dict):
                # Add links if given
                setattr(self, name, node)

        if enums:
            self.enums = self.__class__(classes=enums)

        # Process links
        self.links = links
        self._distribute_links()

    def _distribute_links(self):
        """Adds the given links as instance methods"""

        if self.links is None:
            return

        for name, link in self.links.items():
            obj = getattr(self, link["__model__"])
            converter = lambda self: self.convert_to(template=link)[0]
            setattr(obj, f"to_{name.replace(' ', '_')}", converter)
