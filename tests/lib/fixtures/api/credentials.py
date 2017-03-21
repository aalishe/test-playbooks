import os

from towerkit.config import config
import fauxfactory
import pytest


fixtures_dir = os.path.dirname(__file__)


@pytest.fixture(scope="function")
def credential_kind_choices(authtoken, api_credentials_pg):
    """Return supported credential kinds"""
    return dict(api_credentials_pg.options().actions.POST.kind.choices)


# SSH machine credentials
@pytest.fixture(scope="function")
def ssh_credential(admin_user, factories):
    cred = factories.credential(description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=None, become_password=None)
    return cred


@pytest.fixture(scope="function")
def another_ssh_credential(admin_user, factories):
    cred = factories.credential(description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=None, become_password=None)
    return cred


@pytest.fixture(scope="function")
def ssh_credential_ask(admin_user, factories):
    """Create ssh credential with 'ASK' password"""
    cred = factories.credential(description="machine credential with ASK password - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, password='ASK', become_password=None,
                                ssh_key_data=None)
    return cred


@pytest.fixture(scope="function")
def ssh_credential_with_ssh_key_data_and_sudo(ansible_facts, admin_user, factories):
    """Create ssh credential with sudo user from ansible facts"""
    sudo_user = ansible_facts.values()[0]['ansible_facts']['ansible_env']['SUDO_USER']
    cred = factories.credential(kind='ssh', user=admin_user, username=sudo_user, become_method="sudo", password=None,
                                become_password=None)
    return cred


@pytest.fixture(scope="function", params=['sudo', 'su', 'pbrun', 'pfexec', 'dzdo'])
def ssh_credential_multi_ask(request, admin_user, factories):
    """Create ssh credential with multiple 'ASK' passwords"""
    if request.param not in ('sudo', 'su', 'pbrun', 'pfexec', 'dzdo'):
        raise Exception("Unsupported parameter value: %s" % request.param)

    cred = factories.credential(description="machine credential with mulit-ASK password - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, password='ASK', ssh_key_unlock='ASK',
                                ssh_key_data=config.credentials.ssh.encrypted.ssh_key_data, vault_password='ASK',
                                become_method=request.param, become_password='ASK')
    return cred


@pytest.fixture(scope="function")
def team_ssh_credential(team_with_org_admin, factories):
    cred = factories.credential(description="machine credential for team:%s" % team_with_org_admin.name,
                                kind='ssh', team=team_with_org_admin, ssh_key_data=None, become_password=None)
    return cred


# SSH machine credentials with different types of ssh_key_data
# Passphrases for all encrypted keys is "fo0m4nchU"
@pytest.fixture
def unencrypted_rsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/unencrypted_rsa'), 'r').read()


@pytest.fixture(scope="function")
def unencrypted_rsa_ssh_credential(admin_user, unencrypted_rsa_ssh_key_data, factories):
    cred = factories.credential(name="unencrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=unencrypted_rsa_ssh_key_data,
                                password=None, become_password=None)
    return cred


@pytest.fixture
def encrypted_rsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/encrypted_rsa'), 'r').read()


@pytest.fixture(scope="function")
def encrypted_rsa_ssh_credential(admin_user, encrypted_rsa_ssh_key_data, factories):
    cred = factories.credential(name="encrypted rsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_rsa_ssh_key_data,
                                ssh_key_unlock='ASK', password=None, become_password=None)
    return cred


@pytest.fixture
def unencrypted_dsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/unencrypted_dsa'), 'r').read()


@pytest.fixture(scope="function")
def unencrypted_dsa_ssh_credential(admin_user, unencrypted_dsa_ssh_key_data, factories):
    cred = factories.credential(name="unencrypted dsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=unencrypted_dsa_ssh_key_data,
                                password=None, become_password=None)

    return cred


@pytest.fixture
def encrypted_dsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/encrypted_dsa'), 'r').read()


@pytest.fixture(scope="function")
def encrypted_dsa_ssh_credential(admin_user, encrypted_dsa_ssh_key_data, factories):
    cred = factories.credential(name="encrypted dsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_dsa_ssh_key_data,
                                ssh_key_unlock='ASK', password=None, become_password=None)
    return cred


@pytest.fixture
def unencrypted_ecdsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/unencrypted_ecdsa'), 'r').read()


@pytest.fixture(scope="function")
def unencrypted_ecdsa_ssh_credential(admin_user, unencrypted_ecdsa_ssh_key_data, factories):
    cred = factories.credential(name="unencrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=unencrypted_ecdsa_ssh_key_data,
                                password=None, become_password=None)
    return cred


@pytest.fixture
def encrypted_ecdsa_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/encrypted_ecdsa'), 'r').read()


