import asyncio
import importlib
import json
import logging
import os
import shutil
import site
import stat
import subprocess
import sys
import typing
from difflib import get_close_matches

import discord
from discord.ext import commands
from pkg_resources import parse_version

from core import checks
from core.models import PermissionLevel
from core.paginator import EmbedPaginatorSession

logger = logging.getLogger("ModMail")


class DownloadError(Exception):
    pass


class Plugins(commands.Cog):
    """
    Plugins expand Modmail functionality by allowing third-party addons.

    These addons could have a range of features from moderation to simply
    making your life as a moderator easier!
    """

    def __init__(self, bot):
        self.bot = bot
        self.registry = {}
        self.bot.loop.create_task(self.download_initial_plugins())
        self.bot.loop.create_task(self.populate_registry())

    async def populate_registry(self):
        url = "https://raw.githubusercontent.com/OhlookitsVeld/ModMail/master/plugins/registry.json"
        async with self.bot.session.get(url) as resp:
            self.registry = json.loads(await resp.text())modmail.py

    @staticmethod
    def _asubprocess_run(cmd):
        return subprocess.run(cmd, shell=True, check=True, capture_output=True)

    @staticmethod
    def parse_plugin(name):
        # returns: (username, repo, plugin_name, branch)
        # default branch = master
        try:
            # when names are formatted with inline code
            result = name.split("/")
            result[2] = "/".join(result[2:])
            if "@" in result[2]:
                # branch is specified
                # for example, fourjr/modmail-plugins/welcomer@develop is a valid name
                branch_split_result = result[2].split("@")
                result.append(branch_split_result[-1])
                result[2] = "@".join(branch_split_result[:-1])
            else:
                result.append("master")

        except IndexError:
            return None

        return tuple(result)

    async def download_initial_plugins(self):
        await self.bot.wait_for_connected()

        for i in self.bot.config["plugins"]:
            username, repo, name, branch = self.parse_plugin(i)

            try:
                await self.download_plugin_repo(username, repo, branch)
            except DownloadError as exc:
                msg = f"{username}/{repo}@{branch} - {exc}"
                logger.error(msg, exc_info=True)
            else:
                try:
                    await self.load_plugin(username, repo, name, branch)
                except DownloadError as exc:
                    msg = f"{username}/{repo}@{branch}[{name}] - {exc}"
                    logger.error(msg, exc_info=True)

    async def download_plugin_repo(self, username, repo, branch):
        try:
            cmd = f"git clone https://github.com/{username}/{repo} "
            cmd += f"plugins/{username}-{repo}-{branch} "
            cmd += f"-b {branch} -q"

            await self.bot.loop.run_in_executor(None, self._asubprocess_run, cmd)
            # -q (quiet) so there's no terminal output unless there's an error
        except subprocess.CalledProcessError as exc:
            err = exc.stderr.decode("utf-8").strip()

            if not err.endswith("already exists and is not an empty directory."):
                # don't raise error if the plugin folder exists
                msg = f"Download Error: {username}/{repo}@{branch}"
                logger.error(msg)
                raise DownloadError(err) from exc

    async def load_plugin(self, username, repo, plugin_name, branch):
        ext = f"plugins.{username}-{repo}-{branch}.{plugin_name}.{plugin_name}"
        dirname = f"plugins/{username}-{repo}-{branch}/{plugin_name}"

        if "requirements.txt" in os.listdir(dirname):
            # Install PIP requirements

            venv = hasattr(sys, "real_prefix")  # in a virtual env
            user_install = "--user" if not venv else ""

            try:
                if os.name == "nt":  # Windows
                    await self.bot.loop.run_in_executor(
                        None,
                        self._asubprocess_run,
                        f"pip install -r {dirname}/requirements.txt {user_install} -q -q",
                    )
                else:
                    await self.bot.loop.run_in_executor(
                        None,
                        self._asubprocess_run,
                        f"python3 -m pip install -U -r {dirname}/"
                        f"requirements.txt {user_install} -q -q",
                    )
                    # -q -q (quiet)
                    # so there's no terminal output unless there's an error
            except subprocess.CalledProcessError as exc:
                err = exc.stderr.decode("utf8").strip()
                logger.error("Error.", exc_info=True)
                if err:
                    msg = f"Requirements Download Error: {username}/{repo}@{branch}[{plugin_name}]"
                    logger.error(msg)
                    raise DownloadError(
                        f"Unable to download requirements: ```\n{err}\n```"
                    ) from exc
            else:
                if not os.path.exists(site.USER_SITE):
                    os.makedirs(site.USER_SITE)

                sys.path.insert(0, site.USER_SITE)

        await asyncio.sleep(0.5)
        try:
            self.bot.load_extension(ext)
        except commands.ExtensionError as exc:
            msg = f"Plugin Load Failure: {username}/{repo}@{branch}[{plugin_name}]"
            logger.error(msg, exc_info=True)
            raise DownloadError("Invalid plugin") from exc
        else:
            msg = f"Loaded Plugin: {username}/{repo}@{branch}[{plugin_name}]"
            logger.info(msg)

    @commands.group(aliases=["plugins"], invoke_without_command=True)
    @checks.has_permissions(PermissionLevel.OWNER)
    async def plugin(self, ctx):
        """Plugin handler. Controls the plugins in the bot."""

        await ctx.send_help(ctx.command)

    @plugin.command(name="add", aliases=["install"])
    @checks.has_permissions(PermissionLevel.OWNER)
    async def plugin_add(self, ctx, *, plugin_name: str):
        """Add a plugin."""

        if plugin_name in self.registry:
            details = self.registry[plugin_name]
            plugin_name = (
                details["repository"] + "/" + plugin_name + "@" + details["branch"]
            )

            required_version = details["bot_version"]

            if parse_version(self.bot.version) < parse_version(required_version):
                embed = discord.Embed(
                    description=f"Your bot's version is too low. This plugin requires version `{required_version}`.",
                    color=self.bot.main_color,
                )
                return await ctx.send(embed=embed)

        if plugin_name in self.bot.config["plugins"]:
            embed = discord.Embed(
                description="This plugin is already installed.",
                color=self.bot.main_color,
            )
            return await ctx.send(embed=embed)

        if plugin_name in self.bot.cogs.keys():
            # another class with the same name
            embed = discord.Embed(
                description="There's another cog installed with the same name.",
                color=self.bot.main_color,
            )
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            description="Downloading this plugin...", color=self.bot.main_color
        )
        await ctx.send(embed=embed)

        async with ctx.typing():
            if len(plugin_name.split("/")) >= 3:
                username, repo, name, branch = self.parse_plugin(plugin_name)

                try:
                    await self.download_plugin_repo(username, repo, branch)
                except Exception as exc:
                    if not isinstance(exc, DownloadError):
                        logger.error(
                            "Unknown error when adding a plugin:", exc_info=True
                        )
                    embed = discord.Embed(
                        description=f"Unable to fetch this plugin from Github: `{exc}`.",
                        color=self.bot.main_color,
                    )
                    return await ctx.send(embed=embed)

                importlib.invalidate_caches()

                try:
                    await self.load_plugin(username, repo, name, branch)
                except Exception as exc:
                    if not isinstance(exc, DownloadError):
                        logger.error(
                            "Unknown error when adding a plugin:", exc_info=True
                        )
                    embed = discord.Embed(
                        description=f"Unable to load this plugin: `{exc}`.",
                        color=self.bot.main_color,
                    )
                    return await ctx.send(embed=embed)

                # if it makes it here, it has passed all checks and should
                # be entered into the config

                self.bot.config["plugins"].append(plugin_name)
                await self.bot.config.update()

                embed = discord.Embed(
                    description="The plugin is installed.\n"
                    "*Friendly reminder, plugins have absolute control over your bot. "
                    "Please only install plugins from developers you trust.*",
                    color=self.bot.main_color,
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    description="Invalid plugin name format: use plugin-name or "
                    "username/repo/plugin or username/repo/plugin@branch.",
                    color=self.bot.main_color,
                )
                await ctx.send(embed=embed)

    @plugin.command(name="remove", aliases=["del", "delete"])
    @checks.has_permissions(PermissionLevel.OWNER)
    async def plugin_remove(self, ctx, *, plugin_name: str):
        """Remove a plugin."""

        if plugin_name in self.registry:
            details = self.registry[plugin_name]
            plugin_name = (
                details["repository"] + "/" + plugin_name + "@" + details["branch"]
            )

        if plugin_name in self.bot.config["plugins"]:
            username, repo, name, branch = self.parse_plugin(plugin_name)
            try:
                self.bot.unload_extension(
                    f"plugins.{username}-{repo}-{branch}.{name}.{name}"
                )
            except commands.ExtensionNotLoaded:
                logger.error("Plugin was never loaded.")

            self.bot.config["plugins"].remove(plugin_name)

            try:
                if not any(
                    i.startswith(f"{username}/{repo}")
                    for i in self.bot.config["plugins"]
                ):
                    # if there are no more of such repos, delete the folder
                    def onerror(func, path, _):
                        if not os.access(path, os.W_OK):
                            # Is the error an access error?
                            os.chmod(path, stat.S_IWUSR)
                            func(path)

                    shutil.rmtree(
                        f"plugins/{username}-{repo}-{branch}", onerror=onerror
                    )
            except Exception:
                logger.error("Failed to remove plugin %s.", plugin_name, exc_info=True)
                self.bot.config["plugins"].append(plugin_name)
                return

            await self.bot.config.update()

            embed = discord.Embed(
                description="The plugin is uninstalled and all its data is erased.",
                color=self.bot.main_color,
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="That plugin is not installed.", color=self.bot.main_color
            )
            await ctx.send(embed=embed)

    @plugin.command(name="update")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def plugin_update(self, ctx, *, plugin_name: str):
        """Update a plugin."""

        if plugin_name in self.registry:
            details = self.registry[plugin_name]
            plugin_name = (
                details["repository"] + "/" + plugin_name + "@" + details["branch"]
            )

        if plugin_name not in self.bot.config["plugins"]:
            embed = discord.Embed(
                description="That plugin is not installed.", color=self.bot.main_color
            )
            return await ctx.send(embed=embed)

        async with ctx.typing():
            username, repo, name, branch = self.parse_plugin(plugin_name)

            try:
                cmd = (
                    f"cd plugins/{username}-{repo}-{branch} && "
                    f"git reset --hard origin/{branch} && git fetch --all && git pull"
                )
                cmd = await self.bot.loop.run_in_executor(
                    None, self._asubprocess_run, cmd
                )
            except subprocess.CalledProcessError as exc:
                err = exc.stderr.decode("utf8").strip()

                embed = discord.Embed(
                    description=f"An error occurred while updating: {err}.",
                    color=self.bot.main_color,
                )
                logger.error("An error occurred while updating plugin:", exc_info=True)
                await ctx.send(embed=embed)

            else:
                output = cmd.stdout.decode("utf8").strip()

                embed = discord.Embed(
                    description=f"```\n{output}\n```", color=self.bot.main_color
                )
                await ctx.send(embed=embed)

                if output != "Already up to date.":
                    # repo was updated locally, now perform the cog reload
                    ext = f"plugins.{username}-{repo}-{branch}.{name}.{name}"
                    self.bot.unload_extension(ext)

                    try:
                        await self.load_plugin(username, repo, name, branch)
                    except DownloadError as exc:
                        embed = discord.Embed(
                            description=f"Unable to start the plugin: `{exc}`.",
                            color=self.bot.main_color,
                        )
                        logger.error(
                            "An error occurred while updating plugin:", exc_info=True
                        )
                        await ctx.send(embed=embed)

    @plugin.command(name="enabled", aliases=["installed"])
    @checks.has_permissions(PermissionLevel.OWNER)
    async def plugin_enabled(self, ctx):
        """Shows a list of currently enabled plugins."""

        if self.bot.config["plugins"]:
            msg = "```\n" + "\n".join(sorted(self.bot.config["plugins"])) + "\n```"
            embed = discord.Embed(description=msg, color=self.bot.main_color)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="There are no plugins installed.", color=self.bot.main_color
            )
            await ctx.send(embed=embed)

    @plugin.group(
        invoke_without_command=True, name="registry", aliases=["list", "info"]
    )
    @checks.has_permissions(PermissionLevel.OWNER)
    async def plugin_registry(self, ctx, *, plugin_name: typing.Union[int, str] = None):
        """
        Shows a list of all approved plugins.

        Usage:
        `{prefix}plugin registry` Details about all plugins.
        `{prefix}plugin registry plugin-name` Details about the indicated plugin.
        `{prefix}plugin registry page-number` Jump to a page in the registry.
        """

        await self.populate_registry()

        embeds = []

        registry = sorted(self.registry.items(), key=lambda elem: elem[0])

        if isinstance(plugin_name, int):
            index = plugin_name - 1
            if index < 0:
                index = 0
            if index >= len(registry):
                index = len(registry) - 1
        else:
            index = next(
                (i for i, (n, _) in enumerate(registry) if plugin_name == n), 0
            )

        if not index and plugin_name is not None:
            embed = discord.Embed(
                color=discord.Color.red(),
                description=f'Could not find a plugin with name "{plugin_name}" within the registry.',
            )

            matches = get_close_matches(plugin_name, self.registry.keys())

            if matches:
                embed.add_field(
                    name="Perhaps you meant:",
                    value="\n".join(f"`{m}`" for m in matches),
                )

            return await ctx.send(embed=embed)

        for name, details in registry:
            repo = f"https://github.com/{details['repository']}"
            url = f"{repo}/tree/master/{name}"

            embed = discord.Embed(
                color=self.bot.main_color,
                description=details["description"],
                url=repo,
                title=details["repository"],
            )

            embed.add_field(
                name="Installation", value=f"```{self.bot.prefix}plugins add {name}```"
            )

            embed.set_author(
                name=details["title"], icon_url=details.get("icon_url"), url=url
            )
            if details.get("thumbnail_url"):
                embed.set_thumbnail(url=details.get("thumbnail_url"))
            if details.get("image_url"):
                embed.set_image(url=details.get("image_url"))

            embeds.append(embed)

        paginator = EmbedPaginatorSession(ctx, *embeds)
        paginator.current = index
        await paginator.run()

    @plugin_registry.command(name="compact")
    @checks.has_permissions(PermissionLevel.OWNER)
    async def plugin_registry_compact(self, ctx):
        """Shows a compact view of all plugins within the registry."""

        await self.populate_registry()

        registry = sorted(self.registry.items(), key=lambda elem: elem[0])

        pages = [""]

        for name, details in registry:
            repo = f"https://github.com/{details['repository']}"
            url = f"{repo}/tree/{details['branch']}/{name}"
            desc = details["description"].replace("\n", "")
            fmt = f"[`{name}`]({url}) - {desc}"
            length = len(fmt) - len(url) - 4
            fmt = fmt[: 75 + len(url)].strip() + "..." if length > 75 else fmt
            if len(fmt) + len(pages[-1]) >= 2048:
                pages.append(fmt + "\n")
            else:
                pages[-1] += fmt + "\n"

        embeds = []

        for page in pages:
            embed = discord.Embed(color=self.bot.main_color, description=page)
            embed.set_author(name="Plugin Registry", icon_url=self.bot.user.avatar_url)
            embeds.append(embed)

        paginator = EmbedPaginatorSession(ctx, *embeds)
        await paginator.run()


def setup(bot):
    bot.add_cog(Plugins(bot))