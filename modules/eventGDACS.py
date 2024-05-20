import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import webbrowser
import numpy as np

import rich
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.text import Text

import matplotlib as mpl
from matplotlib.markers import MarkerStyle
from matplotlib import gridspec
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patheffects as fx

import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfea

from modules.geocode import Geocode
from modules.utilities import Utilities


class Event:
    CATEGORIES = {
        "TC": "Tropical Cyclone",
        "EQ": "Earthquake",
        "FL": "Flood",
        "VO": "Volcano",
        "WF": "Wildfire",
        "DR": "Drought",
        "NA": "eventCategory",
    }

    DEFAULT_EVENT = {
        "evid": "0000000",
        "title": "eventTitle",
        "description": "eventDescription: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque vel nisl a nisi accumsan fringilla non cursus neque. Duis luctus.",
        "category": "NA",
        "alert": "alertLevel",
        "severity": "eventSeverity",
        "population": 0,
        "date": "Mon, 1 Jan 1900",
        "coords": (0, 0),
        "country": ["United Nations"],
        "iso2": "UN",
        "link": "https://www.gdacs.org/",
    }

    def __init__(
        self,
        evid=None,
        title=None,
        description=None,
        category=None,
        alert=None,
        severity=None,
        population=None,
        date=None,
        coords=None,
        country=None,
        iso2=None,
        link=None,
    ):
        self.evid = evid if evid is not None else self.DEFAULT_EVENT["evid"]
        self.title = title if title is not None else self.DEFAULT_EVENT["title"]
        self.description = (
            description
            if description is not None
            else self.DEFAULT_EVENT["description"]
        )
        self.category = (
            category if category is not None else self.DEFAULT_EVENT["category"]
        )
        self.alert = alert if alert is not None else self.DEFAULT_EVENT["alert"]
        self.severity = (
            severity if severity is not None else self.DEFAULT_EVENT["severity"]
        )
        self.population = (
            population if population is not None else self.DEFAULT_EVENT["population"]
        )
        self.date = date if date is not None else self.DEFAULT_EVENT["date"]
        self.coords = coords if coords is not None else self.DEFAULT_EVENT["coords"]
        self.country = country if country is not None else self.DEFAULT_EVENT["country"]
        self.iso2 = iso2 if iso2 is not None else self.DEFAULT_EVENT["iso2"]
        self.link = link if link is not None else self.DEFAULT_EVENT["link"]

    def __str__(self):
        return (
            f"Event ID: {self.evid}\n"
            f"Title: {self.title}\n"
            f"Category: {self.CATEGORIES[self.category]}\n"
            f"Date: {self.date}\n"
            f"Coordinates: {self.coords}\n"
            f"Country: {', '.join(self.country) if len(self.country) > 1 else self.country[0]}"
        )

    @property
    def evid(self):
        return self._evid

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description

    @property
    def category(self):
        return self._category

    @property
    def alert(self):
        return self._alert

    @property
    def severity(self):
        return self._severity

    @property
    def population(self):
        return self._population

    @property
    def date(self):
        return self._date

    @property
    def coords(self):
        return self._coords

    @property
    def country(self):
        return self._country

    @property
    def iso2(self):
        return self._iso2

    @property
    def link(self):
        return self._link

    @evid.setter
    def evid(self, e):
        self._evid = e

    @title.setter
    def title(self, t):
        self._title = t

    @description.setter
    def description(self, d):
        self._description = d

    @category.setter
    def category(self, c):
        if c in self.CATEGORIES:
            self._category = c
        else:
            raise ValueError("Not a valid category.")

    @alert.setter
    def alert(self, a):
        self._alert = a

    @severity.setter
    def severity(self, s):
        self._severity = s

    @population.setter
    def population(self, p):
        self._population = p

    @date.setter
    def date(self, d):
        self._date = d

    @coords.setter
    def coords(self, crds):
        self._coords = crds

    @country.setter
    def country(self, ctry):
        self._country = ctry

    @iso2.setter
    def iso2(self, i):
        self._iso2 = i

    @link.setter
    def link(self, l):
        self._link = l

    @classmethod
    def get_categories(cls):
        return cls.CATEGORIES


