from discord.ext import commands


class NotPersonalGuild(commands.CheckFailure):
    pass


def is_personal():
    """ Checks whether a is executed within personal channel or not """
    with open('data/config.json') as f:
        personal_c = json.load(f).get('PERSONALCHAN')
    self.error_logs = personal_guild.get_channel(personal_c)

    async def predicate(ctx):
        if ctx.author.id not in (x[1] for x in personal_c):
            raise NotPersonalGuild('Oops, that was a mistake')
        return True
    return commands.check(predicate)
