import shelve
import re
import textwrap

# This directory maps slack channel IDs (not names) to sets of user IDs 
directory = shelve.open('teams.db')

outputs = []
my_user_id = u'U076D8856'
my_mention = '<@{}>'.format(my_user_id)

def setup():
    # TODO get my user ID

    for channel_id in directory.keys():
        join_channel(channel_id)

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
    text = data['text']
    if text.strip() == 'help':
        return send_help_text(dm_channel_id)

    # Accept messages of the form "command #channel [@user...]"
    match = re.match('\s*(?P<cmd>\w+)\s+<#(?P<channel>C\w+)>(?P<people>(\s+<@U\w+>)*)\s*', text)
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

    elif cmd == 'create':
        if team_members is not None:
            return send(dm_channel_id, 'That team already exists.')

        directory[team_channel_id] = people
        # TODO join the channel

        send(dm_channel_id, 'Team <#{}> created.'.format(team_channel_id))

    elif cmd == 'add':
        if team_members is None:
            return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

        directory[team_channel_id] = team_members | people

        send(dm_channel_id, 'Team <#{}> updated.'.format(team_channel_id))

    elif cmd == 'join':
        if team_members is None:
            return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

        team_members.add(data['user'])
        directory[team_channel_id] = team_members

        send(dm_channel_id, 'Team <#{}> updated.'.format(team_channel_id))

    elif cmd == 'remove':
        if team_members is None:
            return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

        directory[team_channel_id] = team_members.difference(people)

        send(dm_channel_id, 'Team <#{}> updated.'.format(team_channel_id))

    elif cmd == 'leave':
        if team_members is None:
            return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

        team_members.discard(data['user'])
        directory[team_channel_id] = team_members

        send(dm_channel_id, 'Team <#{}> updated.'.format(team_channel_id))

    elif cmd == 'drop':
        if team_members is None:
            return send(dm_channel_id, 'No team record for <#{}>'.format(team_channel_id))

        del directory[team_channel_id] 

        send(dm_channel_id, 'Team <#{}> deleted.'.format(team_channel_id))

    else:
        send(dm_channel_id, "I didn't recognize that command.")
        send_help_text(dm_channel_id)

def handle_channel_message(channel_id, data):
    text = data['text']

    if my_mention in text and str(channel_id) in directory:
        team_members = directory[str(channel_id)]
        send(
            channel_id,
            '^' + (' <@{}>' * len(team_members)).format(*team_members)
        )

def join_channel(channel_id):
    

def send(channel_id, message):
    outputs.append([channel_id, message])

def send_help_text(channel_id):
    send(channel_id, HELP_TEXT)

HELP_TEXT = \
'''Here are the commands I understand:
```
info #channel                           - get team info about #channel
create #channel [@person1 @person2...]  - create a team for #channel and add @person1 and @person2
add #channel [@person3 @person4...]     - add @person3 and @person4 to the team for #channel
remove #channel [@person1 @person2...]  - remove @person1 and @person2 from the team for #channel
join #channel                           - add yourself to the team for #channel
leave #channel                          - remove yourself from the team for #channel
drop #channel                           - drop the team record for #channel```'''
