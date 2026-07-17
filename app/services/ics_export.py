from icalendar import Calendar, Event as ICalEvent

from app.db import Event


def build_ics(events: list[Event]) -> bytes:
    cal = Calendar()
    cal.add("prodid", "-//CFP Conference Agent//render.com//")
    cal.add("version", "2.0")

    for ev in events:
        ical_event = ICalEvent()
        ical_event.add("summary", ev.title)
        ical_event.add("uid", f"event-{ev.id}@cfp-agent")
        description_lines = [ev.link]
        if ev.deadline:
            description_lines.append(f"Deadline: {ev.deadline}")
        if ev.location:
            description_lines.append(f"Where: {ev.location}")
        ical_event.add("description", "\n".join(description_lines))
        if ev.location:
            ical_event.add("location", ev.location)
        cal.add_component(ical_event)

    return cal.to_ical()
