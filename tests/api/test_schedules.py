from copy import deepcopy
from dateutil import rrule
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

import pytest
from towerkit import exceptions as exc
from towerkit.rrule import RRule
from towerkit.utils import poll_until, random_title

from tests.api import APITest


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestSchedules(APITest):

    @pytest.fixture(ids=('minutely', 'hourly', 'daily', 'weekly', 'monthly', 'yearly'),
                    params=[('MINUTELY', 'minutes'), ('HOURLY', 'hours'), ('DAILY', 'days'), ('WEEKLY', 'weeks'),
                            ('MONTHLY', 'months'), ('YEARLY', 'years')])
    def immediate_rrule(self, request):
        """Creates an RRule with the next recurrence targeted for 30 seconds from invocation"""
        frequency, kwarg = request.param
        dtstart = datetime.utcnow() + relativedelta(**{kwarg: -1, 'seconds': 30})
        freq = getattr(rrule, frequency)
        return RRule(freq, dtstart=dtstart)

    def minutely_rrule(self, **kwargs):
        return RRule(rrule.MINUTELY, dtstart=datetime.utcnow() + relativedelta(minutes=-1, seconds=+30), **kwargs)

    def strftime(self, dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    def test_new_resources_are_without_schedules(self, v2_unified_job_template):
        assert v2_unified_job_template.related.schedules.get().count == 0

    def test_duplicate_schedules_disallowed(self, v2_unified_job_template):
        schedule = v2_unified_job_template.add_schedule()

        with pytest.raises(exc.Duplicate) as e:
            v2_unified_job_template.add_schedule(name=schedule.name)
        assert e.value[1]['name'] == ['Schedule with this Name already exists.']

    def test_invalid_rrules_are_rejected(self, v2_unified_job_template):
        invalid_rrules = [
            ('', 'This field may not be blank.'),
            ('DTSTART:asdf asdf', 'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('RRULE:asdf asdf', 'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('DTSTART:20030925T104941Z RRULE:', 'INTERVAL required in rrule.'),
            ('DTSTART: RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5',
             'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('DTSTART:20030925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=500;UNTIL=29040925T104941Z',
             'RRULE may not contain both COUNT and UNTIL'),
            ('DTSTART:20030925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5 RRULE:FREQ=WEEKLY;INTERVAL=10;COUNT=1',
             'Multiple RRULE is not supported.'),
            ('DTSTART:20030925T104941Z DTSTART:20130925T104941Z RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5',
             'Multiple DTSTART is not supported.'),
            ('DTSTART:{} RRULE:FREQ=DAILY;INTERVAL=10;COUNT=5'.format(parse('Thu, 25 Sep 2003 10:49:41 -0300')),
             'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('DTSTART:20140331T055000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5',
             'DTSTART cannot be a naive datetime.  Specify ;TZINFO= or YYYYMMDDTHHMMSSZZ.'),
            ('RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5',
             'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('FREQ=MINUTELY;INTERVAL=10;COUNT=5',
             'Valid DTSTART required in rrule. Value should start with: DTSTART:YYYYMMDDTHHMMSSZ'),
            ('DTSTART:20240331T075000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=10000000', 'COUNT > 999 is unsupported.'),
            ('DTSTART;TZID=US-Eastern:19961105T090000 RRULE:FREQ=MINUTELY;INTERVAL=10;COUNT=5',
             'rrule parsing failed validation: Offset must be tzinfo subclass, tz string, or int offset.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=SECONDLY;INTERVAL=1', 'SECONDLY is not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=SECONDLY', 'INTERVAL required in rrule.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYDAY=20MO;INTERVAL=1',
             'BYDAY with numeric prefix not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=MONTHLY;BYMONTHDAY=10,15;INTERVAL=1',
             'Multiple BYMONTHDAYs not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYMONTH=1,2;INTERVAL=1', 'Multiple BYMONTHs not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYYEARDAY=120;INTERVAL=1', 'BYYEARDAY not supported.'),
            ('DTSTART:20140331T055000Z RRULE:FREQ=YEARLY;BYWEEKNO=10;INTERVAL=1', 'BYWEEKNO not supported.')
        ]
        for invalid, expected in invalid_rrules:
            with pytest.raises(exc.BadRequest, message='Failed to raise for invalid rrule "{}"'.format(invalid)) as e:
                v2_unified_job_template.add_schedule(rrule=invalid)
            assert e.value[1].get('rrule', [e.value[1]])[0] == expected

    def test_schedule_basic_integrity(self, v2_unified_job_template):
        if v2_unified_job_template.type in ('job_template', 'workflow_job_template'):
            v2_unified_job_template.ask_variables_on_launch = True
            extra_data = {random_title(): random_title() for _ in range(20)}
        else:
            extra_data = {}
        rule = self.minutely_rrule()
        payload = dict(name=random_title(),
                       description=random_title(),
                       enabled=False,
                       rrule=str(rule),
                       extra_data=extra_data)
        schedule = v2_unified_job_template.related.schedules.post(payload)
        assert schedule.name == payload['name']
        assert schedule.description == payload['description']
        assert schedule.rrule == str(rule)
        assert not schedule.enabled
        assert schedule.extra_data == extra_data

        schedules = v2_unified_job_template.related.schedules.get()
        assert schedules.count == 1
        assert schedules.results.pop().id == schedule.id
        # Confirm basic REST operations are successful
        schedule.put()
        content = deepcopy(schedule.json)
        content['description'] = 'A New Description'
        schedule.put(content)
        assert schedule.get().description == 'A New Description'
        schedule.description = 'Some Other Description'
        assert schedule.get().description == 'Some Other Description'

    def test_only_count_limited_previous_recurrencences_are_evaluated(self, v2_unified_job_template):
        epoch = parse('Jan 1 1970')
        dtend = epoch + relativedelta(years=9)
        rule = RRule(rrule.YEARLY, dtstart=epoch, count=10, interval=1)
        schedule = v2_unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(epoch)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run is None

    def test_only_count_limited_future_recurrences_are_evaluated(self, v2_unified_job_template):
        odyssey_three = parse('Jan 1 2061')
        dtend = odyssey_three + relativedelta(years=9)
        rule = RRule(rrule.YEARLY, dtstart=odyssey_three, count=10, interval=1)
        schedule = v2_unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(odyssey_three)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run == rule.next_run

    def test_only_count_limited_overlapping_recurrences_are_evaluated(self, v2_unified_job_template):
        last_week = datetime.utcnow() + relativedelta(weeks=-1, minutes=+1)
        dtend = datetime.utcnow() + relativedelta(days=2, minutes=+1)
        rule = RRule(rrule.DAILY, dtstart=last_week, count=10)
        schedule = v2_unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(last_week)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run == rule.next_run

    def test_only_until_limited_previous_recurrencences_are_evaluated(self, v2_unified_job_template):
        epoch = parse('Jan 1 1970')
        dtend = epoch + relativedelta(years=9)
        rule = RRule(rrule.YEARLY, dtstart=epoch, until=dtend, interval=1)
        schedule = v2_unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(epoch)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run is None

    def test_only_until_limited_future_recurrences_are_evaluated(self, v2_unified_job_template):
        odyssey_three = parse('Jan 1 2061')
        dtend = odyssey_three + relativedelta(years=9)
        rule = RRule(rrule.YEARLY, dtstart=odyssey_three, until=dtend, interval=1)
        schedule = v2_unified_job_template.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(odyssey_three)
        assert schedule.dtend == self.strftime(dtend)
        assert schedule.next_run == rule.next_run

    def test_only_until_limited_overlapping_recurrences_are_evaluated(self, project):
        last_week = datetime.utcnow() + relativedelta(weeks=-1, minutes=+1)
        next_week = datetime.utcnow() + relativedelta(weeks=+1, minutes=+1)
        rule = RRule(rrule.DAILY, dtstart=last_week, until=next_week)
        schedule = project.add_schedule(rrule=rule)
        assert schedule.dtstart == self.strftime(last_week)
        assert schedule.dtend == self.strftime(next_week)
        assert schedule.next_run == rule.next_run

    def test_expected_fields_are_readonly(self, factories):
        schedule = factories.v2_job_template().add_schedule()
        original_dtstart = schedule.dtstart
        schedule.dtstart = 'Undesired dtstart'
        assert schedule.dtstart == original_dtstart
        original_dtend = schedule.dtend
        schedule.dtend = 'Undesired dtend'
        assert schedule.dtend == original_dtend
        original_next_run = schedule.next_run
        schedule.next_run = 'Undesired next_run'
        assert schedule.next_run == original_next_run
        schedule.json.update(dict(dtstart='Undesired dtstart',
                                  dtend='Undesired dtend',
                                  next_run='Undesired next_run'))
        schedule.put()
        assert schedule.dtstart == original_dtstart
        assert schedule.dtend == original_dtend
        assert schedule.next_run == original_next_run

    def test_successful_schedule_deletions(self, v2_unified_job_template):
        added_schedules = [v2_unified_job_template.add_schedule() for _ in range(5)]
        schedules = v2_unified_job_template.related.schedules.get()
        for _ in range(5):
            assert set([s.id for s in schedules.get().results]) == set([s.id for s in added_schedules])
            added_schedules.pop().delete()
        assert not schedules.get().count
        assert not schedules.results

    def test_successful_cascade_schedule_deletions(self, v2_unified_job_template):
        schedules = [v2_unified_job_template.add_schedule() for _ in range(5)]
        v2_unified_job_template.delete()
        for schedule in schedules:
            with pytest.raises(exc.NotFound):
                schedule.get()

    def test_schedule_triggers_launch_without_count(self, v2_unified_job_template):
        rule = self.minutely_rrule()
        schedule = v2_unified_job_template.add_schedule(rrule=rule)
        assert schedule.next_run == rule.next_run

        unified_jobs = schedule.related.unified_jobs.get()
        poll_until(lambda: unified_jobs.get().count == 1, interval=15, timeout=5 * 60)
        job = unified_jobs.results.pop()
        assert job.wait_until_completed().is_successful
        assert schedule.get().next_run == rule.next_run

    def test_schedule_triggers_launch_with_count(self, v2_unified_job_template):
        rule = self.minutely_rrule(count=2)
        schedule = v2_unified_job_template.add_schedule(rrule=rule)
        assert schedule.next_run == rule.next_run

        unified_jobs = schedule.related.unified_jobs.get()
        poll_until(lambda: unified_jobs.get().count == 1, interval=15, timeout=5 * 60)
        job = unified_jobs.results.pop()
        assert job.wait_until_completed().is_successful
        assert schedule.get().next_run is None


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestSystemJobTemplateSchedules(APITest):

    @pytest.mark.parametrize('name, extra_data',
                             [('Cleanup Job Schedule', dict(days='120')),
                              ('Cleanup Activity Schedule', dict(days='355')),
                              ('Cleanup Fact Schedule', dict(older_than='120d', granularity='1w'))],
                             ids=['Cleanup Job Schedule', 'Cleanup Activity Schedule', 'Cleanup Fact Schedule'])
    def test_default_schedules_are_prepopulated(self, v2, name, extra_data):
        schedules = v2.schedules.get(name=name)
        assert schedules.count == 1
        assert schedules.results.pop().extra_data == extra_data

    def test_sjt_can_have_multiple_schedules(self, request, system_job_template):
        if system_job_template.job_type == 'cleanup_facts':
            extra_data = dict(older_than='120d', granularity='1w')
        else:
            extra_data = dict(days='120')

        schedules = [system_job_template.add_schedule(extra_data=extra_data) for _ in range(5)]

        def teardown():
            for s in schedules:
                s.delete()

        request.addfinalizer(teardown)

        assert system_job_template.related.schedules.get().count == 6