class EventContainer:
    GDACS_URL = "https://www.gdacs.org/xml/rss_7d.xml"
    NS = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "geo": "http://www.w3.org/2003/01/geo/wgs84_pos#",
        "gdacs": "http://www.gdacs.org",
        "glide": "http://glidenumber.net",
        "georss": "http://www.georss.org/georss",
        "atom": "http://www.w3.org/2005/Atom",
    }

    def __init__(self, events=None):
        self._events = events if events is not None else []

    def __getitem__(self, index):
        if isinstance(index, slice):
            tempcontainer = EventContainer()
            tempcontainer._events = self.events[index]
            return tempcontainer
        else:
            return self.events[index]

    def __len__(self):
        return len(self.events)

    def __iter__(self):
        return iter(self.events)

    @property
    def events(self):
        return self._events

    # --------- FETCH EVENTS ---------#
    def request(self):
        """Request events from GDACS official RSS feed"""
        try:
            event_response = requests.get(self.GDACS_URL)
            root = ET.fromstring(event_response.content)
            items = root.findall(".//item")
            for item in items:
                event = self._parse_event(item)
                self._events.append(event)
            self._events.sort(
                key=lambda event: datetime.strptime(event.date, "%a, %d %b %Y"),
                reverse=True,
            )
        except (requests.RequestException, ET.ParseError) as e:
            print(f"An error occurred while fetching events: {e}")
            self._events.append(Event())

    # --------- PANEL VIEW ---------#
    def panel(self):
        if not self.events:
            print("No events to display.")
            return
        console = Console()
        user_renderables = [
            Panel(self._get_panel_content(event), expand=True) for event in self.events
        ]
        panel = Panel(
            Columns(user_renderables, align="center", expand=True),
            title="[bold]Summary of events[/bold]",
            border_style="dim",
        )
        console.print(panel, justify="center")

    # --------- UTILITIES ---------#
    def _parse_event(self, item):
        """Parse an Event from a XML item"""
        evid = int(item.find("gdacs:eventid", self.NS).text)
        title = item.find("title").text
        description = item.find("description").text
        category = item.find("gdacs:eventtype", self.NS).text
        alert = item.find("gdacs:alertlevel", self.NS).text
        severity = item.find("gdacs:severity", self.NS).text
        population = int(item.find("gdacs:population", self.NS).attrib["value"])
        date = item.find("gdacs:todate", self.NS).text
        date = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")
        date = date.date().strftime("%a, %d %b %Y")
        coords = (
            float(item.find("geo:Point/geo:lat", self.NS).text),
            float(item.find("geo:Point/geo:long", self.NS).text),
        )
        coords = (round(coords[0], 5), round(coords[1], 5))
        country = item.find("gdacs:country", self.NS).text
        if country == None:
            country = ["Off-shore"]
            iso2 = "UN"
        else:
            country = [c.strip() for c in country.split(",")]
            iso2 = Geocode.format_code(
                item.find("gdacs:iso3", self.NS).text, toformat="alpha2"
            )
        link = item.find("link").text
        return Event(
            evid,
            title,
            description,
            category,
            alert,
            severity,
            population,
            date,
            coords,
            country,
            iso2,
            link,
        )

    def _get_panel_content(self, event):
        """Extract text info from a given event"""
        cat = Event.CATEGORIES[event.category]
        color = Utilities.get_alert_color(event.alert)
        return f"[b][{color}]{cat}[/{color}][/b]\n{event.country[0]}\n{event.date}"


