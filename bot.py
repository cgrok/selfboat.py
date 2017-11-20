'''
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
'''

import discord
from discord.ext import commands
import asyncio
import aiohttp
import datetime
import time
import json
import sys
import os
import re
import traceback
import textwrap
import psutil
import urbandict
import bs4 as bs
import urllib.request
import requests

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from discord.ext import commands
from urllib.request import urlopen
from enum import Enum


# git+https://github.com/fourjr/discord.py@rewrite
class Selfboat(commands.Bot):

    _mentions_transforms = {'@everyone': '@\u200beveryone',
                            '@here': '@\u200bhere'}

    _mention_pattern = re.compile('|'.join(_mentions_transforms.keys()))

    def __init__(self, *args, **kwargs):
        bot = self.bot
        super().__init__(command_prefix=self.get_pre, self_bot=True)
        self.description = '''Selfboat.py is a personal boat inspired by Selfbot.tk 
                              and improved by cgrok members\n
                              Just like your trousers... Take it with you wherever you are.'''
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.prefix = None
        self._extensions = [x.replace('.py', '') for x in os.listdir('cogs') if x.endswith('.py')]
        self.last_message = None
        # So, the idea is that user has to set a personal guild to use Selfboat error logs
        personal_guild = discord.utils.find(lambda s: s.id == 376697605029101569, bot.guilds)
        # self.remove_command('help')
        self.add_command(self.load)
        self.load_extensions()
        self.add_command(self.reload)
        self.add_command(self.unload)
        self.error_logs = personal_guild.get_channel(376698567370342400)
        # await self.error_logs.send(f'{readable}```py\n{e}\n```')


    def load_extensions(self, cogs=None, path='cogs.'):
        ''' Loads the default set of extensions '''
        for extension in cogs or self._extensions:
            try:
                self.load_extension(f'{path}{extension}')
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'LoadError: {extension}\n'
                      f'{type(e).__name__}: {e}')

    @commands.command(aliases=["reloadcog"])
    async def reload(self, ctx, *, cog: str):
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
        if ctx.author in dev_list:
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
         in case selfboat isn't in Heroku"""
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
                    readable = 'Your prefix has been changed temporarily until your Selfboat restarts to'
                    await self.error_logs.send(f'{readable}: `{prefix}`')
        except Exception as e:
            for channel in self.error_logs:
                if channel.send_messages:
                    readable = 'Error changing prefix to'
                    await self.error_logs.send(f'{readable}: `{prefix}`\n```py\n{e}\n```')


if __name__ == '__main__':
    Selfboat.init()

