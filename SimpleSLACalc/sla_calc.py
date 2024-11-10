from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import holidays as pyholidays
import pendulum
from dateutil import tz

from .exceptions import (
    InvalidCustomDateList,
    InvalidDateObject,
    NoSLACounterItems,
    ToManySLACounterItems,
)


@dataclass(frozen=True, order=False)
class SLAItem:
    """Class based SLA results item for user return

    Returns:
        cls: Class Object populated with SLA results calculations
    """

    start_time: pendulum.DateTime
    open_time: pendulum.DateTime | None
    close_time: pendulum.DateTime | None
    sla_expiration_time: pendulum.DateTime

    def sla_exp_hour(self) -> int:
        return self.sla_expiration_time.hour

    def sla_exp_min(self) -> int:
        return self.sla_expiration_time.minute

    def sla_exp_day(self) -> int:
        return self.sla_expiration_time.day

    def sla_exp_date(self) -> pendulum.Date:
        return self.sla_expiration_time.date()

    def __repr__(self) -> str:
        return str(self.sla_expiration_time)


class SLACalculator:
    def __init__(self):
        pass

    def calculate(
        self,
        start_time: datetime | pendulum.DateTime | str,
        open_hour: int,
        open_minute: int,
        close_hour: int,
        close_minute: int,
        time_zone: str,
        skip_business_hours: Optional[bool] = True,
        sla_hours: Optional[float] = None,
        sla_days: Optional[int] = None,
        sla_weeks: Optional[int] = None,
        excluded_dates: Optional[list[str]] = None,
        holiday_country: Optional[str] = None,
        holiday_state: Optional[str] = None,
        holiday_province: Optional[str] = None,
    ) -> SLAItem:
        """Calculate SLA times based on open and close business hours(24 hour format).
        Optionally add Country(IE: "US"), state(IE:TX), or province to calculate SLA's
        with holidays included.

        Additionally you can supply a list of dates(IE: ["2023-10-10", "2023-11-01"]) to
        exlude from SLA calculations if necessary.

        Args:
            start_time (datetime | pendulum.DateTime | str): Start of sla time calculation(IE: "2023-10-01") or a datetime object
            open_hour (int): Start of business hour(24h format)
            open_minute (int): Start of business minute
            close_hour (int): End of business hour(24h format)
            close_minute (int): End of business minute
            time_zone (str): Timezone in which to process calculation
            skip_business_hours (Optional[bool]): When True, skips business hours, and just calculates raw SLA. Defaults to True.
            sla_hours (Optional[int], optional): Provide hours to calculate SLA in hours. Defaults to None.
            sla_days (Optional[int], optional): Provide days to calculate SLA in days. Defaults to None.
            sla_weeks (Optional[int], optional): Provide weeks to calculate SLA in weeks. Defaults to None.
            excluded_dates (Optional[list[str]], optional): Provide a list of dates in string format(IE: ["2023-10-1", 2023-10-02"]). Defaults to None.
            holiday_country (Optional[str], optional): Two character country code for holiday parsing. Required for holiday date SLA exclusion. Defaults to None.
            holiday_state (Optional[str], optional): Optional two character state for holiday date SLA exclusion. Defaults to None.
            holiday_province (Optional[str], optional): Optional two character province for holiday date SLA exclusion. Defaults to None.

        Raises:
            ValueError: Error when providing more than one of "sla_hours, sla_days, sla_weeks"
            ValueError: Error when no valid SLA timeframe in minutes can be calculated

        Returns:
            BusinessSLAItem: Class item containing results of sla calculation
        """
        if sla_hours and sla_days and sla_weeks:
            raise ToManySLACounterItems("Please provide sla_hours, or sla_days, or sla_weeks. No more than one.")
        if sla_hours:
            self.sla_mins = self.convert_sla_time_to_mins(sla_time=sla_hours, sla_type="hours")
        elif sla_days:
            self.sla_mins = self.convert_sla_time_to_mins(sla_time=sla_days, sla_type="days")
        elif sla_weeks:
            self.sla_mins = self.convert_sla_time_to_mins(sla_time=sla_weeks, sla_type="weeks")
        else:
            raise NoSLACounterItems("You did not provide a matching SLA timeframe")
        self.open_hour = open_hour
        self.open_minute = open_minute
        self.close_hour = close_hour
        self.close_minute = close_minute
        self.time_zone = time_zone
        self.skip_business_hours = skip_business_hours
        self.excluded_dates = excluded_dates
        self.holiday_country = holiday_country
        self.holiday_state = holiday_state
        self.holiday_province = holiday_province

        # Recursively run to find final sla time expiration and return data
        start_time = self.validate_or_convert_pendulum_datetime(datetime_object=start_time, timezone=time_zone)  # type: ignore
        sla_time = self.find_sla_time(start_time=start_time)
        return sla_time

    def find_sla_time(self, start_time: pendulum.DateTime) -> SLAItem:
        """Recursive fuctional component to find the exact SLA expiration date and time

        Args:
            start_time (pendulum.DateTime): Starting time to calculate SLA expiration

        Returns:
            BusinessSLAItem: Class based results object with SLA calculations
        """
        start_time, open_time, close_time = self.check_start_time_date_variables(start_time=start_time)
        if self.skip_business_hours:
            sla_time = start_time.add(minutes=self.sla_mins)
            return SLAItem(start_time=start_time, open_time=None, close_time=None, sla_expiration_time=sla_time)
        if start_time < open_time:
            start_time = open_time
        elif start_time > close_time:
            start_time = open_time.add(days=1)
            start_time, open_time, close_time = self.check_start_time_date_variables(start_time=start_time)
        time_left_in_today = start_time.diff(close_time).in_minutes()
        if time_left_in_today >= self.sla_mins:
            sla_obj = SLAItem(
                start_time=start_time,
                open_time=open_time,
                close_time=close_time,
                sla_expiration_time=start_time.add(minutes=self.sla_mins),
            )
            return sla_obj
        else:
            self.sla_mins = self.sla_mins - time_left_in_today
            start_time = open_time.add(days=1)
            return self.find_sla_time(start_time=start_time)

    def check_start_time_date_variables(self, start_time: pendulum.DateTime):
        """Wrapper function to adjust start time forf optional SLA calculations such as
        holidays, and excluded days

        Args:
            start_time (pendulum.DateTime): Current date and time object to begin calculations

        Returns:
            pendulum.DateTime, pendulum.DateTime, pendulum.DateTime: Calculated SLA time, new open_time, new close_time
        """
        start_time = self.check_if_working_days(start_time=start_time)
        if self.holiday_country:
            start_time = self.check_for_holidays(start_time=start_time)
        if self.excluded_dates:
            start_time = self.exclude_custom_dates(start_time=start_time)
        open_time = self.calculate_open_and_close_times(
            sla_start_time=start_time, hour_of_day=self.open_hour, minute_of_day=self.open_minute
        )
        close_time = self.calculate_open_and_close_times(
            sla_start_time=start_time, hour_of_day=self.close_hour, minute_of_day=self.close_minute
        )
        return start_time, open_time, close_time

    def calculate_open_and_close_times(self, sla_start_time: pendulum.DateTime, hour_of_day: int, minute_of_day: int):
        """Takes in the target hour of the day(24h) and returns a
        datetime object with the minutes and hour replaced with the provided
        "hour of the day"

        Args:
            sla_start_time (pendulum.DateTime): Current sla time object
            hour_of_day (int): Hour of the day to apply to sla time object

        Returns:
            _type_: _description_
        """
        calculated_time = pendulum.datetime(
            year=sla_start_time.year,
            month=sla_start_time.month,
            day=sla_start_time.day,
            hour=hour_of_day,
            minute=minute_of_day,
            second=0,
            tz=pendulum.timezone(self.time_zone),
        )
        return calculated_time

    def check_if_working_days(self, start_time: pendulum.DateTime) -> pendulum.DateTime:
        """Checks if current datetime object falls on a weekend.

        Args:
            start_time (pendulum.DateTime): Current calculated datetime object

        Returns:
            pendulum.DateTime: Recalculated Datetime Object
        """
        while start_time.day_of_week in (pendulum.SUNDAY, pendulum.SATURDAY):
            start_time = start_time.add(days=1)
            start_time = pendulum.datetime(
                year=start_time.year,
                month=start_time.month,
                day=start_time.day,
                hour=self.open_hour,
                minute=0,
                second=0,
                tz=pendulum.timezone(self.time_zone),
            )
        return start_time

    def check_for_holidays(self, start_time: pendulum.DateTime) -> pendulum.DateTime:
        """If requested, checks for holidays in any provided 2 character
        country name. If holiday date is detected the provided DateTime
        object is advanced 1 day until not equal to a holiday object.

        Args:
            start_time (pendulum.DateTime): Current DateTime Object

        Returns:
            pendulum.DateTime: Calculated/adjusted Datetime Object
        """
        if not self.holiday_country:
            return start_time
        if self.holiday_state:
            holiday_state = self.holiday_state
        else:
            holiday_state = None
        if self.holiday_province:
            holiday_province = self.holiday_province
        else:
            holiday_province = None
        holidays = list(
            pyholidays.CountryHoliday(
                country=self.holiday_country, years=[start_time.year], prov=holiday_province, state=holiday_state
            ).keys()
        )
        while pendulum.date(year=start_time.year, month=start_time.month, day=start_time.day) in holidays:
            start_time = start_time.add(days=1)
        return start_time

    def validate_or_convert_pendulum_datetime(
        self, datetime_object: datetime | pendulum.DateTime | str, timezone: str
    ) -> pendulum.DateTime:
        """Quick and dirty validation of the provided base datetime object. If it
        is a str or datetime type it will be converted to a pendulum.DateTime
        object and returned

        Args:
            datetime_object (datetime | pendulum.DateTime | str): Base starting date object
            timezone (str): Target timzeone for calculations

        Returns:
            pendulum.DateTime: Converted or passed DateTime object
        """
        if isinstance(datetime_object, pendulum.DateTime):
            return datetime_object
        converted_object = pendulum.parse(str(datetime_object), tz=pendulum.timezone(timezone))
        return converted_object  # type: ignore

    def convert_utc_to_local(self, utc_time: datetime, local_timezone: str):
        """Helper function for converting a UTC datetime object into a
        timezone aware local time object

        Args:
            utc_time (datetime): datetime UTC object
            local_timezone (str): Target timezone to convert into

        Returns:
            datetime: local TZ aware datetime object
        """
        from_zone = tz.gettz("UTC")
        to_zone = tz.gettz(local_timezone)
        utc_time_object = utc_time
        utc_time_object.replace(tzinfo=from_zone)
        local_time = utc_time_object.astimezone(to_zone)
        return local_time

    def convert_string_exlude_date_to_datetime(self, exlude_dates: list[str]) -> list:
        """converts the str type list objects provided to the calculate function
        into a set of pendulum date objects and returns them

        Args:
            exlude_dates (list[str]): List of Str date objects. IE: ["2023-10-02"]

        Returns:
            list: A list of pendulum.DateTime objects
        """
        converted_date_list = []
        for date in exlude_dates:
            converted_date_list.append(pendulum.parse(date).to_date_string())  # type: ignore
        return converted_date_list

    def convert_sla_time_to_mins(self, sla_time: int, sla_type: str) -> int:
        """Converts sla[hours, days, weeks] into minutes

        Args:
            sla_time (int): base time number to convert
            sla_type (str): base type. Must be ("hours", "days", "weeks")

        Returns:
            int: sla timeframe in minutes
        """
        sla_mins = 0
        if sla_type == "hours":
            sla_mins = sla_time * 60  # Convert hours to minutes, ensuring int result
        elif sla_type == "days":
            sla_mins = sla_time * 24 * 60  # Convert days to minutes
        elif sla_type == "weeks":
            sla_mins = sla_time * 7 * 24 * 60  # Convert weeks to minutes
        return int(sla_mins)

    def exclude_custom_dates(self, start_time: pendulum.DateTime) -> pendulum.DateTime:
        """Helper function to check currently supplied date against a
        list of excluded dates for sla calculations

        Args:
            start_time (pendulum.DateTime): Current DateTime object

        Raises:
            ValueError: If not a list, throw value error

        Returns:
            pendulum.DateTime: Re-calculated DateTime object, adjusted for any dates skipped
        """
        if not self.excluded_dates:
            return start_time
        if not isinstance(self.excluded_dates, list):
            raise InvalidCustomDateList("Exclude dates must be in list form with string dates in format 'YYYY-MM-DD")
        for custom_date in self.excluded_dates:
            self.validate_excluded_date(excluded_date=custom_date)
        exlude_date_list: list = self.convert_string_exlude_date_to_datetime(exlude_dates=self.excluded_dates)
        if (
            pendulum.date(year=start_time.year, month=start_time.month, day=start_time.day).to_date_string()
            in exlude_date_list
        ):
            return start_time.add(days=1)
        return start_time

    def validate_excluded_date(self, excluded_date: str) -> None:
        """
        Checks the ecluded date objects for validity.

        Args:
            excluded_date (str): Custom date str

        Raises:
            InvalidDateObject: Raised if date object is invalid.
        """
        try:
            datetime.strptime(excluded_date, "%Y-%m-%d")
        except ValueError:
            raise InvalidDateObject(
                f"The date {excluded_date}, is not formatted properly. It should be formatted as such: 'YYYY-MM-DD'"
            )
