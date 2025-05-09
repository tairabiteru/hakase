from django.db import models
from .base import DiscordBaseModel
from ...core.fields import TimezoneField
from ....lib.utils import utcnow
import zoneinfo


class Locale(DiscordBaseModel):
    TEMPERATURE_UNITS = [
        ('degF', "°F"),
        ('degC', "°C"),
        ('degK', "K")
    ]

    DISTANCE_UNITS = [
        ('meters', 'm'),
        ('miles', 'mi'),
        ('kilometers', 'km'),
        ('feet', 'ft')
    ]

    ELEVATION_UNITS = [
        ('meters', 'm'),
        ('feet', 'ft')
    ]

    PRESSURE_UNITS = [
        ('psi', 'psi'),
        ('bar', 'bar'),
        ('pascal', 'Pa'),
        ('hectopascal', 'hPa'),
        ('mmHg', 'mmHg'),
        ('inHg', 'inHg')
    ]

    SPEED_UNITS = [
        ('mph', 'mph'),
        ('kph', 'kph'),
        ('knots', 'kt')
    ]

    DATE_FORMATS = [
        ('%A, %B %-d, %Y', 'day month dd, yyyy'),
        ('%-m/%-d/%Y', 'mm/dd/yyyy'),
        ('%-d/%-m/%Y', 'dd/mm/yyyy'),
        ('%Y/%m/%d', 'yyyy/mm/dd'),
        ('%-m-%-d-%Y', 'mm-dd-yyyy'),
        ('%-d-%-m-%Y', 'dd-mm-yyyy'),
        ('%Y-%m-%d', 'yyyy-mm-dd')
    ]

    TIME_FORMATS = [
        ('%-I:%M:%S %p %Z', '12-hr HH:MM:SS Z'),
        ('%-H:%M:%S %Z', '24-hr HH:MM:SS Z'),
        ('%-I:%M %Z', '12-hr HH:MM Z'),
        ('%-H:%M %Z', '24-hr HH:MM Z')
    ]

    temperature_unit = models.CharField(max_length=4, choices=TEMPERATURE_UNITS, default='degF', help_text="Your preferred temperature unit.")
    distance_unit = models.CharField(max_length=32, choices=DISTANCE_UNITS, default="miles", help_text="Your preferred unit of distance.")
    elevation_unit = models.CharField(max_length=32, choices=ELEVATION_UNITS, default="feet", help_text="Your preferred unit of elevation.")
    pressure_unit = models.CharField(max_length=32, choices=PRESSURE_UNITS, default="hectopascal", help_text="Your preferred unit of atmospheric pressure.")
    speed_unit = models.CharField(max_length=32, choices=SPEED_UNITS, default="mph", help_text="Your preferred unit of speed.")
    date_format = models.CharField(max_length=32, choices=DATE_FORMATS, default="%-m/%-d/%Y", help_text="Your preferred date format.")
    time_format = models.CharField(max_length=32, choices=TIME_FORMATS, default="%-I:%M:%S %p %Z", help_text="Your preferred time format.")
    timezone = TimezoneField(help_text="Your timezone.")

    @property
    def datetime_format(self):
        return f"{self.date_format} {self.time_format}"
    
    def aslocaltime(self, time):
        return time.astimezone(zoneinfo.ZoneInfo(self.timezone))
    
    def localnow(self):
        return self.aslocaltime(utcnow())
    
    def aslocaltime_format(self, time):
        return self.aslocaltime(time).strftime(self.time_format)
    
    def __str__(self):
        try:
            self.user.attach_bot(self._bot)
            return f"Locale Settings for {self.user.obj.username}"
        except (ValueError, AttributeError):
            return f"Locale Settings for UID ({self.user.id})"
    
    @property
    def unit_definition(self):
        return {
            '[length] / [time]': self.speed_unit,
            '[temperature]': self.temperature_unit,
            '[mass] / [length] / [time] ** 2': self.pressure_unit,
            '[length]': self.distance_unit,
            'elevation': self.elevation_unit
        }