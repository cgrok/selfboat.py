from __future__ import division
import discord
import math
import operator
from discord.ext import commands
from pyparsing import (Literal, CaselessLiteral, Word, Combine, Group, Optional,
                       ZeroOrMore, Forward, nums, alphas, oneOf)


class NumericStringParserForPython3(object):
    def pushFirst(self, strg, loc, toks):
        self.exprStack.append( toks[0] )
    def pushUMinus(self, strg, loc, toks):
        if toks and toks[0]=='-':
            self.exprStack.append( 'unary -' )
    def __init__(self):
        point = Literal( "." )
        e     = CaselessLiteral( "E" )
        fnumber = Combine( Word( "+-"+nums, nums ) +
                        Optional( point + Optional( Word( nums ) ) ) +
                        Optional( e + Word( "+-"+nums, nums ) ) )
        ident = Word(alphas, alphas+nums+"_$")
        plus  = Literal( "+" )
        minus = Literal( "-" )
        mult  = Literal( "*" )
        div   = Literal( "/" )
        lpar  = Literal( "(" ).suppress()
        rpar  = Literal( ")" ).suppress()
        addop  = plus | minus
        multop = mult | div
        expop = Literal( "^" )
        pi    = CaselessLiteral( "PI" )
        expr = Forward()
        atom = ((Optional(oneOf("- +")) +
                (pi|e|fnumber|ident+lpar+expr+rpar).setParseAction(self.pushFirst))
                | Optional(oneOf("- +")) + Group(lpar+expr+rpar)
                ).setParseAction(self.pushUMinus)
        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( self.pushFirst ) )
        term = factor + ZeroOrMore( ( multop + factor ).setParseAction( self.pushFirst ) )
        expr << term + ZeroOrMore( ( addop + term ).setParseAction( self.pushFirst ) )
        # addop_term = ( addop + term ).setParseAction( self.pushFirst )
        # general_term = term + ZeroOrMore( addop_term ) | OneOrMore( addop_term)
        # expr <<  general_term
        self.bnf = expr
        # this will map operator symbols to their corresponding arithmetic operations
        epsilon = 1e-12
        self.opn = {
                "+" : operator.add,
                "-" : operator.sub,
                "*" : operator.mul,
                "/" : operator.truediv,
                "^" : operator.pow }
        self.fn  = {
                "sin" : math.sin,
                "cos" : math.cos,
                "tan" : math.tan,
                "abs" : abs,
                "trunc" : lambda a: int(a),
                "round" : round,
                "sgn" : lambda a: abs(a)>epsilon and cmp(a,0) or 0}

    def evaluateStack(self, s):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluateStack( s )
        if op in "+-*/^":
            op2 = self.evaluateStack( s )
            op1 = self.evaluateStack( s )
            return self.opn[op]( op1, op2 )
        elif op == "PI":
            return math.pi # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            return self.fn[op]( self.evaluateStack( s ) )
        elif op[0].isalpha():
            return 0
        else:
            return float( op )
    def eval(self,num_string,parseAll=True):
        self.exprStack=[]
        results=self.bnf.parseString(num_string,parseAll)
        val=self.evaluateStack( self.exprStack[:] )
        return val


class Calc:
    # Init with the bot reference, and a reference to the settings var
    def __init__(self, bot):
        self.bot = bot
        # prepare the session for the dictionaries
        self.session = bot.session
        # make use of all the great stuff from above for calculate command
        self.nsp=NumericStringParserForPython3()
        # Might work for share command into any particular channel
        # FIX THIS! self.TextChannel = discord.TextChannel
        self.color = bot.user_color

    @commands.command(aliases=['calc', 'maths'], name="calculate")
    async def _calculate(self, ctx, *, formula=None):
        """Python calculator commands
        Usage: Add: 2+3, Sub: 2-3, Mul: 2*3, Div: 2/3, Exp: 2^3,
        Pi: PI, E: e, Sin: sin, Cos: cos, Tan: tan, Abs: abs,
        Tru: trunc, Rou: round, Sgn: sgn

        Acknowledgments: Paul McGuire's fourFn.py."""
        u = ctx.message.author.display_name
        try:
            await ctx.channel.trigger_typing()
        except discord.Forbidden:
            pass

        if formula == None:
            pass

        try:
            answer=self.nsp.eval(formula)
        except:
            # If there's a problem with the input, shows examples instead of hanging up
            pass

        # Only if the input is correct it prints an answer
        try:
            await ctx.channel.trigger_typing()
            await asyncio.sleep(3)
            await ctx.send(f'{round(answer, 2)}')
        except discord.HTTPException:
            pass


def setup(bot):
    bot.add_cog(Calc(bot))
