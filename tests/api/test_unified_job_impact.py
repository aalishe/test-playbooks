from towerkit import utils
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.mp_group('OpenShift', 'serial')
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestUnifiedJobImpact(Base_Api_Test):

    def unified_job_impact(self, unified_job_type, num_hosts=None):
        if unified_job_type in ('inventory_update', 'project_update'):
            return 1
        elif unified_job_type == 'system_job':
            return 5
        else:
            return min(5, num_hosts) + 1

    def assert_instance_reflects_zero_running_jobs(self, instance):
        assert instance.jobs_running == 0
        assert instance.consumed_capacity == 0
        assert instance.percent_capacity_remaining == 100.0

    def assert_instance_group_reflects_zero_running_jobs(self, ig):
        assert ig.jobs_running == 0
        assert ig.committed_capacity == 0
        assert ig.consumed_capacity == 0
        assert ig.percent_capacity_remaining == 100.0

    def verify_resource_percent_capacity_remaining(self, resource):
        # works for both instances and instance groups
        expected_percent_remaining = round(100 * (1 - float(resource.consumed_capacity) / resource.capacity), 2)
        assert resource.percent_capacity_remaining == expected_percent_remaining

    @pytest.mark.parametrize('num_hosts', [3, 5, 7])
    def test_job_impact_scales_with_number_of_hosts(self, tower_instance_group, factories, num_hosts):
        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 30}')
        jt.add_instance_group(tower_instance_group)
        instance = tower_instance_group.related.instances.get().results.pop()

        inventory = jt.ds.inventory
        for _ in range(num_hosts):
            factories.v2_host(inventory=inventory)

        self.assert_instance_reflects_zero_running_jobs(instance)
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())

        jt.launch()
        utils.poll_until(lambda: jt.ds.project.related.project_updates.get(status='successful',
                         launch_type='sync').count == 1, interval=5, timeout=60)

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=30)
        assert instance.consumed_capacity == self.unified_job_impact('job', num_hosts)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: tower_instance_group.get().jobs_running == 1, interval=1, timeout=30)
        assert tower_instance_group.consumed_capacity == self.unified_job_impact('ahc', num_hosts)
        self.verify_resource_percent_capacity_remaining(tower_instance_group)

    @pytest.mark.parametrize('num_hosts', [3, 5, 7])
    def test_ahc_impact_scales_with_number_of_hosts(self, tower_instance_group, factories, num_hosts):
        instance = tower_instance_group.related.instances.get().results.pop()
        inventory = factories.v2_inventory()
        inventory.add_instance_group(tower_instance_group)
        for _ in range(num_hosts):
            factories.v2_host(inventory=inventory)

        self.assert_instance_reflects_zero_running_jobs(instance)
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())

        factories.v2_ad_hoc_command(inventory=inventory, module_name='shell', module_args='sleep 30')

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=30)
        assert instance.consumed_capacity == self.unified_job_impact('ahc', num_hosts)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: tower_instance_group.get().jobs_running == 1, interval=1, timeout=30)
        assert tower_instance_group.consumed_capacity == self.unified_job_impact('ahc', num_hosts)
        self.verify_resource_percent_capacity_remaining(tower_instance_group)

    def test_instance_group_updates_for_simultaneous_unified_jobs(self, factories, tower_instance_group):
        instance = tower_instance_group.related.instances.get().results.pop()
        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 30}',
                                       allow_simultaneous=True)
        inventory = jt.ds.inventory
        factories.v2_host(inventory=inventory)

        self.assert_instance_reflects_zero_running_jobs(instance)
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())

        for _ in range(2):
            jt.launch()
        utils.poll_until(lambda: jt.ds.project.related.project_updates.get(status='successful',
                         launch_type='sync').count == 2, interval=5, timeout=60)
        factories.v2_ad_hoc_command(inventory=inventory, module_name='shell', module_args='sleep 30')

        utils.poll_until(lambda: instance.get().jobs_running == 3, interval=1, timeout=30)
        assert instance.consumed_capacity == 2 * self.unified_job_impact('job', 1) + \
                                             self.unified_job_impact('ahc', 1)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: tower_instance_group.get().jobs_running == 3, interval=1, timeout=30)
        assert tower_instance_group.consumed_capacity == 2 * self.unified_job_impact('job', 1) + \
                                                         self.unified_job_impact('ahc', 1)
        self.verify_resource_percent_capacity_remaining(tower_instance_group)

    # FIXME: Tower issue? Only JT IG updates for job, not additional IGs
    def test_all_groups_that_contain_job_execution_node_update_for_running_job(self, factories,
                                                                               tower_instance_group):
        igs = [factories.instance_group() for _ in range(3)]
        instance = tower_instance_group.related.instances.get().results.pop()
        for ig in igs:
            ig.add_instance(instance)

        jt = factories.v2_job_template(playbook='sleep.yml', extra_vars='{"sleep_interval": 30}',
                                       allow_simultaneous=True)
        factories.v2_host(inventory=jt.ds.inventory)

        self.assert_instance_reflects_zero_running_jobs(instance)
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())

        jt.launch()
        utils.poll_until(lambda: jt.ds.project.related.project_updates.get(status='successful',
                         launch_type='sync').count == 1, interval=5, timeout=60)

        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=30)
        assert instance.consumed_capacity == self.unified_job_impact('job', 1)
        self.verify_resource_percent_capacity_remaining(instance)

        utils.poll_until(lambda: tower_instance_group.get().jobs_running == 1, interval=1, timeout=30)
        assert tower_instance_group.consumed_capacity == self.unified_job_impact('job', 1)
        self.verify_resource_percent_capacity_remaining(tower_instance_group)

        for ig in igs:
            utils.poll_until(lambda: ig.get().jobs_running == 1, interval=1, timeout=30)
            assert ig.consumed_capacity == self.unified_job_impact('job', 1)
            self.verify_resource_percent_capacity_remaining(ig)

    def test_project_updates_have_an_impact_of_one(self, factories, tower_instance_group):
        project = factories.v2_project(scm_url='https://github.com/django/django.git', wait=False)
        project_update = project.related.current_job.get()

        instance = tower_instance_group.related.instances.get().results.pop()
        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        utils.poll_until(lambda: instance.get().consumed_capacity == 1, interval=1, timeout=60)
        utils.poll_until(lambda: tower_instance_group.get().jobs_running == 1, interval=1, timeout=60)
        utils.poll_until(lambda: tower_instance_group.get().consumed_capacity == 1, interval=1, timeout=60)

        project_update.wait_until_completed()
        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())

    def test_inventory_updates_have_an_impact_of_one(self, factories, tower_instance_group):
        aws_cred = factories.v2_credential(kind='aws')
        inv_source = factories.v2_inventory_source(source='ec2', credential=aws_cred)
        inv_update = inv_source.update()

        instance = tower_instance_group.related.instances.get().results.pop()
        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        utils.poll_until(lambda: instance.get().consumed_capacity == 1, interval=1, timeout=60)
        utils.poll_until(lambda: tower_instance_group.get().jobs_running == 1, interval=1, timeout=60)
        utils.poll_until(lambda: tower_instance_group.get().consumed_capacity == 1, interval=1, timeout=60)

        inv_update.wait_until_completed()
        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())

    def test_system_jobs_have_an_impact_of_five(self, factories, tower_instance_group,
                                                cleanup_activitystream_template):
        system_job = cleanup_activitystream_template.launch()

        instance = tower_instance_group.related.instances.get().results.pop()
        utils.poll_until(lambda: instance.get().jobs_running == 1, interval=1, timeout=60)
        utils.poll_until(lambda: instance.get().consumed_capacity == 5, interval=1, timeout=60)
        utils.poll_until(lambda: tower_instance_group.get().jobs_running == 1, interval=1, timeout=60)
        utils.poll_until(lambda: tower_instance_group.get().consumed_capacity == 5, interval=1, timeout=60)

        system_job.wait_until_completed()
        self.assert_instance_reflects_zero_running_jobs(instance.get())
        self.assert_instance_group_reflects_zero_running_jobs(tower_instance_group.get())