@pytest.fixture(scope="function")
def encrypted_ecdsa_ssh_credential(admin_user, encrypted_ecdsa_ssh_key_data, factories):
    cred = factories.credential(name="encrypted ecdsa ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_ecdsa_ssh_key_data,
                                ssh_key_unlock='ASK', password=None, become_password=None)

    return cred


@pytest.fixture
def unencrypted_open_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/unencrypted_open_rsa'), 'r').read()


@pytest.fixture(scope="function")
def unencrypted_open_ssh_credential(admin_user, unencrypted_open_ssh_key_data, factories):
    cred = factories.credential(name="unencrypted open ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=unencrypted_open_ssh_key_data,
                                password=None, become_password=None)
    return cred


@pytest.fixture
def encrypted_open_ssh_key_data():
    return open(os.path.join(fixtures_dir, 'static/encrypted_open_rsa'), 'r').read()


@pytest.fixture(scope="function")
def encrypted_open_ssh_credential(admin_user, encrypted_open_ssh_key_data, factories):
    cred = factories.credential(name="encrypted open ssh_credentials-%s" % fauxfactory.gen_utf8(),
                                description="machine credential - %s" % fauxfactory.gen_utf8(),
                                kind='ssh', user=admin_user, ssh_key_data=encrypted_open_ssh_key_data,
                                ssh_key_unlock='ASK', password=None, become_password=None)
    return cred


# Convenience fixture that iterates through ssh credentials
ssh_credential_params = ['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open',
                         'encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open']


@pytest.fixture(
    scope="function",
    params=ssh_credential_params,
    ids=ssh_credential_params,
)
def ssh_credential_with_ssh_key_data(request, params=ssh_credential_params):
    return (request.param, request.getfuncargvalue(request.param + '_ssh_credential'))


# Convenience fixture that iterates through unencrypted ssh credentials
unencrypted_ssh_credential_params = ['unencrypted_rsa', 'unencrypted_dsa', 'unencrypted_ecdsa', 'unencrypted_open']


@pytest.fixture(
    scope="function",
    params=unencrypted_ssh_credential_params,
    ids=unencrypted_ssh_credential_params,
)
@pytest.fixture(scope="function", params=unencrypted_ssh_credential_params)
def unencrypted_ssh_credential_with_ssh_key_data(request):
    return (request.param, request.getfuncargvalue(request.param + '_ssh_credential'))


# Convenience fixture that iterates through encrypted ssh credentials
encrypted_ssh_credential_params = ['encrypted_rsa', 'encrypted_dsa', 'encrypted_ecdsa', 'encrypted_open']


@pytest.fixture(
    scope="function",
    params=encrypted_ssh_credential_params,
    ids=encrypted_ssh_credential_params,
)
@pytest.fixture(scope="function", params=encrypted_ssh_credential_params)
def encrypted_ssh_credential_with_ssh_key_data(request):
    return (request.param, request.getfuncargvalue(request.param + '_ssh_credential'))


# Network credentials
@pytest.fixture(scope="function")
def network_credential_with_basic_auth(admin_user, factories):
    cred = factories.credential(name="network credentials-%s" % fauxfactory.gen_utf8(),
                                description="network credential - %s" % fauxfactory.gen_utf8(),
                                kind='net', user=admin_user, ssh_key_data=None, authorize_password=None)
    return cred


@pytest.fixture(scope="function")
def network_credential_with_authorize(admin_user, factories):
    cred = factories.credential(name="network credentials-%s" % fauxfactory.gen_utf8(),
                                description="network credential - %s" % fauxfactory.gen_utf8(),
                                kind='net', user=admin_user, ssh_key_data=None)
    return cred


@pytest.fixture(scope="function")
def network_credential_with_ssh_key_data(admin_user, factories):
    cred = factories.credential(name="network credentials-%s" % fauxfactory.gen_utf8(),
                                description="network credential - %s" % fauxfactory.gen_utf8(),
                                kind='net', user=admin_user, password=None, authorize_password=None)
    return cred


# Convenience fixture that iterates through network credentials
@pytest.fixture(scope="function", params=['network_credential_with_basic_auth',
                                          'network_credential_with_authorize',
                                          'network_credential_with_ssh_key_data'])
def network_credential(request):
    return request.getfuncargvalue(request.param)


# SCM credentials
@pytest.fixture(scope="function")
def unencrypted_scm_credential(admin_user, factories):
    cred = factories.credential(name="scm credentials-%s" % fauxfactory.gen_utf8(),
                                description="unencrypted scm credential - %s" % fauxfactory.gen_utf8(),
                                kind='scm', user=admin_user, password=None)
    return cred


