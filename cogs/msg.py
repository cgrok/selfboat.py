import discord
import asyncio
import random
import aiohttp
import json
import os
import urbandict
import bs4 as bs
import urllib.request
import requests

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from discord.ext import commands
from urllib.request import urlopen


class Messages:
    def __init__(self, bot):
        self.bot = bot
        # prepare the session for the dictionaries
        self.session = bot.session


    @commands.command()
    async def clap(self, ctx, *, msg):
        """ Clap that message! """
        if msg is not None:
            text = msg.replace(' ', ' :clap: ')
            await ctx.edit(content=text)
        else:
            pass


def setup(bot):
    bot.add_cog(Messages(bot))
