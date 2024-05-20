import textwrap
import time

from cartopy.mpl.geoaxes import GeoAxes
from cartopy.mpl.gridliner import Gridliner
from cartopy.mpl.feature_artist import FeatureArtist
from matplotlib.axes import Axes


class Utilities:
    """Collection of useful methods to use in the 'GDACS Near-Real-Time NATURAL DISASTERS VISUALIZER' project."""

    @staticmethod
    def remove_features(ax: GeoAxes) -> None:
        """
        Remove features and gridlines from a Cartopy GeoAxes.

        :param ax: Cartopy GeoAxes
        """
        [child.remove() for child in ax.findobj(FeatureArtist)]
        [child.remove() for child in ax.findobj(Gridliner)]

    @staticmethod
    def format_axis(ax: Axes, modecolor: str, sides: str = "tblr") -> None:
        """
        Format axes by removing ticks and labels and/or sides and customizing the remaining sides.
        Mainly intended to create a frame around an axes.

        :param ax: matplotlib Axes
        :param modecolor: sides color
        :param sides: choose sides to be shown: top (t), bottom (b), left (l), right (r)

        """
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels("")
        ax.set_yticklabels("")
        for spine in ax.spines.values():
            spine.set_linewidth(1)
            spine.set_edgecolor(modecolor)
        if not "t" in sides:
            ax.spines.top.set_visible(False)
        if not "b" in sides:
            ax.spines.bottom.set_visible(False)
        if not "l" in sides:
            ax.spines.left.set_visible(False)
        if not "r" in sides:
            ax.spines.right.set_visible(False)

    @staticmethod
    def get_alert_color(alert: str) -> str:
        """
        Get the color of the the GDACS alert level.

        :param alert: GDACS alert level
        :return: HEX color
        """
        if alert == "Green":
            alert_color = "#008700"
        elif alert == "Orange":
            alert_color = "#d78700"
        elif alert == "Red":
            alert_color = "#ff0000"
        else:
            alert_color = "violet"
        return alert_color

    @staticmethod
    def wrap_text(text: str, max_width: int) -> str:
        """
        Wrap the given text to fit within the specified maximum width.

        :param text: text you want to wrap
        :param max_width: maximum width of text
        :return: wrapped text
        """
        if not (isinstance(text, str) and isinstance(max_width, int)):
            raise TypeError("text must be str, max_width must be int")
        wrapper = textwrap.TextWrapper(width=max_width)
        wrapped_lines = wrapper.wrap(text)
        return "\n".join(wrapped_lines)


class Timer:
    """Timer object with start/stop methods (tic/tac)."""

    def __init__(self):
        """Create a timer object."""
        self._ts = 0

    def tic(self):
        """Start the timer."""
        self._ts = time.perf_counter()

    def toc(self):
        """Stop the timer and print the elapsed time."""
        print(f"Time elapsed: {time.perf_counter()-self._ts:0.4f}s")
