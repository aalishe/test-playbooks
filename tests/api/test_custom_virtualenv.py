from datetime import datetime
from dateutil import rrule
from dateutil.relativedelta import relativedelta

import pytest
from towerkit.exceptions import BadRequest
from towerkit.rrule import RRule
from towerkit.utils import (poll_until, random_title)

from tests.api import APITest
from tests.lib.helpers.workflow_utils import (WorkflowTree, WorkflowTreeMapper)


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.requires_single_instance
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestCustomVirtualenv(APITest):

    @pytest.mark.mp_group('CustomVirtualenv', 'isolated_serial')
    def test_default_venv(self, v2, venv_path):
        assert v2.config.get().custom_virtualenvs == [venv_path()]

    def test_default_venv_can_be_sourced(self, v2, factories, venv_path):
        jt = factories.v2_job_template()
        jt.custom_virtualenv = venv_path()
        job = jt.launch().wait_until_completed()
        job.assert_successful()
        assert job.job_env['VIRTUAL_ENV'] == venv_path()

    def test_cannot_associate_invalid_venv_path_with_resource(self, v2, factories, create_venv, venv_path, get_resource_from_jt):
        folder_names = [random_title(non_ascii=False) for _ in range(2)]
        malformed_venvs = ('foo',
                           '/',
                           '/tmp',
                           '[]',
                           '()',
                           '/var/lib/awx/venv/',
                           '/var/lib /awx/venv/{}/'.format(folder_names[0]),
                           '/var/lib/awx/venv/{}'.format(folder_names[0][:-1]),
                           '/var/lib/awx/venv/{}/foo'.format(folder_names[0]),
                           '/var/lib/awx/venv/{}/foo/'.format(folder_names[0]),
                           folder_names[0],
                           '/{}'.format(folder_names[0]),
                           '/{}/'.format(folder_names[0]),
                           '/var/lib/awx/venv/{}/ /var/lib/awx/venv/{}/'.format(folder_names[0], folder_names[1]),
                           '/var/lib/awx/venv/{} /var/lib/awx/venv/{}'.format(folder_names[0], folder_names[1]),
                           '[/var/lib/awx/venv/{}/, /var/lib/awx/venv/{}/]'.format(folder_names[0], folder_names[1]),
                           '(/var/lib/awx/venv/{}/, /var/lib/awx/venv/{}/)'.format(folder_names[0], folder_names[1]))
        jt = factories.v2_job_template()

        with create_venv(folder_names[0]):
            with create_venv(folder_names[1]):
                poll_until(lambda: all([path in v2.config.get().custom_virtualenvs
                                        for path in (venv_path(folder_names[0]), venv_path(folder_names[1]))]),
                           interval=1, timeout=15)
                for resource_type in ('job_template', 'project', 'organization'):
                    resource = get_resource_from_jt(jt, resource_type)
                    for path in malformed_venvs:
                        with pytest.raises(BadRequest):
                            resource.custom_virtualenv = path

    def test_can_associate_valid_venv_path_with_resource(self, v2, factories, create_venv, venv_path,
                                                         get_resource_from_jt):
        folder_name = random_title(non_ascii=False)
        valid_venvs = ('/var/lib/awx/venv/{}'.format(folder_name),
                       '/var/lib/awx/venv/{}/'.format(folder_name),
                       '')
        jt = factories.v2_job_template()

        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            for resource_type in ('job_template', 'project', 'organization'):
                resource = get_resource_from_jt(jt, resource_type)
                for path in valid_venvs:
                    resource.custom_virtualenv = path

    def test_run_job_using_venv_with_required_packages(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.v2_job_template()
            jt.ds.inventory.add_host()
            assert jt.custom_virtualenv is None
            jt.custom_virtualenv = venv_path(folder_name)
            job = jt.launch().wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'] == venv_path(folder_name)

    @pytest.mark.parametrize('resource_pair', [('organization', 'project'), ('organization', 'job_template'),
                                               ('project', 'job_template')],
                             ids=['org and project', 'org and jt', 'project and jt'])
    def test_venv_resource_hierarchy(self, v2, factories, create_venv, resource_pair, venv_path, get_resource_from_jt):
        folder_names = [random_title(non_ascii=False) for _ in range(2)]
        with create_venv(folder_names[0]):
            with create_venv(folder_names[1]):
                poll_until(lambda: all([path in v2.config.get().custom_virtualenvs
                                        for path in (venv_path(folder_names[0]), venv_path(folder_names[1]))]),
                           interval=1, timeout=15)
                jt = factories.v2_job_template()
                jt.ds.inventory.add_host()

                for i in range(2):
                    resource = get_resource_from_jt(jt, resource_pair[i])
                    assert resource.custom_virtualenv is None
                    resource.custom_virtualenv = venv_path(folder_names[i])

                job = jt.launch().wait_until_completed()
                job.assert_successful()
                assert job.job_env['VIRTUAL_ENV'] == venv_path(folder_names[1])

    @pytest.mark.parametrize('ansible_version', ['2.6.1', '2.5.6', '2.4.6.0', '2.3.3.0', '2.2.3.0'])
    def test_venv_with_ansible(self, v2, factories, create_venv, ansible_version, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name, 'python-memcached psutil ansible=={}'.format(ansible_version)):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.v2_job_template(playbook='run_command.yml', extra_vars='{"command": "ansible --version"}')
            jt.ds.inventory.add_host()
            assert jt.custom_virtualenv is None
            jt.custom_virtualenv = venv_path(folder_name)
            job = jt.launch().wait_until_completed()
            job.assert_successful()
            job_events = job.related.job_events.get().results

            event = [e for e in job_events if e.task == 'command' and e.event == 'runner_on_ok'].pop()
            stdout = event.event_data.res.stdout
            assert 'ansible {}'.format(ansible_version) in stdout

            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'] == venv_path(folder_name)

    def test_venv_with_missing_requirements(self, v2, factories, create_venv, ansible_version, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name, ''):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.v2_job_template()
            jt.ds.inventory.add_host()
            assert jt.custom_virtualenv is None
            jt.custom_virtualenv = venv_path(folder_name)
            job = jt.launch().wait_until_completed()
            assert job.status == 'failed'
            assert job.job_explanation == ''
            possible_error_msgs = ['{0} is missing; /var/lib/awx/venv/{1}/bin/pip install {0}'.format(pkg, folder_name) for pkg in ('psutil', 'python-memcached')]
            assert any(msg in job.result_stdout for msg in possible_error_msgs)

    def test_relaunched_jobs_use_venv_specified_on_jt_at_launch_time(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.v2_job_template()
            jt.ds.inventory.add_host()
            jt.custom_virtualenv = venv_path(folder_name)
            job = jt.launch().wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'] == venv_path(folder_name)

            relaunched_job = job.relaunch().wait_until_completed()
            assert relaunched_job.job_env['VIRTUAL_ENV'] == venv_path(folder_name)

            # Per https://github.com/ansible/tower/issues/2844,
            # venv is a property of the job, not a value in time that is persisted.
            # Relaunched job should source whatever venv is set on the JT at launch time.
            jt.custom_virtualenv = venv_path()
            relaunched_job = job.relaunch().wait_until_completed()
            assert relaunched_job.job_env['VIRTUAL_ENV'] == venv_path()

    def test_relaunched_jobs_fail_when_venv_no_longer_exists(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.v2_job_template()
            jt.ds.inventory.add_host()
            jt.custom_virtualenv = venv_path(folder_name)

        poll_until(lambda: venv_path(folder_name) not in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
        assert jt.get().custom_virtualenv == venv_path(folder_name)
        job = jt.launch().wait_until_completed()
        assert job.status == 'error'
        assert 'RuntimeError: a valid Python virtualenv does not exist at {}'\
               .format(venv_path(folder_name)) in job.result_traceback
        assert job.job_explanation == ''

    def test_workflow_job_node_sources_venv(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.v2_job_template()
            jt.ds.inventory.add_host()
            jt.custom_virtualenv = venv_path(folder_name)

            wfjt = factories.workflow_job_template()
            factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
            wf_job = wfjt.launch().wait_until_completed()
            wf_job.assert_successful()
            wf_job_node = wf_job.related.workflow_nodes.get().results.pop()
            job = wf_job_node.related.job.get()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'] == venv_path(folder_name)

    def test_only_workflow_node_with_custom_venv_sources_venv(self, v2, factories, create_venv, venv_path):
        """Workflow:
         - n1                   <--- default venv
          - (always) n2         <--- custom venv
            - (success) n3      <--- default venv
        """
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.v2_job_template()
            jt.ds.inventory.add_host()
            jt_with_venv = factories.v2_job_template()
            jt_with_venv.ds.inventory.add_host()
            jt_with_venv.custom_virtualenv = venv_path(folder_name)

            wfjt = factories.workflow_job_template()
            n1 = factories.workflow_job_template_node(workflow_job_template=wfjt, unified_job_template=jt)
            n2 = n1.related.always_nodes.post(dict(unified_job_template=jt_with_venv.id))
            n3 = n2.related.success_nodes.post(dict(unified_job_template=jt.id))
            wf_job = wfjt.launch().wait_until_completed()
            wf_job.assert_successful()

            # map nodes to job nodes
            tree = WorkflowTree(wfjt)
            job_tree = WorkflowTree(wf_job)
            mapping = WorkflowTreeMapper(tree, job_tree).map()

            assert mapping, "Failed to map WFJT to WFJ.\n\nWFJT:\n{0}\n\nWFJ:\n{1}".format(tree, job_tree)
            n1_job_node, n2_job_node, n3_job_node = [v2.workflow_job_nodes.get(id=mapping[n.id]).results.pop()
                                                     for n in (n1, n2, n3)]
            n1_job, n2_job, n3_job = [job_node.related.job.get() for job_node in
                                      (n1_job_node, n2_job_node, n3_job_node)]
            all([job.assert_successful()

            assert n1_job.job_env['VIRTUAL_ENV'] == venv_path().rstrip('/')
            assert n2_job.job_env['VIRTUAL_ENV'] == venv_path(folder_name)
            assert n3_job.job_env['VIRTUAL_ENV'] == venv_path().rstrip('/')

    def test_scheduled_job_uses_venv_associated_with_resource(self, v2, factories, create_venv, venv_path):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.v2_job_template()
            jt.ds.inventory.add_host()
            jt.custom_virtualenv = venv_path(folder_name)

            dtstart = datetime.utcnow() + relativedelta(seconds=-30)
            minutely_rrule = RRule(rrule.MINUTELY, dtstart=dtstart)
            schedule = jt.add_schedule(rrule=minutely_rrule)

            unified_jobs = schedule.related.unified_jobs.get()
            poll_until(lambda: unified_jobs.get().count == 1, interval=15, timeout=5 * 60)
            job = unified_jobs.results.pop()
            job.wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'] == venv_path(folder_name)

    @pytest.mark.parametrize('resource_type', ['project', 'job_template'])
    def test_venv_preserved_by_copied_resource(self, v2, factories, create_venv, copy_with_teardown, resource_type,
                                               venv_path, get_resource_from_jt):
        folder_name = random_title(non_ascii=False)
        with create_venv(folder_name):
            poll_until(lambda: venv_path(folder_name) in v2.config.get().custom_virtualenvs, interval=1, timeout=15)
            jt = factories.v2_job_template()
            jt.ds.inventory.add_host()
            resource = get_resource_from_jt(jt, resource_type)
            resource.custom_virtualenv = venv_path(folder_name)

            copied_resource = copy_with_teardown(resource)
            assert copied_resource.custom_virtualenv == venv_path(folder_name)

            if resource_type == 'project':
                update = copied_resource.related.project_updates.get().results.pop()
                update.wait_until_completed().assert_successful()
                jt.project = copied_resource.id
            elif resource_type == 'job_template':
                jt = copied_resource

            job = jt.launch().wait_until_completed()
            job.assert_successful()
            assert job.job_env['VIRTUAL_ENV'] == venv_path(folder_name)
