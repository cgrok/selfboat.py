from __future__ import division
import discord
import asyncio
import random
import json
import urbandictionary as ud
import string
import win_unicode_console

win_unicode_console.enable()

from bs4 import BeautifulSoup
from discord.ext import commands
from utils.calcparser import NumericStringParserForPython3


class Video:
    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['yt', 'vid'])
    async def video(self, ctx, *, search):
        """ Search for the first videos match on YouTube """

        with await ctx.channel.typing():
            search = search.replace(' ', '+').lower()

            with await self.bot.session.get(f"https://www.youtube.com/results?search_query={search}") as resp:
                response = await resp.text()

            result = BeautifulSoup(response, "lxml")
            dir_address = f"{result.find_all(attrs={'class': 'yt-uix-tile-link'})[0].get('href')}"
            output = f"https://www.youtube.com{dir_address}"

            if not dir_address:
                return

            try:
                await ctx.edit(message=output)
            except discord.Forbidden:
                await ctx.message.delete()
                return await ctx.send(output)


def setup(bot):
    bot.add_cog(Video(bot))
