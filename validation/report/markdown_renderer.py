import os
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader

class MarkdownRenderer:
    """
    Jinja2 template renderer that merges data dictionary with markdown templates.
    """
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renders a Jinja2 template with the given context.
        """
        template = self.env.get_template(template_name)
        return template.render(context)
