import discord
import asyncio
import random
import aiohttp
import json
import os
import bs4 as bs
import urllib.request
import requests

from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from discord.ext import commands
from urllib.request import urlopen


class Generate:
    def __init__(self, bot):
        self.bot = bot
        # prepare the session for qrcode
        self.session = bot.session

    @commands.group(aliases=['generate', 'create'])
    async def gen(self, ctx, *, msg):
        """ Group commands to generate verious things """
        pass

    @gen.command()
    async def qrcode(self, ctx, *, text: str=None):
        """ Generate a QR Code image """
        pass
    
    @gen.command()
    async def tinyurl(self, ctx, url: str=None):
        """ Generate a tinyurl link """
        pass

    @gen.command()
    async def invite(self, ctx, client_id: int=None):
        """ Generate an invite link for your bot """
        pass


def setup(bot):
    bot.add_cog(Generate(bot))
