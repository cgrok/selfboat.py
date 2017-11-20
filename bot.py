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

import aiohttp
import re
import os
import json


# git+https://github.com/fourjr/discord.py@rewrite
class Selfboat(commands.Bot):
    '''Custom client'''
    _mentions_transforms = {'@everyone': '@\u200beveryone',
                            '@here': '@\u200bhere'}

    _mention_pattern = re.compile('|'.join(_mentions_transforms.keys()))

    def __init__(self, *args, **kwargs):
        super().__init__(command_prefix=self.prefix, self_bot=True)
        self.description = '''Selfboat.py is a personal boat inspired by Selfbot.tk 
                              and improved by cgrok members\n
                              Just like your trousers... Take it with you wherever you are.'''
        self.session = aiohttp.ClientSession(loop=self.loop)
        self._extensions = [x.replace('.py', '') for x in os.listdir('cogs') if x.endswith('.py')]
        self.last_message = None
        # So, the idea is that user has to set a personal guild to use Selfboat error logs
        # Look at error_logs
        # self.remove_command('help')
        self.load_extensions()
        self.add_command(self.load)
        self.add_command(self.reload)
        self.add_command(self.unload)

    @property
    def token(self):
        '''Get the token wherever it is'''
        with open('data/config.json') as f:
            token = json.load(f).get('TOKEN')
        return os.environ.get('TOKEN') or token.strip('"').strip('"')

    @property
    def githubtoken(self):
        '''Get the token wherever it is'''
        with open('data/config.json') as f:
            token = json.load(f).get('GITHUBTOKEN')
        return os.environ.get('GITHUBTOKEN') or token.strip('"').strip('"')

    @property
    def prefix(self):
        '''Get the user prefix or default (//)'''
        with open('data/options.json') as f:
            return json.load(f).get('PREFIX')

    @property
    def error_logs(self):
        '''Get the user-configured error log channel'''
        with open('data/options.json') as f:
            return self.get_channel(int(json.load(f).get('ERROR-CHANNEL')))

    @classmethod
    def init(cls, token=None):
        '''Start the bot'''
        try:
            cls().run(token, bot=False, reconnect=True)
        except Exception as e:
            print(e)

    def load_extensions(self, cogs=None, path='cogs.'):
        ''' Loads the default set of extensions '''
        for extension in cogs or self._extensions:
            try:
                self.load_extension(f'{path}{extension}')
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'LoadError: {extension}\n{type(e).__name__}: {e}')

    @commands.command(aliases=["reloadcog"])
    async def reload(self, ctx, *, cog: str):
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
            await ctx.send(", ".join(sorted(unloaded)))

    @commands.group(invoke_without_command=True, name='sh', hidden=True)
    async def _sh(self, ctx, *, cmd: str=None):
        """ Extra layer of security
         in case selfboat isn't in Heroku"""
        pass

    @_sh.command(name='logout', hidden=True)
    async def _logout(self, ctx, *, _input: str=None):
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
