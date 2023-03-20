import html
from typing import List, Optional

import matplotlib.colors
import numpy

from sflkit.analysis.suggestion import Suggestion, Location


class ColorCode:
    """
    Inspired by SpectrumDebugger from https://www.debuggingbook.org/html/StatisticalDebugger.html
    """

    def __init__(self, results: List[Suggestion] = None):
        self._suspiciousness = dict()
        if results:
            for suggestion in results:
                for location in suggestion.lines:
                    if location in self._suspiciousness:
                        self._suspiciousness[location].append(suggestion.suspiciousness)
                    else:
                        self._suspiciousness[location] = [suggestion.suspiciousness]

    def suspiciousness(self, location: Location):
        if location in self._suspiciousness:
            return max(self._suspiciousness[location])

    def tooltip(self, location: Location) -> str:
        """
        Return a tooltip for the given event (default: percentage).
        To be overloaded in subclasses.
        """
        return self.percentage(location)

    def percentage(self, location: Location) -> str:
        """
        Return the suspiciousness for the given event as percentage string.
        """
        suspiciousness = self.suspiciousness(location)
        if suspiciousness is not None:
            return str(int(suspiciousness * 100)).rjust(3) + "%"
        else:
            return " " * len("100%")

    def color(self, location: Location) -> Optional[str]:
        """
        Return an HTML color for the given event.
        """
        suspiciousness = self.suspiciousness(location)
        if suspiciousness is None:
            return None
        red = numpy.array((255, 153, 153)) / 255
        yellow = numpy.array((255, 255, 153)) / 255
        green = numpy.array((179, 230, 179)) / 255
        if suspiciousness <= 0.5:
            result = 2 * (suspiciousness * yellow + (0.5 - suspiciousness) * green)
        else:
            result = 2 * ((1 - suspiciousness) * yellow + (suspiciousness - 0.5) * red)
        return matplotlib.colors.rgb2hex(result)

    def code(
        self,
        file,
        code,
        color: bool = False,
        suspiciousness: bool = False,
        line_numbers: bool = True,
    ) -> str:
        """
        Color code
        """

        out = ""

        for line_number, line in enumerate(code.split("\n"), start=1):
            line = html.escape(line)
            if line.strip() == "":
                line = "&nbsp;"
            location = Location(file, line_number)
            location_suspiciousness = self.suspiciousness(location)
            if location_suspiciousness is not None:
                tooltip = f"Line {line_number}: {self.tooltip(location)}"
            else:
                tooltip = f"Line {line_number}: not executed"

            if suspiciousness:
                line = self.percentage(location) + " " + line

            if line_numbers:
                line = str(line_number).rjust(4) + " " + line

            line_color = self.color(location)

            if color and line_color:
                line = f"""<pre style="background-color:{line_color}"
                title="{tooltip}">{line.rstrip()}</pre>"""
            else:
                line = f'<pre title="{tooltip}">{line}</pre>'

            out += line + "\n"

        return f"<div>{out}</div>"
