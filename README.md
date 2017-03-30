teambot
=======

[![Build Status](https://travis-ci.org/tdeck/teambot.svg?branch=master)](https://travis-ci.org/tdeck/teambot)

A bot to create per-channel notification lists in Slack.

At Square, we have a lot of teams that make heavy use of slack. Each team owns a few different services, so people might hang around in the team's channel to get updates or ask questions. However, this makes it difficult to use @channel or @here to contact just your team.
By setting up teambot as a bot whose name is "team", you can notify your team with @team.

Teambot is my personal project. **We have been using it at Square for over a year. At last count, 90 different team channels are using teambot.** Despite its simplicity, it has only broken once during a slack outage. I tend to just forget it's running.

Setting up the bot
------------------
Teambot requires Python and virtualenv.

1. Install the bot and its dependencies:
```shell
$ git clone https://github.com/tdeck/teambot.git
$ cd teambot
$ pip env
$ . env/bin/activate
$ pip install -r requirements.txt
```
2. Obtain a token for your slack bot (see the [Slack documentation](https://api.slack.com/getting-started)). I recommend naming it "team".
3. You can configure the bot in one of two ways:

    i. Specify configuration in the environment. At a minimum, you'll need to set the env var `SLACK_TOKEN`. See the section below for more details.

    ii. Provide a configuration file with the slack token. If the file `rtmbot.conf` is present in the working directory, teambot will use that. Or you can specify a different configuration file with the `--config` option. One simple way is to `cp rtmbot.conf.example rtmbot.conf`, then edit rtmbot.conf and replace `<your-token-here>` with the bot's token from your Slack dashboard.

4. That's it. Start the bot with `python rtmbot.py`.

*NOTE*: Teambot will store its directory in a file called `teams.db` in the working directory from which it was run. You can use a different path by providing it in `TEAM_DB_FILE`.

More on configuration
---------------------
Teambot takes the following configuration options, either from the environment or from a configuration file. The configuration file is in YAML format, although for historical reasons its default name is "rtmbot.conf".

`SLACK_TOKEN` (required) - The token used to connect to your Slack team.

`DAEMON` (optional) - When true, teambot will run as a daemon in the background.

`DEBUG` (optional) - When true, teambot will log more debugging information about what it's doing.

`LOGFILE` (optional) - When logging debug details, teambot will log to this file if provided

`TEAM_DB_FILE` (optional) - Teambot will persist its directory in this file. If absent, it will use `teams.db` in the working directory.

If both the file and environment variables are present, the environment variables take precedence. Boolean flags `DAEMON` and `DEBUG` will should be set to the string `true` to enable them.

Setting up a team
-----------------
Team management is simple, and anyone can do it by direct-messaging @team in slack. The bot has a built in help, but here's a quick start guide. Let's imagine that you want to create a team for the #xp channel with a bunch of people. Just run these commands:

```
/join #xp
/invite @team
/msg @team create #xp @jackson @amberdixon @tp @bhartard @dan @killpack @glenn @scottsilver @jess @tdeck @barlow
```

Then Curtis, a new intern, joins your XP team. You can either ask him to run `/msg @team join #xp`, or run `/msg @team add #xp @curtisf`.

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
