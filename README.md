<div align="center">
  <img src="https://i.imgur.com/o558Qnq.png" align="center">
  <br>
  <strong><i>A feature-rich Modmail bot for Discord.</i></strong>
  <br>
  <br>

  <a href="https://discord.gg/rHRCcyb">
    <img src="https://img.shields.io/discord/515071617815019520.svg?label=Discord&logo=Discord&colorB=7289da&style=for-the-badge" alt="Support">
  </a>

  <a href="https://patreon.com/OhlookitsVeld">
    <img src="https://img.shields.io/badge/patreon-donate-orange.svg?style=for-the-badge&logo=Patreon" alt="Python 3.7">
  </a>

  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Made%20With-Python%203.7-blue.svg?style=for-the-badge&logo=Python" alt="Made with Python 3.7">
  </a>

  <a href="https://github.com/ambv/black">
    <img src="https://img.shields.io/badge/Code%20Style-Black-black?style=for-the-badge">
  </a>

  <a href="https://github.com/OhlookitsVeld/ModMail/blob/master/LICENSE">
    <img src="https://img.shields.io/badge/license-agpl-e74c3c.svg?style=for-the-badge" alt="MIT License">
  </a>

## What is Modmail?

Modmail is similar to Reddit's Modmail both in functionality and purpose. It serves as a shared inbox for server staff to communicate with their users in a seamless way.

This bot is free for everyone and always will be. If you like this project and would like to show your appreciation, you can support us on **[Patreon](https://www.patreon.com/OhlookitsVeld)**, cool benefits included! 

## How does it work?

When a member sends a direct message to the bot, Modmail will create a channel or "thread" within an isolated category. All further DM messages will automatically relay to that channel, for any available staff can respond within the channel.

All threads are logged and you can view previous threads through their corresponding log link.

## Features

* **Highly Customisable:**
  * Bot activity, prefix, category, log channel, etc.
  * Command permission system.
  * Interface elements (color, responses, reactions, etc).
  * Snippets and *command aliases*.
  * Minimum duration for accounts to be created before allowed to contact Modmail (`account_age`).
  * Minimum duration for members to be in the guild before allowed to contact Modmail (`guild_age`). 

* **Advanced Logging Functionality:**
  * When you close a thread, Modmail will generate a log link and post it to your log channel.
  * Native Discord dark-mode feel.
  * Markdown/formatting support.
  * Login via Discord to protect your logs ([premium Patreon feature](https://patreon.com/OhlooitsVeld)).
  * See past logs of a user with `?logs`.
  * Searchable by text queries using `?logs search`.

* **Robust implementation:**
  * Schedule tasks in human time, e.g. `?close in 2 hours silently`.
  * Editing and deleting messages are synced.
  * Support for the diverse range of message contents (multiple images, files).
  * Paginated commands interfaces via reactions.

This list is ever-growing thanks to active development and our exceptional contributors. See a full list of documented commands by using the `?help` command.

## Installation

Where can I find the Modmail bot invite link? 

Unfortunately, due to how this bot functions, it cannot be invited. This is to ensure the individuality to your server and grant you full control over your bot and data. Nonetheless, you can easily obtain a free copy of Modmail for your server by following one of the methods listed below (roughly takes 15 minutes of your time)...

### Hosting for patrons

If you don't want to go through the trouble of setting up your very own ModMail bot, and/or want to support this project, we offer the all inclusive installation, hosting and maintenance of your ModMail with [**Patron**](https://patreon.com/OhlookitsVeld). Join our [ModMail Discord Server](https://discord.gg/rHRCcyb) for more info! 

### Locally

Local hosting of Modmail is also possible, first you will need [`Python 3.7`](https://www.python.org/downloads/).

Follow the [**installation guide**](https://github.com/kyb3r/modmail/wiki/Installation) and disregard deploying the Heroku bot application. If you run into any problems, join our [ModMail Discord Server](https://discord.gg/rHRCcyb) for help and support.

Clone the repo:

```console
$ git clone https://github.com/OhlookitsVeld/ModMail
$ cd ModMail
```

Install dependencies:

```console
$ pipenv install
```

Rename the `.env.example` to `.env` and fill out the fields. If `.env.example` is nonexistent (hidden), create a text file named `.env` and copy the contents of [`.env.example`](https://raw.githubusercontent.com/OhlookitsVeld/ModMail/master/.env.example) then modify the values.

Finally, start Modmail.

```console
$ pipenv run bot
```


## Sponsors

Special thanks to our sponsors for supporting the project.

Become a sponsor on [Patreon](https://patreon.com/OhlookitsVeld).

## Plugins

Modmail supports the use of third-party plugins to extend or add functionalities to the bot. This allows niche features as well as anything else outside of the scope of the core functionality of ModMail. 

Plugins requests and support is available in our [Modmail Plugins Server](https://discord.gg/4JE4XSW).

## Contributing

Contributions to ModMail are always welcome, whether it be improvements to the documentation or new functionality, please feel free to make the change. 

If you like this project and would like to show your appreciation, support us on **[Patreon](https://www.patreon.com/Ohlookitsveld)**!