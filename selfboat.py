"""
MIT License
Copyright (c) 2017 cgrok
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import discord
import aiohttp
import asyncio
# import colorthief
import datetime
import io
import json
import os
import psutil
import random
import re
import sys
import textwrap
import time
import traceback
# import wikipedia

from ext import embedtobox
from PIL import Image
from discord.ext import commands


class StatsBoard:
    """ StatsBoard class made by Kyb3r for Cody """
    def __init__(self, bot, channel, base=None):
        self.bot = bot
        self.channel = channel
        self.base = base
        self.running = bool(base)

    @property
    def current_stats(self):
        em = discord.Embed(title='Personal Statistics about Selfboat.py and my account :)')
        em.timestamp = datetime.datetime.utcnow()
        status = None
        me = self.channel.guild.me
        status = str(me.status)
        if status == 'online':
            em.set_author(name="Selfboat.py - Live Stats | Online", icon_url='https://i.imgur.com/wlh1Uwb.png')
            em.color = discord.Color.green()
        elif status == 'dnd':
            status = 'maintenance'
            em.set_author(name="Selfboat.py - Live Stats | Maintenance", icon_url='https://i.imgur.com/lbMqojO.png')
            em.color = discord.Color.purple()
        else:
            em.set_author(name="Selfboat.py - Live Stats | Busy", icon_url='https://i.imgur.com/dCLTaI3.png')
            em.color = discord.Color.red()

        total_online = len({m.id for m in self.bot.get_all_members() if m.status is not discord.Status.offline})
        total_unique = len(self.bot.users)
        channels = sum(1 for g in self.bot.guilds for _ in g.channels)

        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt
        uptime = fmt.format(d=days, h=hours, m=minutes, s=seconds)
        g_authors = 'kyb3r, fourjr, kwugfighter, FloatCobra, and kuro (XAOS1502)'
        em.description = f'Made by: {g_authors}'
        em.add_field(name='Current Status', value=str(status).title())
        em.add_field(name='Uptime', value=uptime)
        em.add_field(name="Boat's Latency", value=f'{self.bot.ws.latency*1000:.2f} ms')
        em.add_field(name="Guilds I'm in", value=len(self.bot.guilds))
        em.add_field(name='Members I can see', value=f'{total_online}/{total_unique} online')
        em.add_field(name='Channels I can see', value=f'{channels} in total')
        memory_usage = self.bot.process.memory_full_info().uss / 1024**2
        cpu_usage = self.bot.process.cpu_percent() / psutil.cpu_count()
        em.add_field(name='RAM Usage of Boat', value=f'{memory_usage:.2f} MiB')
        em.add_field(name='CPU Usage of Boat',value=f'{cpu_usage:.2f}% CPU')
        em.add_field(name="How many Commands I have used", value=sum(self.bot.commands_used.values()))
        em.add_field(name='How many DMs I have', value=self.bot.messages_sent)
        em.set_footer(text=f'My user ID: {self.bot.user.id}')

        return em

    async def make_base(self):
        self.base = await self.channel.send(embed=self.current_stats)
        self.running = True
        with open('data/config_base.json') as f:
            data = json.load(f)
        #with open('data/config_base.json', 'w') as f:
            data['base'] = self.base.id
        #    json.dump(data, f)

    async def force_update(self):
        await self.base.edit(embed=self.current_stats)

    async def run(self):
        if not self.running:
            await self.make_base()

        if isinstance(self.base, int):
            try:
                self.base = await self.channel.get_message(self.base)
            except:
                await self.make_base()

        while self.running:
            try:
                await self.base.edit(embed=self.current_stats)
            except discord.HTTPException:
                await self.make_base()
            await asyncio.sleep(5)


class Selfboat(commands.Bot):

    _mentions_transforms = {'@everyone': '@\u200beveryone',
                            '@here': '@\u200bhere'}

    _mention_pattern = re.compile('|'.join(_mentions_transforms.keys()))

    def __init__(self, *args, **kwargs):
        # bot = self.bot
        super().__init__(command_prefix=self.get_pre, self_bot=True)
        self.description = textwrap.dedent("""
        Selfboat.py is a personal boat inspired by Selfbot.tk 
        and improved by cgrok members with much love ❤
        Just like your trousers...Take it with you everywhere you go.""")
        # Here is all the important stuff, gotta make sure it works
        self.uptime = datetime.datetime.utcnow()
        # self.db = ConfigDatabase(self)
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.process = psutil.Process()
        self._extensions = [x.replace('.py', '') for x in os.listdir('cogs') if x.endswith('.py')]
        self.messages_sent = 0
        self.commands_used = defaultdict(int)
        # So, the idea is that user has to set a personal guild to use Selfboat error logs
        with open('data/config.json') as f:
            personal_g = json.load(f).get('DEFAULT-GUILD')
        personal_guild = discord.utils.find(lambda s: s.id == personal_g, bot.guilds)
        # for now, we don't need this help command
        # self.remove_command('help')
        self.add_command(self.load)
        self.load_extensions()
        self.add_command(self._reload)
        self.add_command(self.unload)
        with open('data/config.json') as f:
            personal_c = json.load(f).get('ERROR-CHANNEL')
        self.error_logs = personal_guild.get_channel(personal_c)
        
        self.loop.create_task(self.statsboard())
        #self.remove_command('help')
        self.add_command(self.ping)
        # self.repo_version = 
        # Need to include GitHub commit number as version to know what version is running
        # it will not run rightnow because it is not defined!

    '''def __init__(self, *args, **kwargs):
        super().__init__(command_prefix=self.prefix, self_bot=True)
        self.description = textwrap.dedent("""Selfboat.py is a personal boat inspired by Selfbot.tk 
                              and improved by cgrok members\n
                              Just like your trousers... Take it with you wherever you are.""")
        self.session = aiohttp.ClientSession(loop=self.loop)
        self._extensions = [x.replace('.py', '') for x in os.listdir('cogs') if x.endswith('.py')]
        self.last_message = None
        # So, the idea is that user has to set a personal guild to use Selfboat error logs
        # Look at error_logs
        # self.remove_command('help')
        self.load_extensions()
        self.add_command(self.load)
        self.add_command(self.reload)
        self.add_command(self.unload)'''


    #################################################################
    # Okay, you are thinking right now, "what is all this shit?"
    # I don't blame you. There is still a lot to figure out and fix,
    # but the main idea behind this project is stability and security,
    # as well as to make sure that the Discord API isn't abused in
    # any way whatsoever. To ensure this, it is required for you to:
    # -------------~-------------
    # 1) get your Discord TOKEN
    # 2) get your GitHub TOKEN
    # 3) make a new guild
    # 4) copy its ID
    # 5) and, put all that ^ in Heroku Config Vars
    # -------------~-------------
    # after this is done, all of Selfboat commands will print their
    # output in your DEFAULT-GUILD, inside ERROR-CHANNEL,
    # this is done with the hope that your account isn't flagged
    # by Discord for being a malicious self-bot.
    # As an extra layer of security, we also have included
    # git+https://github.com/fourjr/discord.py@rewrite
    # which fixes problems of the current Python wrapper; mainly the
    # message headers.
    # If you aren't Mod or Owner of a guild, don't bother using
    # the moderation cog.
    # Also, any command that produces an output, will print it
    # in ERROR-CHANNEL, with a few exceptions.
    # A word of advice: don't go showing off your new toy.
    #
    # For help, or just to interact with the devs, join our support
    # guild at: https://discord.gg/Fa767ZW
    #################################################################

    @property
    def token(self):
        """ Returns your token from Heroku only """
        if not os.environ.get('TOKEN'):
            print(textwrap.dedent(f"""
            To use Selfboat.py you need to
            define these parameters in Heroku:
            
            Key:      TOKEN
            Value:    paste_here_your_discord_token
            -------------~-------------
            If you don't know how to get
            your token, join support guild"""))
        else:
            return os.environ.get('TOKEN')

    @property
    def githubtoken(self):
        """ Get the token wherever it is """
        if not os.environ.get('GITHUBTOKEN'):
            print(textwrap.dedent(f"""
            To use Selfboat.py you need to
            define these parameters in Heroku:

            Key:      GITHUBTOKEN
            Value:    paste_here_your_GitHub_token
            -------------~-------------
            If you don't know how to get
            your token, join support guild"""))
        else:
            with open('data/config.json') as f:
                token = json.load(f).get('GITHUBTOKEN')
            return os.environ.get('GITHUBTOKEN') or token.strip('"').strip('"')

    async def githubusername():
        async with self.session.get('https://api.github.com/user', 
                                    headers={"Authorization": f"Bearer {self.githubtoken}"}) as resp: #get username 
            if 300 > resp.status >= 200:
                return (await resp.json())['login']
            if resp.status == 401: #invalid token!
                return None
                   
    # TO ADD TO CUSTOM CTX
    async def premium(error=False):
        async with self.session.get('https://api.github.com/user/starred/cgrok/selfboat.py', 
                                    headers={"Authorization": f"Bearer {bot.githubtoken}"}) as resp:
            if resp.status == 204:
                if discord.utils.get(bot.guilds, id=376697605029101569) is None:
                    if not error:
                        star = '<https://discord.gg/Fa767ZW!>'
                        msg = '**This is a premium command**, to unlock it, join our support guild: {star}'
                        await ctx.send(msg)
                    return False
                else:
                    return True
            if resp.status == 404:
                if not error:
                    star = '<https://github.com/cgrok/selfboat.py>'
                    msg = '**This is a premium command**, to unlock it, ensure you have starred {star}'
                    await ctx.send(msg)
                return False

    async def updatedata(self, path:str, content:str, commitmsg='No Commit Message'):
        '''To edit data in Github'''
        #get username
        username = await bot.githubusername()
        #get sha (dont even know why this is a compulsory field)
        async with self.session.get(f'https://api.github.com/repos/{username}/selfbot.py/contents/{path}', 
                                    headers={"Authorization": f"Bearer {bot.githubtoken}"}) as resp2:
            if 300 > resp2.status >= 200:
                #push to path
                async with self.session.put(f'https://api.github.com/repos/{username}/selfbot.py/contents/{path}', 
                                            headers={"Authorization": f"Bearer {bot.githubtoken}"}, 
                                            json={"path":"data/cc.json", "message":commitmsg, 
                                            "content":base64.b64encode(bytes(content, 'utf-8')).decode('ascii'), 
                                            "sha":(await resp2.json())['sha'], "branch":"rewrite"}) as resp3:
                    if 300 > resp3.status >= 200:
                        return True
                        #data pushed successfully
                    else:
                        msg = 'Well, I failed somehow, send the following to `4JR#2713` (180314310298304512): '\
                              '```py\n' + str(await resp3.json()) + '\n```'
                        await self.send(msg)
                        return False 
            else:
                msg = 'Well, I failed somehow, send the following to `4JR#2713` (180314310298304512): '\
                      '```py\n' + str(await resp2.json()) + '\n```'
                await self.send(msg)
        return False

    # TO ADD ABOVE TO CUSTOM CTX

    @staticmethod
    async def get_pre(bot, message):
        """ Returns the prefix, default (//) """
        with open('data/config.json') as f:
            prefix = json.load(f).get('PREFIX')
        return os.environ.get('PREFIX') or prefix or '//'

    @property
    def error_logs(self):
        """ Get the user-configured error log channel """
        with open('data/options.json') as f:
            return os.environ.get('ERROR-CHANNEL') or \
                   self.get_channel(int(json.load(f).get('ERROR-CHANNEL')))


    @classmethod
    def init(cls, token=None):
        """ Start the bot """
        try:
            cls().run(token, bot=False, reconnect=True)
        except Exception as e:
            print(e)


    def load_extensions(self, cogs=None, path='cogs.'):
        """ Loads the default set of extensions """
        for extension in cogs or self._extensions:
            try:
                self.load_extension(f'{path}{extension}')
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'LoadError: {extension}\n'
                      f'    --> {type(e).__name__}: {e}')

    async def on_ready(self):
        if not hasattr(self, 'start_time'):
            self.start_time = datetime.now()
        print(f"Starting at: {self.start_time}.\n")

    async def on_connect(self):
        print(textwrap.dedent(f"""
        -------------~-------------
        Selfboat.py connected!
        {self.user.name}
        {self.user.id}
        -------------~-------------
        Developed by:    github.com/cgrok/selfboat.py
        Current Version: `self.repo_version`
        
        (∩｀-´)⊃━☆ﾟ.*･｡ﾟ
        
        Some people still consider
        selfbots to be against ToS
        and we've done our best to
        make this bot as secure as
        possible. Yet, if you get
        banned, we are not in any
        way responsible.
        Use it wisely! Enjoy it!"""))
        await self.change_presence(status=discord.Status.online, afk=True)

    async def on_command_error(self, ctx, error):
        send_help = (commands.MissingRequiredArgument, commands.BadArgument, 
                    commands.TooManyArguments, commands.UserInputError)
        em = discord.Embed(color = discord.Color.red(), timestamp=ctx.message.created_at, 
                           description="Command Error:")
        em.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url)
        if ctx.invoked_subcommand:
            em.add_field(name="Invoked Subcommand", value=ctx.invoked_subcommand, inline=False)
        else:
            em.add_field(name="Invoked Command", value=ctx.command, inline=False)
        em.add_field(name="Error", value=f'```py\n{error}\n```', inline=False)
        # await bot.get_channel(365900963355295745).send(embed=em) this is Selfboat.py's channel
        ## await bot.get_channel(355461117004218371).send(embed=em) # This is robotsu tester channel
        # Rushed so if someone wants to fix that'd be nice xoxoxoxo
        await ctx.send(embed=em)
        if isinstance(error, send_help):
            await self.send_cmd_help(ctx)

    async def on_command(self, ctx):
        cmd = ctx.command.qualified_name.replace(' ', '_')
        self.commands_used[cmd] += 1

    async def process_commands(self, message):
        """Utilises the CustomContext subclass of discord.Context"""
        ctx = await self.get_context(message, cls=CustomContext)
        if ctx.command is None:
            return
        await self.invoke(ctx)

    # And here are the commands to load, unload, reload and view the
    # rest of cogs. Each cog will have a single command, or similar
    # ones, that way it is easy to enable or disable them.
    # Perhaps could include a way to save which ones are (un)loaded
    # in a cogs.json file, so it is persistent.
    # The way these commands work is that they send the result to the
    # ERROR-CHANNEL by default, regardless where they are invoked
    #
    # The ERROR-CHANNEL should be automatically created after first
    # installation of Selfboat. All it requires is a defined DEFAULT-GUILD
    # and then it can set ERROR-CHANNEL as private and save some info
    # in channel topic (same as ModMail)
    @commands.command(aliases=["reloadcog"], name='reload')
    async def _reload(self, ctx, *, cog: str):
        """ Reload any cog """
        cog = f"cogs.{cog}"
        self.unload_extension(cog)
        try:
            self.load_extension(cog)
            for channel in self.error_logs:
                if channel.send_messages:
                    readable = 'Successfully reloaded the'
                    await self.error_logs.send(f'{readable}: {cog}')
        except Exception as e:
            for channel in self.error_logs:
                if channel.send_messages:
                    readable = 'Error reloading cog'
                    await self.error_logs.send(f'{readable}: {cog}\n```py\n{e}\n```')

    @commands.command(aliases=["loadcog"])
    async def load(self, ctx, *, cog: str):
        """ Load a cog """
        try:
            self.load_extension(cog)
            for channel in self.error_logs:
                if channel.send_messages:
                    readable = 'Successfully loaded the'
                    await self.error_logs.send(f'{readable}: {cog}')
        except Exception as e:
            for channel in self.error_logs:
                if channel.send_messages:
                    readable = 'Error loading cog'
                    await self.error_logs.send(f'{readable}: {cog}\n```py\n{e}\n```')

    @commands.command(aliases=["unloadcog"])
    async def unload(self, ctx, *, cog: str):
        """ Unload any cog """
        try:
            for channel in self.error_logs:
                if channel.send_messages:
                    readable = 'Successfully unloaded the'
                    await self.error_logs.send(f'{readable}: {cog}')
                    self.unload_extension(cog)
        except Exception as e:
            for channel in self.error_logs:
                if channel.send_messages:
                    readable = 'Error unloading cog'
                    await self.error_logs.send(f'{readable}: {cog}\n```py\n{e}\n```')

    # Okay, this is a complete mess, sorry
    @commands.command(aliases=['listcogs'])
    async def cogs(self, ctx):
        """ See unloaded and loaded cogs! """
        if ctx.channel == self.error_logs:
            def pagify(text, delims=['\n'], *, escape=True, shorten_by=8,
                       page_length=2000):
                in_text = text
                if escape:
                    num_mentions = text.count('@here') + text.count('@everyone')
                    shorten_by += num_mentions
                page_length -= shorten_by
                while len(in_text) > page_length:
                    closest_delim = max([in_text.rfind(d, 0, page_length)
                                         for d in delims])
                    closest_delim = closest_delim if closest_delim != -1 else page_length
                    if escape:
                        to_send = escape_mass_mentions(in_text[:closest_delim])
                    else:
                        to_send = in_text[:closest_delim]
                    yield to_send
                    in_text = in_text[closest_delim:]
                yield in_text

            def box(text, lang=''):
                ret = f'```{lang}\n{text}\n```'
                return ret
            loaded = [c.__module__.split('.')[1] for c in self.bot.cogs.values()]
            # What's in the folder but not loaded is unloaded

            def _list_cogs():
                  cogs = [os.path.basename(f) for f in 'cogs/*.py' or 'cogs/community/*.py']
                  return ['cogs.' + os.path.splitext(f)[0] for f in cogs]
            unloaded = [c.split('.')[1] for c in _list_cogs() if c.split('.')[1] not in loaded]

            if not unloaded:
                unloaded = ['None']

            await ctx.send(", ".join(sorted(loaded)))
            await ctx.send(", ".join(sorted(unloaded)))
        else:
            pass

    @commands.group(invoke_without_command=True, name='sh', hidden=True)
    async def _sh(self, ctx, *, cmd: str=None):
        """ Extra layer of security
         in case selfboat isn't in Heroku """
        pass

    @_sh.command(name='logout', hidden=True)
    async def _logout(self, ctx, *, input: str=None):
        """ Shutdown in case of malfunction """
        await self.change_presence(status=discord.Status.offline)
        for channel in self.error_logs:
            if channel.send_messages:
                readable = 'Logging off Selfboat'
                await self.error_logs.send(readable)
        self.session.close()
        await self.logout()

    @commands.command(name='prefix')
    async def _prefix(self, ctx, *, prefix):
        """ Change temporarily bot's prefix """
        os.environ['PREFIX'] = prefix
        await ctx.edit(f'{prefix}')
        try:
            for channel in self.error_logs:
                if channel.send_messages:
                    readable = 'Your prefix has been changed temporarily to'
                    msg = 'until your Selfboat restarts'
                    await self.error_logs.send(f'{readable}: `{prefix}` {msg}')
        except Exception as e:
            for channel in self.error_logs:
                if channel.send_messages:
                    readable = 'Error changing prefix to'
                    await self.error_logs.send(f'{readable}: `{prefix}`\n```py\n{e}\n```')

    #################################################################
    #  !»--~ ModLogs ~--«! and channel_log are setup here before 
    # Selfboat.py can be used anywhere. This is to get a place for 
    # the message outputs to have a place to print and show errors.
    #################################################################
    async def setup(self, ctx):
        """ Sets up a guild and channel for Selfboat.py """
        sg = '<https://discord.gg/2B4UvKx>'
        pr = '<https://github.com/cgrok/selfboat.py/pull/new/master>'
        issue = '<https://github.com/cgrok/selfboat.py/issues/new>'
        fjr = '<https://github.com/fourjr/discord.py@rewrite>'
        message = ctx.author
        warn = "Oops, wrong Guild\nI'll do this in my Guild! Sorry"
        desc = textwrap.dedent(f"""As of November 2017, the discord.py API wrapper v1.0.0a doesn't handle 
        message Headers *'correctly'*  for self-bots, as it is meant for regular bot-accounts; and the Discord 
        API doesn't like these Headers to show up in any DMs that are supposed to come from user-accounts, so 
        they *will* most likely `flag` or `disable` your account for such infractions.\n\n**Why?** Because this 
        constitutes Discord API abuse.\nHowever, this is not the case with ***Selfboat.py***.\n\nRegardless, 
        please use this personal Python app wisely.\n```py\nThe purpose of this channel is for you to spam 
        commands and practise, as well as to print all errors and messages any time you execute commands 
        elsewhere.```\n***Selfboat.py*** is made in Python3.6 and uses v1.0.0aX, a fork of Discord.py\n\nPlease 
        join our [Support Guild]({sg})\n(File an issue]({issue})\n[Pull a request]({pr})""")
        v = f'created by cgrok using {fjr}'
        foo = '» A lite, clean & stealthy boat to keep you afloat «'

        if ctx.author.id != ctx.guild.owner_id:
            return await message.edit(content=warn, delete_after=5)

        if ctx.author.id == ctx.guild.owner_id:
            if discord.utils.get(ctx.guild.categories, name='!»--~ ModLogs ~--«!'):
                succ = "Reee! I already set this guild up #ModLogs"
                return await ctx.send(succ, delete_after=5)
            try:
                modlogs_category = await ctx.guild.create_category(name='»--~ ModLogs ~--«')
                await modlogs_category.edit(position=0)
                c = await ctx.guild.create_text_channel(name='channel-log', category=modlogs_category)
                em = discord.Embed(title="Welcome, here you can test Selfboat.py's commands",
                                   colour=discord.Colour(0xed791d))
                em.description = f'{desc}'
                em.add_field(name='Selfboat.py', value=v)
                em.set_footer(text=foo, icon_url='https://take-me-to.space/BMznunc.png')
                em.set_thumbnail(url='https://take-me-to.space/d66twk4.png')
                await c.send(embed=em)
                await ctx.send('***Selfboat.py*** server is ready.')

            except discord.Forbidden:
                await message.edit(content=warn, delete_after=5)
        else:
            pass

    # Selfboat doesn't print results outside ERROR-CHANNEL
    '''@commands.command(aliases=["reloadcog"], name='reload')
    async def _reload(self, ctx, *, cog: str):
        """ Reload any cog """
        cog = f'cogs.{cog}'
        try:
            self.unload_extension(cog)
            self.load_extension(cog)
        except Exception as e:
            await ctx.send(f'Error occured while reloading {cog}\n```py\n{e}\n```')
        else:
            await ctx.send(f'Successfully reloaded {cog}')

    @commands.command(aliases=["loadcog"])
    async def load(self, ctx, *, cog: str):
        """ Load a cog """
        cog = f'cogs.{cog}'
        try:
            self.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'Error occured while loading {cog}\n```py\n{e}\n```')
        else:
            await ctx.send(f'Successfully unloaded {cog}')

    @commands.command(aliases=["unloadcog"])
    async def unload(self, ctx, *, cog: str):
        """ Unload any cog """
        try:
            self.unload_extension(cog)
        except Exception as e:
            await ctx.send(f'Error occured while unloading {cog}\n```py\n{e}\n```')
        else:
            await ctx.send(f'Successfully unloaded {cog}')

    # Okay, this is a complete mess, sorry
    @commands.command(name='cogs', aliases=['listcogs'])
    async def _cogs(self, ctx):
        '''See unloaded and loaded cogs!'''
        def pagify(text, delims=['\n'], *, escape=True, shorten_by=8,
                   page_length=2000):
            '''Pagify!'''
            in_text = text
            if escape:
                num_mentions = text.count('@here') + text.count('@everyone')
                shorten_by += num_mentions
            page_length -= shorten_by
            while len(in_text) > page_length:
                closest_delim = max([in_text.rfind(d, 0, page_length)
                                     for d in delims])
                closest_delim = closest_delim if closest_delim != -1 else page_length
                if escape:
                    to_send = escape_mass_mentions(in_text[:closest_delim])
                else:
                    to_send = in_text[:closest_delim]
                yield to_send
                in_text = in_text[closest_delim:]
            yield in_text

            def box(text, lang=''):
                '''Turns it into the discord syntax highlighting'''
                ret = f'```{lang}\n{text}\n```'
                return ret
            loaded = [c.__module__.split('.')[1] for c in self.cogs.values()]
            # What's in the folder but not loaded is unloaded

            def _list_cogs():
                '''List all cogs'''
                cogs = [os.path.basename(f) for f in 'cogs/*.py' or 'cogs/community/*.py']
                return ['cogs.' + os.path.splitext(f)[0] for f in cogs]
            unloaded = [c.split('.')[1] for c in _list_cogs() if c.split('.')[1] not in loaded]

            if not unloaded:
                unloaded = ['None']

            await ctx.send(", ".join(sorted(loaded)))
            await ctx.send(", ".join(sorted(unloaded)))'''


if __name__ == '__main__':
    Selfboat.init()
