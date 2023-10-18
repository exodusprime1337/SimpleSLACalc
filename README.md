# Simple SLA Calculator
A very simple and rudimentary SLA timeframe calculator. 

## Installation
NOTE: While in the test repository, required packages may not be available. 
```
pip install -i https://test.pypi.org/simple/ SimpleSLACalc==0.0.1
```
## Usage
To calculate and SLA you need to provide a minimum set of parameters. 
- start_time (datetime | pendulum.DateTime | str): Start of sla time calculation(IE: "2023-10-01") or a datetime object
- open_hour (int): Start of business hour(24h format)
- close_hour (int): End of business hour(24h format)
- time_zone (str): Timezone in which to process calculation
- sla_hours (Optional[int], optional): Provide hours to calculate SLA in hours. Defaults to None.
- sla_days (Optional[int], optional): Provide days to calculate SLA in days. Defaults to None.
- sla_weeks (Optional[int], optional): Provide weeks to calculate SLA in weeks. Defaults to None.

**NOTE: Only provide one sla_hours, sla_days, or sla_weeks. Do not combine**

Additionally you can provide a number of optional parmeters to fine tune your SLA calculations. 
Most notable here is **skip_business_hours**. By default business hours are ignored. It will return only the raw SLA calculation including weekends, and holidays. To only calculate business hours SLA's, set to False.
- skip_business_hours (Optional[bool]): When True, skips business hours, and just calculates raw SLA. Defaults to True.
- excluded_dates (Optional[list[str]], optional): Provide a list of dates in string format(IE: ["2023-10-1", 2023-10-02"]). Defaults to None.
- holiday_country (Optional[str], optional): Two character country code for holiday parsing. Required for holiday date SLA exclusion. Defaults to None.
- holiday_state (Optional[str], optional): Optional two character state for holiday date SLA exclusion. Defaults to None.
- holiday_province (Optional[str], optional): Optional two character province for holiday date SLA exclusion. Defaults to None.
```
from SimpleSLACalc import SLACalculator

my_sla_cal = SLACalculator()
sla_values = my_sla_cal.calculate(
    start_time="2023-10-18 01:27",
    open_hour=9,
    close_hour=17,
    sla_hours=6,
    time_zone="America/Chicago",
    skip_business_hours=False
)

print(sla_values.sla_expiration_time)
```
The output of the above code snippet looks as follows.
```
❯ python tests/test.py
2023-10-18 15:00:00-05:00
```
The output object is a class object named SLAItem with a range of values available for use. It appears like this in code.
```
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
```