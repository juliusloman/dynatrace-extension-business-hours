from dynatrace_extension import Extension, Status, StatusValue
import croniter
# from icalendar import Calendar, Event
from datetime import datetime, date
import pytz


class ExtensionImpl(Extension):

    def initialize(self):
        self.metric_key = "business_hours"
        self.metric_level_dimension = "level"

    def query(self):
        """
        The query method is automatically scheduled to run every minute
        """
        self.logger.info("Generating business hours metrics")

        for level in self.activation_config["levels"]:
            level_name = level["level"]
            cron_expression = level["cron"]
            weight = level["weight"]
            weight_outside = level.get("weight_outside")
            self.logger.debug(f"Generating {level} of {cron_expression}")
            
            if croniter.croniter.match(cron_expression, datetime.now()):
                self.report_metric(self.metric_key, weight, dimensions={self.metric_level_dimension: level_name})
            elif weight_outside:
                self.report_metric(self.metric_key, weight_outside, dimensions={self.metric_level_dimension: level_name})    

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
