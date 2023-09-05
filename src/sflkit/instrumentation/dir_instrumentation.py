import os
import queue
import re
import shutil
from typing import List, Optional, Iterable, Tuple

from sflkit.instrumentation import Instrumentation
from sflkit.instrumentation.file_instrumentation import FileInstrumentation
from sflkit.language.visitor import ASTVisitor
from sflkit.logger import LOGGER


class DirInstrumentation(Instrumentation):
    def __init__(self, visitor: ASTVisitor):
        super().__init__(visitor)
        self.file_instrumentation = FileInstrumentation(visitor)

    @staticmethod
    def check_included(element: str, includes: Optional[Iterable[str]]):
        return not includes or any(re.match(include, element) for include in includes)

    def handle_element(
        self,
        element: str,
        file_queue: queue.Queue[Tuple[str, bool]],
        src: os.PathLike,
        dst: os.PathLike,
        suffixes: List[str],
        check: bool,
    ):
        if os.path.isdir(os.path.join(src, element)):
            LOGGER.debug(f"I found a subdir at {element}.")
            os.makedirs(os.path.join(dst, element), exist_ok=True)
            for f in os.listdir(os.path.join(src, element)):
                file_queue.put((os.path.join(element, f), check))
        elif (
            not check
            and any(element.endswith(f".{suffix}") for suffix in suffixes)
            and not os.path.islink(os.path.join(src, element))
        ):
            LOGGER.debug(f"I found a file I can instrument at {element}.")
            self.file_instrumentation.instrument(
                os.path.join(src, element),
                os.path.join(dst, element),
                file=element,
            )
        else:
            LOGGER.debug(f"I found a file I will not instrument at {element}.")
            shutil.copy(
                os.path.join(src, element),
                os.path.join(dst, element),
                follow_symlinks=False,
            )

    def instrument(
        self,
        src: os.PathLike,
        dst: os.PathLike,
        suffixes: List[str] = None,
        file: str = "",
        includes: Optional[Iterable[str]] = None,
        excludes: Optional[Iterable[str]] = None,
    ):
        if suffixes is None:
            raise ValueError("DirInstrumentation requires suffixes")
        if excludes is None:
            excludes = list()
        if not os.path.exists(src):
            raise ValueError(f"Path {src} does not exist")
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        if os.path.isfile(src):
            LOGGER.debug(f"I found a file I can instrument at {src}.")
            self.file_instrumentation.instrument(
                src, dst, suffixes=suffixes, file=os.path.split(src)[-1]
            )
        else:
            os.makedirs(dst, exist_ok=True)
            file_queue = queue.Queue()
            file_queue.put(("", True))
            while not file_queue.empty():
                element, check = file_queue.get()
                if check and self.check_included(element, includes):
                    self.handle_element(element, file_queue, src, dst, suffixes, False)
                elif element != "" and any(
                    re.match(exclude, element) for exclude in excludes
                ):
                    if os.path.isdir(os.path.join(src, element)):
                        shutil.copytree(
                            os.path.join(src, element),
                            os.path.join(dst, element),
                            symlinks=True,
                        )
                    else:
                        shutil.copy(
                            os.path.join(src, element),
                            os.path.join(dst, element),
                            follow_symlinks=False,
                        )
                    continue
                else:
                    self.handle_element(element, file_queue, src, dst, suffixes, check)
            self.events = self.file_instrumentation.events
        LOGGER.info(f"I found {len(self.events)} events in {src}.")
