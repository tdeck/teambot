teambot
=======
A bot to help team-based Slack channels.

Have you ever:
- Wanted to notify your team in your Slack channel without pinging the other 80 people hanging out in your room?
- Wanted to get help in another team's channel and not known who to ask?

Teambot is here to help. It allows you to designate a core group of people for each channel that corresponds to that channel's team. Then, when you add @team to a message in that channel, teambot will post a notification to those people. This is a simple but useful feature that's missing from vanilla Slack.

Setting up a team
-----------------
Team management is simple, and anyone can do it by direct-messaging @team in slack. The bot has a built in help, but here's a quick start guide. Let's imagine that you want to create a team for the #xp channel with a bunch of people. Just run these commands:

```
/join #xp
/invite @team
/msg @team create #xp @jackson @amberdixon @tp @bhartard @dan @killpack @glenn @scottsilver @jess @tdeck @barlow
```

Then Curtis, a new intern, joins your XP. You can either ask him to run `/msg @team join #xp`, or run `/msg @team add #xp @curtisf`.

Similarly, if Jess gets tired of being notified about every deploy, she can `/msg @team leave #xp`, or you can take her off the list with `/msg @team remove #xp @jess`.

All the commands
----------------
- **info** - gets the team list for a channel:
```info #xp```
- **create** - creates a new team for a channel and optionally adds people to the list:
```create #xp @killpack @amberdixon @tp @dneighman```
- **add** - adds one or more people to a team list
```add #xp @tdeck```
- **remove** - removes one or more people from a team list
```remove #xp @dneighman```
- **join** - adds you to a channel's team
```join #xp```
- **leave** - removes you from a channel's team
```leave #xp```
- **drop** - deletes the team list for a channel
```drop #foundation-server``` - *don't drop teams you weren't on*