class EventViewer:
    def __init__(self, events=[Event()], appearance="light"):
        # Matplotlib preferences
        mpl.use("Qt5Agg")  # A better backend for my purposes
        mpl.rcParams["toolbar"] = "None"

        # Viewer attributes
        self.events = events
        self.appearance = appearance
        if self.appearance == "light":
            self.uicolors = ("white", "black")
        elif self.appearance == "dark":
            self.uicolors = ("#2C2C28", "white")
        self.current_index = 0
        self.figure = self._setup()

    @property
    def current_index(self):
        return self._current_index

    @property
    def current_event(self):
        return self.events[self._current_index]

    @current_index.setter
    def current_index(self, value):
        self._current_index = value % len(self.events)

    def _setup(self):
        # Create the figure and the layout of subplots
        figratio = 2/3
        figwidth = 14
        fig = plt.figure(figsize=(figwidth, figratio*figwidth),
                         num=f"EventViewer ({self.current_index+1}/{len(self.events)})",
                         facecolor=self.uicolors[0]
                         )
        spec = gridspec.GridSpec(ncols=2, nrows=2,
                         width_ratios=[2, 1], wspace=0.5,
                         hspace=0.1, height_ratios=[3, 2]
                         )

        # Add the axes (ax_map is a GeoAxes axis)
        proj = ccrs.NearsidePerspective(0, 0)
        ax_map = fig.add_subplot(spec[:, 0], facecolor=self.uicolors[0], projection=proj, label="ax_map")
        ax_info = fig.add_subplot(spec[0, 1], label="ax_info")
        subspec = spec[1, 1].subgridspec(nrows=2, ncols=1, height_ratios=[4, 1])
        ax_flag = fig.add_subplot(subspec[0], label="ax_flag")
        ax_sources = fig.add_subplot(subspec[1], label="ax_sources")

        # Populate the axes
        self.plot_map(ax_map)
        self.plot_info(ax_info)
        self.plot_flag(ax_flag)
        self.plot_sources(ax_sources)

        # Show current_event's ID
        ax_id = fig.add_axes([0.1, 0.1, 0.1, 0.1], label="ax_id")
        ax_id.set_axis_off()
        ax_id.text(0, 0,
                   f"{self.current_event.category} {self.current_event.evid}",
                   fontsize="medium",
                   color=self.uicolors[1]
                   )

        # Return the figure
        return fig


    #--------- PLOTTERS ---------#
    def plot_map(self, ax):
        # Cartopy map
        proj = ccrs.NearsidePerspective(self.current_event.coords[1], self.current_event.coords[0])
        ax.projection = proj
        ax.set_global()
        ax.coastlines(resolution="50m", color=self.uicolors[1])
        ax.add_feature(cfea.BORDERS, edgecolor="grey", alpha=0.5, linewidth=0.4, visible=False, label="borders")
        gl = ax.gridlines()
        gl.xlocator = mtick.FixedLocator([-180, -120, -60, 0, 60, 120, 180])
        gl.xformatter = LONGITUDE_FORMATTER
        gl.yformatter = LATITUDE_FORMATTER
        ax.spines["geo"].set_edgecolor(self.uicolors[1])

        # Marker
        marker_outer = dict(markersize=15,
                        markeredgecolor="firebrick",
                        markeredgewidth=5,
                        )
        marker_inner = dict(markersize=15,
                        markeredgecolor=self.uicolors[0],
                        markeredgewidth=0.7,
                        )
        m = MarkerStyle("1", capstyle="butt")
        ax.plot(0, 0, marker=m, **marker_outer)
        ax.plot(0, 0, marker=m, **marker_inner)

    def plot_flag(self, ax):
        # Flag image
        country = self.current_event.country[0]
        image, _ = Geocode.get_flag(self.current_event.iso2)
        ax.imshow(image)

        # Country name
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        country_xpos = (xlim[1] - xlim[0]) * 0.5
        country_ypos = ylim[1] - (ylim[0] - ylim[1]) * 0.1
        ax.text(country_xpos, country_ypos,
                f"{country}",
                va="bottom",
                ha="center",
                fontsize="xx-large",
                color=self.uicolors[1],
                fontweight="bold"
                )

        # Format axis
        Utilities.format_axis(ax, self.uicolors[1])

    def plot_sources(self, ax):
        spec = gridspec.GridSpecFromSubplotSpec(ncols=4, nrows=1, subplot_spec=ax,
                                                width_ratios=[1, 1, 1, 1], wspace=0, hspace=0,
                                                )

        # Get flags
        un_flag, _ = Geocode.get_flag("un")
        eu_flag, _ = Geocode.get_flag("eu")

        # Gradient axis
        subax_gradL = ax.figure.add_subplot(spec[1])
        subax_gradL.imshow(un_flag, visible=False)
        subax_gradR = ax.figure.add_subplot(spec[2])
        subax_gradR.imshow(un_flag, visible=False)

        def color_gradient(c1,c2,mix=0):
            c1=np.array(mpl.colors.to_rgb(c1))
            c2=np.array(mpl.colors.to_rgb(c2))
            return mpl.colors.to_hex((1-mix)*c1 + mix*c2)

        flag_width = subax_gradL.get_xlim()[1]
        c1 = "#003399"
        c2 = "#019EDB"
        cmid = "#0169BA"
        n = int(flag_width)
        for x in range(n+1):
            subax_gradL.axvline(x, color=color_gradient(c1,cmid,x/n), linewidth=4)
            subax_gradR.axvline(x, color=color_gradient(cmid,c2,x/n), linewidth=4)

        # EU flag
        subax_eu = ax.figure.add_subplot(spec[0])
        subax_eu.imshow(eu_flag)
        Utilities.format_axis(subax_eu, self.uicolors[1], sides="tbl")

        # UN flag
        subax_un = ax.figure.add_subplot(spec[3])
        subax_un.imshow(un_flag)
        Utilities.format_axis(subax_un, self.uicolors[1], sides="tbr")

        # Text
        subax_text = ax.figure.add_axes([0, 0, 1, 1], zorder=10)
        wrapped_source = Utilities.wrap_text("Global Disaster Alert and Coordination System", 30)
        txt = subax_text.text(0.5, 0.5,
                        f"{wrapped_source}\n https://gdacs.org",
                        transform=ax.transAxes,
                        ha="center",
                        va="center",
                        fontsize="x-small",
                        fontweight="bold",
                        color="white"
                        )
        txt.set_path_effects([fx.Stroke(linewidth=1, foreground="black"), fx.Normal()])

        # Format axis
        ax.set_axis_off()
        Utilities.format_axis(subax_gradL, self.uicolors[1], sides="tb")
        Utilities.format_axis(subax_gradR, self.uicolors[1], sides="tb")
        subax_text.set_axis_off()

    def plot_info(self, ax):
            # Category
            ax.text(0.5, 1,
                    f"{Event.get_categories()[self.current_event.category]}",
                    ha="center",
                    va="top",
                    fontsize=25,
                    fontweight="bold",
                    color=self.uicolors[1])

            # Alert
            alert_color = Utilities.get_alert_color(self.current_event.alert)
            ax.text(0.5, 0.9,
                    f"{self.current_event.alert} alert",
                    ha="center",
                    va="top",
                    fontsize="x-large",
                    fontweight="bold",
                    color=alert_color)

            # Date and coordinates
            lat, lon = Geocode.coord_converter(self.current_event.coords)
            ax.text(0.5, 0.8,
                    f"{self.current_event.date}\n({lat}, {lon})",
                    ha="center",
                    va="top",
                    fontsize="medium",
                    fontweight="regular",
                    color=self.uicolors[1])

            # Severity
            sev_tit = ax.text(0.5, 0.65,
                              "Severity",
                              ha="center",
                              va="top",
                              fontsize="large",
                              fontweight="bold",
                              color=self.uicolors[1],
                              alpha=0.5)
            wrapped_text = Utilities.wrap_text(self.current_event.severity, 40)
            bbox_props = dict(facecolor="lightgrey", edgecolor=self.uicolors[1], boxstyle="round,pad=0.5", alpha=0.5)
            sev = ax.text(0.5, 0,
                            wrapped_text,
                            ha="center",
                            va="top",
                            fontsize="medium",
                            fontweight="regular",
                            color=self.uicolors[1],
                            bbox=bbox_props)
            self.nextline(ax, sev_tit, sev)

            # Population affected
            population_text = f"{self.current_event.population} people affected"
            bbox_props = dict(facecolor="lightgrey", edgecolor=self.uicolors[1], boxstyle="round,pad=0.5", alpha=0.5)
            pop = ax.text(0.5, 0,
                    population_text,
                    ha="center",
                    va="top",
                    fontsize="medium",
                    fontweight="regular",
                    color=self.uicolors[1],
                    bbox=bbox_props)
            self.nextline(ax, sev, pop)

            # Other countries affected
            bbox_props = dict(facecolor=self.uicolors[0], edgecolor=self.uicolors[1], boxstyle="round,pad=0.5", alpha=0.5)
            otherctry = ax.text(0.5, 0,
                    "otherctry_text",
                    ha="center",
                    va="top",
                    fontsize="medium",
                    fontweight="regular",
                    color=self.uicolors[1],
                    bbox=bbox_props,
                    visible=False)
            self.nextline(ax, pop, otherctry, pad=0.15)
            if len(self.current_event.country) > 1:
                otherctry_text = (
                    r"$\it{Other\ countries\ affected:}$" +
                    f"\n {Utilities.wrap_text(", ".join(self.current_event.country[1:]), 40)}"
                )
                otherctry.set_text(otherctry_text)
                otherctry.set_visible(True)

            # Format axis
            ax.set_axis_off()


    #--------- UPDATERS ---------#
    def _update_map(self):
        # Get map axis
        for axis in self.figure.get_axes():
            if axis.get_label() == "ax_map": ax_map = axis

        # Update map axis
        proj = ccrs.NearsidePerspective(self.current_event.coords[1], self.current_event.coords[0])
        ax_map.projection = proj

    def _update_info(self):
        # Get information axis
        for axis in self.figure.get_axes():
            if axis.get_label() == "ax_info": ax_info = axis

        # Update information axis
        ax_info.texts[0].set_text(f"{Event.get_categories()[self.current_event.category]}")
        ax_info.texts[1].set_text(f"{self.current_event.alert} alert")
        ax_info.texts[1].set_color(Utilities.get_alert_color(self.current_event.alert))
        lat, lon = Geocode.coord_converter(self.current_event.coords)
        ax_info.texts[2].set_text(f"{self.current_event.date}\n({lat}, {lon})")
        wrapped_text = Utilities.wrap_text(self.current_event.severity, 40)
        ax_info.texts[4].set_text(wrapped_text)
        ax_info.texts[5].set_text(f"{self.current_event.population} people affected")
        self.nextline(ax_info, ax_info.texts[4], ax_info.texts[5])
        if len(self.current_event.country) > 1:
            otherctry_text = (
                r"$\it{Other\ countries\ affected:}$" +
                f"\n {Utilities.wrap_text(", ".join(self.current_event.country[1:]), 40)}"
            )
            ax_info.texts[6].set_text(otherctry_text)
            ax_info.texts[6].set_visible(True)
        else:
            ax_info.texts[6].set_visible(False)
        self.nextline(ax_info, ax_info.texts[5], ax_info.texts[6], pad=0.15)

    def _update_flag(self):
        # Get flag axis
        for axis in self.figure.get_axes():
            if axis.get_label() == "ax_flag": ax_flag = axis

        # Update flag axis
        flag = ax_flag.findobj(mpl.image.AxesImage)[0]
        new_code = self.current_event.iso2
        new_country = self.current_event.country[0]
        new_image, ratio = Geocode.get_flag(new_code)
        flag.set_data(new_image)
        flag.set_extent((0, 2560, 0, 2560*ratio))
        ax_flag.texts[0].set_text(new_country)
        xlim = ax_flag.get_xlim()
        ylim = ax_flag.get_ylim()
        country_xpos = (xlim[1] - xlim[0]) * 0.5
        country_ypos = ylim[1] - (ylim[0] - ylim[1]) * 0.1
        ax_flag.texts[0].set_position((country_xpos, country_ypos))

    def _update_id(self):
        for axis in self.figure.get_axes():
            if axis.get_label() == "ax_id": ax_id = axis
        ax_id.texts[0].set_text(f"{self.current_event.category} {self.current_event.evid}")

    def _border_visibility(self):
        # Get map axis
        for axis in self.figure.get_axes():
            if axis.get_label() == "ax_map": ax_map = axis
        # Get borders object
        for artist in ax_map.get_children():
            if artist.get_label() == "borders": borders = artist
        # Toggle visibility
        if borders.get_visible() == True:
            borders.set_visible(False)
            rich.print("[bold]Borders [italic red]disabled ✗[/italic red][/bold]")
        elif borders.get_visible() == False:
            borders.set_visible(True)
            rich.print("[bold]Borders [italic green]enabled ✓[/italic green][/bold]")

    def _callback_handler(self, callback):
        # Next/previous event
        if callback.key == "right":
            print("Showing next event...")
            self.current_index += 1
        elif callback.key == "left":
            print("Showing previous event...")
            self.current_index -= 1

        # Open GDACS official link for the event
        if callback.key == "w":
            print("Opening official GDACS report...")
            webbrowser.open(self.current_event.link)

        # Toggle borders
        if callback.key == "b":
            self._border_visibility()

        # Update the figure with current_event
        self._update_map()
        self._update_info()
        self._update_flag()
        self._update_id()

        # Redraw the updated figure
        self.figure.canvas.manager.set_window_title(f"EventViewer ({self.current_index+1}/{len(self.events)})")
        self.figure.canvas.draw()

    #--------- UTILITIES ---------#
    def nextline(self, ax, artist1, artist2, pad=0.05):
        lowlimit = artist1.get_window_extent().transformed(ax.transData.inverted()).y0
        artist2.set_y(lowlimit - pad)

    def key_shortcuts(self, console):
        # Create title and text and stylize
        tit = "[bold]Keyboard Shortcuts[/bold]"
        txt = ( "◀ | previous event\n"
                "▶ | next event\n"
                "W | open official report\n"
                "B | toggle border visibility\n"
                "Q | terminate EventViewer")
        styled_txt = Text(txt, justify="left")
        styled_txt.stylize(style="bold yellow", start=0, end=1)
        styled_txt.stylize(style="bold yellow", start=19, end=20)
        styled_txt.stylize(style="bold yellow", start=34, end=35)
        styled_txt.stylize(style="bold yellow", start=59, end=60)
        styled_txt.stylize(style="bold yellow", start=88, end=89)
        styled_txt.stylize(style="italic", start=102)
        # Create panel and print
        panel = Panel(styled_txt, expand=False, title=tit)
        console.line()
        console.print(panel, justify="center")
        console.line()

    #--------- SHOW ---------#
    def run(self):
        # Connect the key press event to the update function
        self.figure.canvas.mpl_connect("key_press_event", self._callback_handler)
        # Prevent figure resizing
        win = self.figure.canvas.window()
        win.setFixedSize(win.size())
        # Initialize console
        console = Console()
        # Initialization separator
        console.line(2)
        txt = "[bold blue][italic]EventViewer[/italic] initialized[/bold blue]"
        console.rule(title=txt, characters="·", style="blue", align="center")
        # Keyboard shortcuts
        self.key_shortcuts(console)
        # Show the final figure
        plt.show()
        # Termination separator
        txt = "[bold blue][italic]EventViewer[/italic]  terminated[/bold blue]"
        console.rule(title=txt, characters="·", style="blue", align="center")
        console.line(2)
