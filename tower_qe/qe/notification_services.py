import json
import time
import logging

from slacker import Slacker
from hypchat import HypChat
from gcloud import datastore

log = logging.getLogger(__name__)

# FIXME: General issue - methods may return true if they find
#        test notification from previous test run.
#        Need way to ensure that searches exclude notifications
#        fired before this test run. (Fire off bookmark notification? Use time?)


def confirm_slack_message(testsetup, msg):
    '''Determine if given message is present in slack channel(s). Return True if found.'''
    # TODO: Compare slack history before and after firing notification?
    #      (to ensure that no other notifications were created?)

    # Get slack configuration
    token = testsetup.credentials['notification_services']['slack']['token']
    channels = testsetup.credentials['notification_services']['slack']['channels']

    # Connect
    slack = Slacker(token)

    # Get channel information
    channel_list = slack.channels.list().body['channels']
    channel_mapping = dict((channel['name'], channel['id']) for channel in channel_list)

    # Check each channel
    for channel in channels:
        if channel not in channel_mapping:
            assert False, "Failed to locate slack channel '%s'" % channel
        channel_id = channel_mapping[channel]

        # Locate message
        history = slack.channels.history(channel=channel_id).body['messages']
        for line in history:
            if msg == line['text']:
                return True
    return False


def confirm_hipchat_message(testsetup, msg):
    '''Determine if given message is present in hipchat room(s). Return True if found.'''
    # TODO: Compare hipchat history before and after firing notification?
    #      (to ensure that no other notifications were created?)

    # Get hipchat configuration
    token = testsetup.credentials['notification_services']['hipchat']['user_token']
    rooms = testsetup.credentials['notification_services']['hipchat']['rooms']

    # Connect
    hipchat = HypChat(token)

    # Get room information
    room_list = hipchat.rooms().contents()
    room_mapping = dict((room['name'], room['id']) for room in room_list)

    # Check each room
    for room in rooms:
        if room not in room_mapping:
            assert False, "Failed to locate hipchat room '%s'" % room
        room_id = room_mapping[room]

        # Locate message
        history = hipchat.get_room(room_id).history().contents()
        for line in history:
            if msg == line['message']:
                return True
    return False


def confirm_webhook_message(testsetup, msg):
    '''
    Determine if given message was sent to webservice.

    Both the headers and body of webhook notifications are formatted as json.
    This method takes `msg`, a tuple containing the headers and body expected
    from the webhook payload.
    '''
    # TODO: Compare webservice history before and after firing notification?
    #      (to ensure that no other notifications were created?)

    # TODO: Add support for present argument

    def truncate_time(body, expected_body):
        '''
        (HACK) The time string appears differently in notification message
        and tower api. Truncate the time string (remove microseconds)
        to remove formatting difference.
        '''
        for field in ['started', 'finished']:
            if 'started' in body and 'started' in expected_body:
                body[field] = body[field].split('.')[0]
                expected_body[field] = expected_body[field].split('.')[0]

        return (body, expected_body)

    if type(msg) != tuple or len(msg) != 2:
        raise Exception('Expect tuple containing webhook headers and body (as dictionaries)')
    (expected_headers, expected_body) = (msg[0], msg[1])

    # Get webhook configuration
    # url = testsetup.credentials['notification_services']['webhook']['url']
    gce_project = testsetup.credentials['notification_services']['webhook']['gce_project']
    parent_key = testsetup.credentials['notification_services']['webhook']['gce_parent_key']
    body_field = testsetup.credentials['notification_services']['webhook']['gce_body_field']
    headers_field = testsetup.credentials['notification_services']['webhook']['gce_headers_field']

    # Get list of requests received by server
    client = datastore.Client(project=gce_project)
    query = client.query(kind=parent_key)
    db_results = list(query.fetch())

    # Search for message in history of web requests
    for result in db_results:
        # Sanity check: db record should include field that holds request body
        if not result.get(body_field, ''):
            continue

        # Convert request body to dictionary (by way of json object)
        body_as_dict = json.loads(result.get(body_field))

        # Hack: Time in notification formatted differently
        # than time shown in Tower api. Truncate time
        # to second position to make time formats the same.
        (body_as_dict, expected_body) = truncate_time(body_as_dict, expected_body)

        # Compare request body to expected body
        if body_as_dict != expected_body:
            continue

        # Sanity check: db record should include field that holds headers
        if not result.get(headers_field, ''):
            continue

        # Convert request body to dictionary (by way of json object)
        headers_as_dict = json.loads(result.get(headers_field))

        # Assert headers (note: headers are case-insensitive)
        for exp_key in expected_headers:
            matching_keys = [key for key in headers_as_dict if key.lower() == exp_key.lower()]
            if len(matching_keys) != 1:
                break
            key = matching_keys[0]
            if expected_headers[exp_key] != headers_as_dict[key]:
                break
        else:
            return True  # All expected headers matched

    return False


# TODO: Bit odd to be defining dictionary here
CONFIRM_METHOD = {
    "slack": confirm_slack_message,
    "hipchat": confirm_hipchat_message,
    "webhook": confirm_webhook_message
}


def can_confirm_notification(notification_template_pg):
    '''Determines if notification can be confirmed by this module'''
    return notification_template_pg.notification_type in CONFIRM_METHOD


def confirm_notification(testsetup, notification_template_pg, msg, is_present=True, interval=5, min_polls=2, max_polls=12):
    '''Confirms presence (or absence) of given message in appropriate notification service. Returns True if message is in expected state.'''
    nt_type = notification_template_pg.notification_type
    if not can_confirm_notification(notification_template_pg):
        raise Exception("notification type %s not supported" % nt_type)

    # Poll notification service
    i = 0
    while i < max_polls:
        present = CONFIRM_METHOD[nt_type](testsetup, msg)
        if present:
            break
        i += 1
        if not is_present and i > min_polls:
            break
        log.debug("Sleeping for {}".format(interval))
        time.sleep(interval)
    return present == is_present