@pytest.fixture(scope="function")
def encrypted_scm_credential(admin_user, factories):
    cred = factories.credential(name="scm credentials-%s" % fauxfactory.gen_utf8(),
                                description="encrypted scm credential - %s" % fauxfactory.gen_utf8(),
                                kind='scm', user=admin_user, ssh_key_data=config.credentials.scm.encrypted.ssh_key_data,
                                ssh_key_unlock=config.credentials.scm.encrypted.ssh_key_unlock, password=None)
    return cred


@pytest.fixture(scope="function")
def scm_credential_key_unlock_ASK(admin_user, factories):
    cred = factories.credential(name="scm credentials-%s" % fauxfactory.gen_utf8(),
                                description="SCM credential %s (scm_key_unlock:ASK)" % fauxfactory.gen_utf8(),
                                kind='scm', ssh_key_data=config.credentials.scm.encrypted.ssh_key_data,
                                scm_key_unlock='ASK', user=admin_user, password=None)
    return cred


# Cloud credentials
@pytest.fixture(scope="function")
def aws_credential(admin_user, factories):
    cred = factories.credential(name="awx-credential-%s" % fauxfactory.gen_utf8(),
                                description="AWS credential %s" % fauxfactory.gen_utf8(),
                                kind='aws', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def rax_credential(admin_user, factories):
    cred = factories.credential(name="rax-credential-%s" % fauxfactory.gen_utf8(),
                                description="Rackspace credential %s" % fauxfactory.gen_utf8(),
                                kind='rax', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def azure_classic_credential(admin_user, factories):
    cred = factories.credential(name="azure-classic-credential-%s" % fauxfactory.gen_utf8(),
                                description="Microsoft Azure credential %s" % fauxfactory.gen_utf8(),
                                kind='azure_classic', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def azure_credential(admin_user, factories):
    cred = factories.credential(name="azure-credential-%s" % fauxfactory.gen_utf8(),
                                description="Microsoft Azure credential %s" % fauxfactory.gen_utf8(),
                                kind='azure_rm', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def azure_ad_credential(admin_user, factories):
    cred = factories.credential(name="azure-ad-credential-%s" % fauxfactory.gen_utf8(),
                                description="Microsoft Azure credential %s" % fauxfactory.gen_utf8(),
                                kind='azure_ad', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def gce_credential(admin_user, factories):
    cred = factories.credential(name="gce-credential-%s" % fauxfactory.gen_utf8(),
                                description="Google Compute Engine credential %s" % fauxfactory.gen_utf8(),
                                kind='gce', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def vmware_credential(admin_user, factories):
    cred = factories.credential(name="vmware-credential-%s" % fauxfactory.gen_utf8(),
                                description="VMware vCenter credential %s" % fauxfactory.gen_utf8(),
                                kind='vmware', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def openstack_v2_credential(admin_user, factories):
    cred = factories.credential(name="openstack-v2-credential-%s" % fauxfactory.gen_utf8(),
                                description="OpenStack credential %s" % fauxfactory.gen_utf8(),
                                kind='openstack_v2', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def openstack_v3_credential(admin_user, factories):
    cred = factories.credential(name="openstack-v3-credential-%s" % fauxfactory.gen_utf8(),
                                description="OpenStack credential %s" % fauxfactory.gen_utf8(),
                                kind='openstack_v3', user=admin_user)
    return cred


# Convenience fixture that iterates through OpenStack credentials
@pytest.fixture(scope="function", params=['openstack_v2', 'openstack_v3'])
def openstack_credential(request):
    return request.getfuncargvalue(request.param + '_credential')


@pytest.fixture(scope="function")
def cloudforms_credential(admin_user, factories):
    cred = factories.credential(name="cloudforms-credentials-%s" % fauxfactory.gen_utf8(),
                                description="CloudForms credential - %s" % fauxfactory.gen_utf8(),
                                kind='cloudforms', user=admin_user)
    return cred


@pytest.fixture(scope="function")
def satellite6_credential(admin_user, factories):
    cred = factories.credential(name="satellite6-credentials-%s" % fauxfactory.gen_utf8(),
                                description="Satellite6 credential - %s" % fauxfactory.gen_utf8(),
                                kind='satellite6', user=admin_user)
    return cred


# Convenience fixture that iterates through supported cloud_credential types
@pytest.fixture(scope="function", params=['aws', 'rax', 'azure_classic', 'azure', 'azure_ad', 'gce', 'vmware',
                                          'openstack_v2', 'openstack_v3', 'cloudforms', 'satellite6'])
def cloud_credential(request, ansible_os_family, ansible_distribution_major_version):
    if (ansible_os_family == 'RedHat' and ansible_distribution_major_version == '6' and
            request.param in ['azure', 'azure_ad']):
        pytest.skip("Inventory import %s not unsupported on EL6 platforms." % request.param)

    return request.getfuncargvalue(request.param + '_credential')
