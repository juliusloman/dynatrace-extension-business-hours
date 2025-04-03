from dynatrace_extension import Extension, Status, StatusValue
import croniter
from datetime import datetime
from dataclasses import dataclass, field
from dacite import from_dict
from typing import List
import icalendar
import recurring_ical_events
import time
import requests

@dataclass
class CronBH:
    level: str
    cron: str
    weight: float = 1
    generate_negative: bool = False
    weight_outside: float = None
@dataclass
class CalendarBH:
    level: str
    calendar_url: str
    refresh_minutes: int
    use_summary: bool
    weight: float = 1
    weight_outside: float = None
    generate_negative: bool = False
    rical: icalendar = None
    last_refresh: int = 0
    event_summaries: set = field(default_factory=set)

@dataclass
class BHConfig:
    crons: List[CronBH]
    calendars: List[CalendarBH]


class ExtensionImpl(Extension):
    bh_config: BHConfig

    def initialize(self):
        self.metric_key = "business_hours"
        self.metric_level_dimension = "level"        
        self.negative_prefix = "-"
        self.bh_config = from_dict(data_class=BHConfig, data=self.activation_config.config)        
        self.refresh_calendars()

    def query(self):
        """
        The query method is automatically scheduled to run every minute
        """
        self.logger.info("Generating business hours metrics")
        self.process_crons()
        self.refresh_calendars()
        self.process_calendars()

    def process_crons(self):
        for cron in self.bh_config.crons:
            self.logger.info(f"Generating business hour metric by cron {cron.level} of {cron.cron}")
            
            if croniter.croniter.match(cron.cron, datetime.now()):
                self.logger.info(f"Generating business hour metric level={cron.level} with value {cron.weight}")
                self.report_metric(self.metric_key, cron.weight, dimensions={self.metric_level_dimension: cron.level})
            else:
                if cron.weight_outside is not None:
                    self.logger.info(f"Generating business hour negative metric level={cron.level} with value {cron.weight_outside}")
                    self.report_metric(self.metric_key, cron.weight_outside, dimensions={self.metric_level_dimension: cron.level})
                if cron.generate_negative:
                    self.logger.info(f"Generating business hour negative metric level={self.negative_prefix + cron.level} with value {cron.weight}")
                    self.report_metric(self.metric_key, cron.weight, dimensions={self.metric_level_dimension: self.negative_prefix + cron.level})                            

    def process_calendars(self):
        for calendar in self.bh_config.calendars:
            self.logger.info(f"Generating business hour metric from calendar {calendar.calendar_url}")
            try:
                current_events = calendar.rical.at(date=datetime.now())
                if current_events:
                    if calendar.use_summary:
                        active_event_summaries = set()
                        for event in current_events:
                            event_summary = event.get("SUMMARY")
                            active_event_summaries.add(event_summary)
                            if event_summary:
                                self.report_metric(self.metric_key, calendar.weight, dimensions={self.metric_level_dimension: event_summary})
                            else:
                                self.report_metric(self.metric_key, calendar.weight, dimensions={self.metric_level_dimension: calendar.level})

                        if calendar.generate_negative:                            
                            self.logger.info(f"Generating negative values for inactive summaries {calendar.event_summaries - active_event_summaries}")
                            for level in calendar.event_summaries - active_event_summaries:
                                self.report_metric(self.metric_key, calendar.weight, dimensions={self.metric_level_dimension: self.negative_prefix + level})                            
                    else:
                        self.report_metric(self.metric_key, calendar.weight, dimensions={self.metric_level_dimension: calendar.level})
                else:
                    if calendar.weight_outside:
                        self.report_metric(self.metric_key, calendar.weight_outside, dimensions={self.metric_level_dimension: calendar.level})

                    if calendar.generate_negative:
                        if calendar.use_summary:
                            self.logger.info(f"Generating negative values for inactive summaries {calendar.event_summaries}")
                            for level in calendar.event_summaries:                                
                                self.report_metric(self.metric_key, calendar.weight, dimensions={self.metric_level_dimension: self.negative_prefix + level})                            
                        else:
                            self.logger.info(f"Generating negative value for level {calendar.level}")
                            self.report_metric(self.metric_key, calendar.weight, dimensions={self.metric_level_dimension: self.negative_prefix + calendar.level})

            except Exception as e:
                self.logger.error(f"Error {e} when processing calendar {calendar.calendar_url}")

    def refresh_calendars(self):
        for calendar in self.bh_config.calendars:
            if time.time() > calendar.last_refresh + 60*calendar.refresh_minutes:
                try:
                    self.logger.info(f"Loading ical from {calendar.calendar_url}")
                    ical_response = requests.get(calendar.calendar_url)
                    ical_response.raise_for_status()
                    ical = icalendar.Calendar.from_ical(ical_response.text)
                    calendar.rical = recurring_ical_events.of(ical)
                    calendar.last_refresh = time.time()
                    for event in ical.walk('VEVENT'):
                        calendar.event_summaries.add(str(event.get("SUMMARY")))
                    self.logger.info(f"Found summaries {calendar.event_summaries}")
                except Exception as e:
                    self.logger.error(f"Error {e} for {calendar.calendar_url}")
            else:
                self.logger.info(f"Not refreshing {calendar.calendar_url}")

    def fastcheck(self) -> Status:
        """
        This is called when the extension runs for the first time.
        If this AG cannot run this extension, raise an Exception or return StatusValue.ERROR!
        """
        return Status(StatusValue.OK)


def main():
    ExtensionImpl().run()


if __name__ == '__main__':
    main()
