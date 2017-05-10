from distutils.version import LooseVersion
import logging
import json

import towerkit.tower.inventory
import towerkit.exceptions
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


class TestJobTemplateCredentials(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

    def test_launch_without_credential(self, job_template_no_credential):
        """Verify the job->launch endpoint does not allow launching a job_template
        that has no associated credential.
        """
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert launch_pg.credential_needed_to_start

        # launch the job_template without providing a credential
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch_pg.post()

    def test_launch_with_credential_in_payload(self, job_template_no_credential, ssh_credential):
        """Verify the job->launch endpoint behaves as expected"""
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert launch_pg.credential_needed_to_start

        # launch the job_template providing the credential in the payload
        payload = dict(credential=ssh_credential.id)
        job_pg = job_template_no_credential.launch(payload).wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

        # assert job is associated with the expected credential
        assert job_pg.credential == ssh_credential.id, \
            "A job_template was launched with a credential in the payload, but" \
            "the launched job does not have the same credential " \
            "(%s != %s)" % (job_pg.credential, ssh_credential.id)

    def test_launch_with_team_credential(self, job_template_no_credential, team_with_org_admin, team_ssh_credential, user_password):
        """Verifies that a team user can use a team credential to launch a job template."""
        team_user = team_with_org_admin.get_related('users').results[0]
        with self.current_user(team_user.username, user_password):
            launch_pg = job_template_no_credential.get_related('launch')

            # assert values on launch resource
            assert not launch_pg.can_start_without_user_input
            assert not launch_pg.ask_variables_on_launch
            assert not launch_pg.passwords_needed_to_start
            assert not launch_pg.variables_needed_to_start
            assert launch_pg.credential_needed_to_start

            # launch the job_template providing the credential in the payload
            payload = dict(credential=team_ssh_credential.id)
            job_pg = job_template_no_credential.launch(payload).wait_until_completed()

            # assert success
            assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

            # assert job is associated with the expected credential
            assert job_pg.credential == team_ssh_credential.id, \
                "A job_template was launched with a credential in the payload, but" \
                "the launched job does not have the same credential " \
                "(%s != %s)" % (job_pg.credential, team_ssh_credential.id)

    def test_launch_with_invalid_credential_in_payload(self, job_template_no_credential):
        """Verify the job->launch endpoint behaves as expected when launched with
        a bogus credential id.
        """
        launch_pg = job_template_no_credential.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert not launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert launch_pg.credential_needed_to_start

        # launch the job_template providing a bogus credential in payload
        for bogus in ['', 'one', 0, False, [], {}]:
            payload = dict(credential=bogus)
            with pytest.raises(towerkit.exceptions.BadRequest):
                job_template_no_credential.launch(payload).wait_until_completed()

    def test_launch_with_ask_credential_and_without_passwords_in_payload(self, job_template_no_credential,
                                                                         ssh_credential_multi_ask):
        """Verify that attempts to launch a JT when providing an ask-credential at launch-time without
        providing the required passwords get rejected.
        """
        launch = job_template_no_credential.related.launch.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert launch.credential_needed_to_start

        # launch the JT providing the credential in the payload, but no passwords_needed_to_start
        payload = dict(credential=ssh_credential_multi_ask.id)
        exc_info = pytest.raises(towerkit.exceptions.BadRequest, launch.post, payload)
        result = exc_info.value[1]

        # assert response includes field: passwords_needed_to_start
        assert 'passwords_needed_to_start' in result, \
            "Unexpected API response: {0}.".format(json.dumps(result))

        # assert expected passwords_needed_to_start value
        assert ssh_credential_multi_ask.expected_passwords_needed_to_start == result['passwords_needed_to_start']

    def test_launch_with_ask_credential_and_with_passwords_in_payload(self, job_template_no_credential,
                                                                      ssh_credential_multi_ask):
        """Verify launching a JT when providing an ask-credential at launch-time with required
        passwords.
        """
        launch = job_template_no_credential.related.launch.get()

        # assert values on launch resource
        assert not launch.can_start_without_user_input
        assert not launch.ask_variables_on_launch
        assert not launch.passwords_needed_to_start
        assert not launch.variables_needed_to_start
        assert launch.credential_needed_to_start

        # build a payload containing the credential and passwords
        payload = dict(credential=ssh_credential_multi_ask.id,
                       ssh_password=self.credentials['ssh']['password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       become_password=self.credentials['ssh']['become_password'])

        # launch JT and assert successful
        job = job_template_no_credential.launch(payload).wait_until_completed()
        assert job.is_successful, "Job unsuccessful - %s" % job

        assert job.credential == ssh_credential_multi_ask.id

    @pytest.mark.ansible_integration
    def test_launch_with_unencrypted_ssh_credential(self, ansible_runner, job_template, unencrypted_ssh_credential_with_ssh_key_data):
        """Launch job template with unencrypted ssh_credential"""
        (credential_type, credential_pg) = unencrypted_ssh_credential_with_ssh_key_data

        job_template.patch(credential=credential_pg.id)

        launch_pg = job_template.get_related('launch')
        assert not launch_pg.passwords_needed_to_start
        job_pg = job_template.launch().wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "unencrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg
            else:
                assert job_pg.status == 'error', "Job did not error as expected - %s" % job_pg
                assert "RuntimeError: It looks like you're trying to use a private key in OpenSSH format" in job_pg.result_traceback, \
                    "Unexpected job_pg.result_traceback when launching a job with a OpenSSH credential: %s." % job_pg.result_traceback

        # assess job launch behavior with other credential types
        else:
            assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    @pytest.mark.ansible_integration
    def test_launch_with_encrypted_ssh_credential(self, ansible_runner, job_template, encrypted_ssh_credential_with_ssh_key_data):
        """Launch job template with encrypted ssh_credential"""
        (credential_type, credential_pg) = encrypted_ssh_credential_with_ssh_key_data

        job_template.patch(credential=credential_pg.id)

        launch_pg = job_template.get_related('launch')
        assert launch_pg.passwords_needed_to_start == [u'ssh_key_unlock']
        payload = dict(ssh_key_unlock="fo0m4nchU")
        job_pg = job_template.launch(payload).wait_until_completed()

        # support for OpenSSH credentials was introduced in OpenSSH 6.5
        if credential_type == "encrypted_open":
            contacted = ansible_runner.command('ssh -V')
            if LooseVersion(contacted.values()[0]['stderr'].split(" ")[0].split("_")[1]) >= LooseVersion("6.5"):
                assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg
            else:
                assert job_pg.status == 'error', "Job did not error as expected - %s" % job_pg
                assert "RuntimeError: It looks like you're trying to use a private key in OpenSSH format" in job_pg.result_traceback, \
                    "Unexpected job_pg.result_traceback when launching a job with a OpenSSH credential: %s." % job_pg.result_traceback

        # assess job launch behavior with other credential types
        else:
            assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_launch_without_passwords_needed_to_start(self, job_template_passwords_needed_to_start):
        """Verify the job->launch endpoint behaves as expected when passwords are needed to start"""
        launch_pg = job_template_passwords_needed_to_start.get_related('launch')

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert expected values in launch_pg.passwords_needed_to_start
        credential = job_template_passwords_needed_to_start.get_related('credential')
        assert credential.expected_passwords_needed_to_start == launch_pg.passwords_needed_to_start

        # launch the job_template without passwords
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch_pg.post()

        # prepare payload with empty passwords
        payload = dict(ssh_password='', ssh_key_unlock='', become_password='')

        # launch the job_template
        with pytest.raises(towerkit.exceptions.BadRequest):
            launch_pg.post(payload)

    def test_launch_with_passwords_needed_to_start(self, job_template_passwords_needed_to_start):
        """Verify the job->launch endpoint behaves as expected when passwords are needed to start"""
        launch_pg = job_template_passwords_needed_to_start.get_related('launch')

        print json.dumps(launch_pg.json, indent=2)

        # assert values on launch resource
        assert not launch_pg.can_start_without_user_input
        assert not launch_pg.ask_variables_on_launch
        assert launch_pg.passwords_needed_to_start
        assert not launch_pg.variables_needed_to_start
        assert not launch_pg.credential_needed_to_start

        # assert expected passwords_needed_to_start
        credential = job_template_passwords_needed_to_start.get_related('credential')
        assert credential.expected_passwords_needed_to_start == launch_pg.passwords_needed_to_start

        # prepare payload with passwords
        payload = dict(ssh_password=self.credentials['ssh']['password'],
                       ssh_key_unlock=self.credentials['ssh']['encrypted']['ssh_key_unlock'],
                       become_password=self.credentials['ssh']['become_password'])

        # launch the job_template
        job_pg = job_template_passwords_needed_to_start.launch(payload).wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg
