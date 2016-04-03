# This file contains the actual app logic for teambot. The rtmbot
# framework calls into it by invoking setup() and process_message(),
# and will send any messages queued up in the outputs list.

import shelve
import re
import json
import atexit

# This directory maps slack channel IDs (not names) to sets of user IDs
directory = shelve.open('teams.db')

outputs = []
my_name = None
my_user_id = None
slack_client = None

def setup(bot):
    global my_name
    global my_user_id
    global slack_client
    slack_client = bot.slack_client

    my_user_id = slack_client.server.login_data['self']['id']
    my_name = slack_client.server.login_data['self']['name']

def process_message(data):
    # Ignore joins, leaves, typing notifications, etc... and messages from me
    if 'subtype' in data or data['user'] == my_user_id:
        return

    channel_id = data['channel']
    channel_tag = channel_id[0]
    if channel_tag == 'C': # 'C' indicates a message in a normal channel
        handle_channel_message(channel_id, data)
    elif channel_tag == 'D': # 'D' indicates a message in an IM channel
        handle_direct_message(channel_id, data)

def handle_direct_message(dm_channel_id, data):
    text = data['text'].strip()
    if text == 'help':
        return send_help_text(dm_channel_id)
    elif text == 'stats':
        user_count = len(set((uid for uids in directory.values() for uid in uids)))
        return send(dm_channel_id, '{} distinct users in {} teams'.format(user_count, len(directory)))
    elif text == 'list-all':
        return send(dm_channel_id,
            "\n".join(
                (
                    '<#{}>: {}'.format(channel, ' <@{}>' * len(team_members)).format(*team_members)
                    for channel, team_members in directory.iteritems()
                )
            )
        )

    # Accept messages of the form "command #channel [@user...]"
    match = re.match('^(?P<cmd>\w+)\s+<#(?P<channel>C\w+)>(?P<people>(\s+<@U\w+>)*)$', text)
    if not match:
        send(dm_channel_id, "I didn't recognize that command.")
        send_help_text(dm_channel_id)
        return

    groups = match.groupdict()

    cmd = groups['cmd']
    team_channel_id = str(groups['channel'])
    people = set()
    if groups['people']:
        people = set(re.findall('<@(\w+)>', groups['people']))

    team_members = directory.get(team_channel_id)

    if cmd == 'info':
        if team_members is None:
            return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

        send(
            dm_channel_id,
            'Team members for <#{0}>:'.format(team_channel_id) +
                (' <@{}>' * len(team_members)).format(*team_members)
        )

    else:
        if not in_channel(team_channel_id):
            # TODO just join the channel if Slack ever allows it
            return send(
                dm_channel_id,
                'You must invite <@{}> to <#{}> before you can manage team records.'.format(
                    my_user_id,
                    team_channel_id
                )
            )

        if cmd == 'create':
            if team_members is not None:
                return send(dm_channel_id, 'That team already exists.')

            directory[team_channel_id] = people
            directory.sync()

            send(dm_channel_id, 'Team <#{}> created.'.format(team_channel_id))

        elif cmd == 'add':
            if team_members is None:
                return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

            directory[team_channel_id] = team_members | people
            directory.sync()

            send(dm_channel_id, 'Team <#{}> updated.'.format(team_channel_id))

        elif cmd == 'join':
            if team_members is None:
                return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

            team_members.add(data['user'])
            directory[team_channel_id] = team_members
            directory.sync()

            send(dm_channel_id, 'Team <#{}> updated.'.format(team_channel_id))

        elif cmd == 'remove':
            if team_members is None:
                return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

            directory[team_channel_id] = team_members.difference(people)
            directory.sync()

            send(dm_channel_id, 'Team <#{}> updated.'.format(team_channel_id))

        elif cmd == 'leave':
            if team_members is None:
                return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

            team_members.discard(data['user'])
            directory[team_channel_id] = team_members
            directory.sync()

            send(dm_channel_id, 'Team <#{}> updated.'.format(team_channel_id))

        elif cmd == 'drop':
            if team_members is None:
                return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

            del directory[team_channel_id]
            directory.sync()

            send(dm_channel_id, 'Team <#{}> deleted.'.format(team_channel_id))

        else:
            send(dm_channel_id, "I didn't recognize that command.")
            send_help_text(dm_channel_id)

def handle_channel_message(channel_id, data):
    text = data['text']

    if mentions_me(text):
        # Sanity check; in case they haven't created a team
        if str(channel_id) not in directory:
            send(channel_id,
                "There is no team record for this channel.\n" +
                'PM `help` to <@{}> for more information.'.format(my_user_id)
            )
            return

        team_members = directory[str(channel_id)] - set([data['user']])
        send(
            channel_id,
            '^' + (' <@{}>' * len(team_members)).format(*team_members)
        )

def in_channel(channel_id):
    channel_info = slack_client.api_call('channels.info', channel=channel_id)
    return my_user_id in channel_info['channel']['members']

def mentions_me(message_text):
    # Some clients (i.e. slackbot) appear to format the mentions as
    # "<@USERID|username>" rather than "<@USERID>"
    return (
        '<@{}>'.format(my_user_id) in message_text or
        ('<@{}|{}>'.format(my_user_id, my_name) in message_text)
    )

def send(channel_id, message):
    outputs.append([channel_id, message])

def send_help_text(channel_id):
    send(channel_id, HELP_TEXT)

atexit.register(directory.close)

HELP_TEXT = \
'''Here are the commands I understand:
```
info #channel                           - get team info about #channel
create #channel @person1 @person2...    - create a team for #channel and add @person1 and @person2
add #channel @person3 @person4...       - add @person3 and @person4 to the team for #channel
remove #channel @person1 @person2...    - remove @person1 and @person2 from the team for #channel
join #channel                           - add yourself to the team for #channel
leave #channel                          - remove yourself from the team for #channel
drop #channel                           - drop the team record for #channel
list-all                                - list all registered teams
stats                                   - get slackbot team statistics
help                                    - this help```'''
