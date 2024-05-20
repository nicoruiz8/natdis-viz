from rich.console import Console
import rich.box as box
from rich.panel import Panel
from rich.prompt import IntPrompt, Confirm, Prompt

import sys
import textwrap
from datetime import datetime, date, timedelta
from functools import partial
from typing import Union

from modules.eventGDACS import Event, EventContainer, EventViewer


def main():
    # Initialize
    console = Console()
    init_ui(console)

    # Request events
    with console.status("Requesting GDACS events...", spinner="earth"):
        events = EventContainer()
        events.request()

    # Filter events
    choices = ["date", "category", "alert", "none"]
    fil_prompt = "🎛️ Filter events by"
    while True:
        if not events:
            console.print("[bold red]⚠️ No events to display ⚠️[/bold red]")
            term_ui(console)  # terminate session
            break
        console.print(f"{len(events)} events are ready to be displayed.")
        if len(choices) < 2:
            break
        fil = Prompt.ask(fil_prompt, choices=choices)
        match fil:
            case "date":
                date_prompt = "╰─ 🗓️ Show last x days where x"
                while True:
                    days = IntPrompt.ask(date_prompt)
                    if not days >= 0:
                        console.print("[red]Please enter a non-negative integer[/red]")
                    else:
                        break
                events = filter_events(date_filter, days, events)
                choices.remove("date")
            case "category":
                category_prompt = "╰─ 🗂️ Show just one of these categories"
                category = Prompt.ask(
                    category_prompt, choices=Event.get_categories().keys()
                )
                events = filter_events(category_filter, category, events)
                choices.remove("category")

            case "alert":
                alert_prompt = "╰─ 🚥 Show just events with alert-level"
                alert = Prompt.ask(alert_prompt, choices=["green", "orange", "red"])
                events = filter_events(alert_filter, alert, events)
                choices.remove("alert")
            case "none":
                break

    # Number of events and panel summary
    n_prompt = f"📟 How many events do you want to see?"
    n = IntPrompt.ask(n_prompt)
    if n < 1:
        term_ui(console)
    else:
        events = events[0:n]
        events.panel()

    # Run EventViewer
    if Confirm.ask("📺 Run [italic]EventViewer[/italic]?"):
        mode = Prompt.ask("⬯⬮ Choose appearance", choices=["light", "dark"])
        with console.status(
            "Initializing [italic]EventViewer[/italic]...", spinner="earth"
        ):
            viewer = EventViewer(events=events, appearance=mode)
        viewer.run()
        term_ui(console)
    else:
        term_ui(console)


# UI construction
def init_ui(console: Console):
    """Initialization UI"""
    console.line()
    tit = "[bold]⫸ Global Disaster Alert and Coordination System ⫷[/bold]"
    console.rule(title=tit, style="bold", align="center", characters="≣")
    desc = "GDACS is a cooperation framework between United Nations and European Commission"
    desc = wrap_text(desc, 40)
    panel = Panel(desc, expand=False, box=box.SQUARE)
    console.print(panel, justify="center")
    console.line()


def term_ui(console: Console):
    """Termination UI"""
    tit = "[bold]Made by Nicolás Ruiz Lafuente[/bold]"
    panel = Panel("No affiliation to EU or UN", title=tit, box=box.SQUARE)
    console.print(panel, justify="center")
    console.rule(style="bold", align="center", characters="≣")
    console.line()
    sys.exit()


# Utils
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


# Filtering
def date_filter(delta: int, event: Event) -> bool:
    """
    Filter a GDACS Event by its date.

    :param delta: days to go back from today
    :param event: GDACS event

    :return: bool depending on the filter success
    """
    # Error handling
    if not isinstance(event, Event):
        raise TypeError("event must be an instance of Event")
    if not (isinstance(delta, int) and delta >= 0):
        raise ValueError("delta must be non-negative int")

    # Filter
    today = date.today()
    delta = timedelta(delta)
    event_date = datetime.strptime(event.date, "%a, %d %b %Y").date()
    if (today - event_date) <= delta:
        return True
    else:
        return False


def category_filter(category: str, event: Event) -> bool:
    """
    Filter a GDACS Event by its category.

    :param category: {'TC', 'EQ', 'FL', 'VO', 'DR', 'NA'}
    :param event: GDACS event

    :return: bool depending on the filter success
    """
    # Error handilng
    if not isinstance(event, Event):
        raise TypeError("event must be an instance of Event")
    if not (isinstance(category, str) and category.upper() in Event.get_categories()):
        raise ValueError("category must be TC, EQ, FL, VO, DR or NA.")

    # Filter
    if event.category == category:
        return True
    else:
        return False


def alert_filter(alert: str, event: Event) -> bool:
    """
    Filter a GDACS Event by its alert level.

    :param alert: {'Green', 'Orange', 'Red'}
    :param event: GDACS event

    :return: bool depending on the filter success
    """
    # Error handling
    if not isinstance(event, Event):
        raise TypeError("event must be an instance of Event")
    if not (isinstance(alert, str) and alert.lower() in ("green", "orange", "red")):
        raise ValueError("Alert level can only be Green, Orange or Red.")

    # Filter
    if event.alert.lower() == alert.lower():
        return True
    else:
        return False


def filter_events(
    fil: callable, key: Union[int, str], events: EventContainer
) -> EventContainer:
    """
    Function to implement the event filters to an events on an EventContainer.

    :param fil: filter function to apply {date_filter, category_filter, alert_filter}
    :param key: filtering keyword depending on the filter function chosen
    :param events: EventContainer we want to filter

    :return: bool depending on the filter success
    """
    # Error handling (events)
    if not isinstance(events, EventContainer):
        raise TypeError("events must be an instance of EventContainer")

    # Error handling (filter function)
    if not fil in (date_filter, category_filter, alert_filter):
        raise ValueError("fil must be an existing filter function")

    # Apply filter
    custom_filter = partial(fil, key)
    filtered_events = filter(custom_filter, events)
    return EventContainer(list(filtered_events))


# Call main
if __name__ == "__main__":
    main()
