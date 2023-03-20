import atexit
import logging
import os
import queue
import re
import shutil
from typing import List

from sflkit.instrumentation import lib, Instrumentation
from sflkit.instrumentation.file_instrumentation import FileInstrumentation
from sflkit.language.visitor import ASTVisitor

atexit.unregister(lib.dump_events)


class DirInstrumentation(Instrumentation):
    def __init__(self, visitor: ASTVisitor):
        super().__init__(visitor)
        self.file_instrumentation = FileInstrumentation(visitor)

    def instrument(
        self,
        src: str,
        dst: str,
        suffixes: List[str] = None,
        file: str = "",
        excludes: list = None,
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
            logging.debug(f"I found a file I can instrument at {src}.")
            self.file_instrumentation.instrument(
                src, dst, suffixes=suffixes, file=os.path.split(src)[-1]
            )
        else:
            os.makedirs(dst, exist_ok=True)
            file_queue = queue.Queue()
            file_queue.put("")
            while not file_queue.empty():
                element = file_queue.get()
                if any(re.match(exclude, element) for exclude in excludes):
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
                if os.path.isdir(os.path.join(src, element)):
                    logging.debug(f"I found a subdir at {element}.")
                    os.makedirs(os.path.join(dst, element), exist_ok=True)
                    for f in os.listdir(os.path.join(src, element)):
                        file_queue.put(os.path.join(element, f))
                elif any(
                    element.endswith(f".{suffix}") for suffix in suffixes
                ) and not os.path.islink(os.path.join(src, element)):
                    logging.debug(f"I found a file I can instrument at {element}.")
                    self.file_instrumentation.instrument(
                        os.path.join(src, element),
                        os.path.join(dst, element),
                        file=element,
                    )
                else:
                    logging.debug(f"I found a file I will not instrument at {element}.")
                    shutil.copy(
                        os.path.join(src, element),
                        os.path.join(dst, element),
                        follow_symlinks=False,
                    )
            self.events = self.file_instrumentation.events
        logging.info(f"I found {len(self.events)} events in {src}.")
