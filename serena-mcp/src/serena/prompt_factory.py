from serena.constants import PROMPT_TEMPLATES_DIR
from serena.generated.generated_prompt_factory import PromptFactory


class SerenaPromptFactory(PromptFactory):
    """
    A class for retrieving and rendering prompt templates and prompt lists.
    """

    def __init__(self) -> None:
        super().__init__(PROMPT_TEMPLATES_DIR)
