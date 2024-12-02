# 修改自 InquirerPy 的 inquirer.filepath，筛选后缀为 .pdf 或 .zip 的文件。
"""Module contains the class to create filepath prompt and filepath completer class."""
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Generator, Optional

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.completion.base import ThreadedCompleter

from InquirerPy.prompts.input import InputPrompt
from InquirerPy.utils import (
    InquirerPyDefault,
    InquirerPyKeybindings,
    InquirerPyMessage,
    InquirerPySessionResult,
    InquirerPyStyle,
    InquirerPyValidate,
)

if TYPE_CHECKING:
    from prompt_toolkit.input.base import Input
    from prompt_toolkit.output.base import Output

__all__ = ["FilePathPrompt", "FilePathCompleter"]


class FilePathCompleter(Completer):
    """An auto completion class which generates system filepath.

    See Also:
        :class:`~prompt_toolkit.completion.Completer`

    Args:
        only_directories: Only complete directories.
        only_files: Only complete files.
    """

    def __init__(self, only_directories: bool = False, only_files: bool = False):
        self._only_directories = only_directories
        self._only_files = only_files
        self._delimiter = "/" if os.name == "posix" else "\\"

    def get_completions(
        self, document, complete_event
    ) -> Generator[Completion, None, None]:
        """Get a list of valid system paths."""
        if document.text == "~":
            return

        validation = lambda file, doc_text: str(file).startswith(doc_text)

        if document.cursor_position == 0:
            dirname = Path.cwd()
            validation = lambda file, doc_text: True
        elif document.text.startswith("~"):
            dirname = Path(os.path.dirname(f"{Path.home()}{document.text[1:]}"))
            validation = lambda file, doc_text: str(file).startswith(
                f"{Path.home()}{doc_text[1:]}"
            )
        elif document.text.startswith(f".{self._delimiter}"):
            dirname = Path(os.path.dirname(document.text))
            validation = lambda file, doc_text: str(file).startswith(doc_text[2:])
        else:
            dirname = Path(os.path.dirname(document.text))

        for item in self._get_completion(document, dirname, validation):
            yield item

    def _get_completion(
        self, document, path, validation
    ) -> Generator[Completion, None, None]:
        if not path.is_dir():
            return

        # To prioritize .zip and .pdf files in the completion menu, collect the completions in two separate lists
        file_completions = []
        dir_completions = []

        for file in path.iterdir():
            if self._only_directories and not file.is_dir():
                continue
            if self._only_files and not file.is_file():
                continue
            if file.is_dir() or file.name.endswith(('.zip', '.pdf')):
                if validation(file, document.text):
                    file_name: str = file.name
                    display_name = file_name + (self._delimiter if file.is_dir() else "")
                    completion = Completion(
                        file.name,
                        start_position=-1 * len(os.path.basename(document.text)),
                        display=display_name,
                    )
                    if file.is_dir():
                        dir_completions.append(completion)
                    else:
                        file_completions.append(completion)

        for completion in file_completions:
            yield completion

        for completion in dir_completions:
            yield completion
