import aiofile
import asyncio
import datetime
import hikari
import lightbulb
import orjson as json
import os
import py_expression_eval
import random
import zoneinfo

from ...core.conf import Config
from .dice import dice
from ...lib.utils import aio_get, utcnow, execute_in_background
from ...lib.ctx import as_embed
from ...lib.timer import BackgroundTimer, BackgroundTimerError
from ...mvc.discord.models import User, Locale
from ...mvc.reminders.models import Reminder
from ...lib.components import WelcomeView


conf = Config.load()
tools = lightbulb.Loader()
tools.command(dice)


@tools.command
class Ping(
    lightbulb.SlashCommand,
    name="ping",
    description=f"See if {conf.name} is alive."
):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        await ctx.respond("PONG! 🏓")


@tools.command
class Cat(
    lightbulb.SlashCommand,
    name="cat",
    description="Post a random cat."
):
    ENDPOINT = "https://cataas.com"

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        data = await aio_get(
            f"{self.ENDPOINT}/cat?json=true",
            headers={'Accept': 'text/plain'}
        )
        await ctx.respond(as_embed(json.loads(data)['url']))


@tools.command
class Dog(
    lightbulb.SlashCommand,
    name="dog",
    description="Post a random dog."
):
    ENDPOINT = "https://random.dog/woof.json"

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        data = await aio_get(self.ENDPOINT)
        await ctx.respond(as_embed(json.loads(data)['url']))


@tools.command
class EightBall(
    lightbulb.SlashCommand,
    name="8ball",
    description="Ask a yes or no question, get an answer."
):
    
    question = lightbulb.string("question", "The question to ask.")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        if not self.question.endswith("?"):
            await ctx.respond(f"So usually questions end with a question mark. For example:\nDoes {ctx.user.username} know how a question works?")
        
        msg = f"**{ctx.user.username} asked:** `{self.question}`"
        async with aiofile.async_open(os.path.join(conf.asset_dir, "8ball_responses.txt"), "r") as responses:
            lines = []
            async for line in responses:
                lines.append(line)
            await ctx.respond(f"{msg}\n{random.choice(lines)}")


@tools.command
class Calculate(
    lightbulb.SlashCommand,
    name="calculate",
    description="Compute a math expression."
):
    
    expression = lightbulb.string("expression", "The expression to compute. Ex: sin(2 * (1.772 + 0.000454)^2).")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        try:
            parser = py_expression_eval.Parser()
            result = parser.parse(
                self.expression.replace("^", "**")
            ).evaluate({})
            await ctx.respond(f"`{self.expression} = {result}`")
        except ZeroDivisionError:
            await ctx.respond(f"`{self.expression}` results in a division by zero.")
        except Exception as e:
            await ctx.respond(f"Error: {str(e)}")


@tools.command
class Help(
    lightbulb.SlashCommand,
    name="help",
    description=f"Explain various parts of {conf.name}."
):
    
    topic = lightbulb.string("topic", "The topic to get help with.")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        pass


@tools.command
class RockPaperScissors(
    lightbulb.SlashCommand,
    name="rockpaperscissors",
    description="Play rock paper scissors."
):
    
    choice = lightbulb.string(
        "choice",
        "Your choice",
        choices=[
            lightbulb.Choice("rock", "rock"),
            lightbulb.Choice("paper", "paper"),
            lightbulb.Choice("scissors", "scissors")
        ]
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        choices = ["rock", "paper", "scissors"]
        game_matrix = [
            ["\nTie.", "\nI win!", f"\n{ctx.user.username} wins."],
            [f"\n{ctx.user.username} wins.", "\nTie.", "\nI win!"],
            ["\nI win!", f"\n{ctx.user.username} wins.", "\nTie."]
        ]

        bot_choice = random.choice(choices)
        msg = f"Your choice: {self.choice}"
        interaction = await ctx.respond(msg)
        await asyncio.sleep(1)
        msg += f"\nMy choice: {bot_choice}"
        await ctx.edit_response(interaction, msg)
        await asyncio.sleep(1)

        outcome = game_matrix[choices.index(self.choice)][choices.index(bot_choice)]
        msg += outcome
        await ctx.edit_response(interaction, msg)


@tools.command
class Choose(
    lightbulb.SlashCommand,
    name="choose",
    description=f"Have {conf.name} make a choice for you."
):
    
    choices = lightbulb.string("choice", "The choices to pick from, comma separated.")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, user: User):
        choices = self.choices.lower().split(",")
        choices = list(map(lambda x: x.strip(), choices))

        if len(choices) < 2:
            await ctx.respond("I need at least two things to choose from, or else it ain't much of a choice, now is it?")
            return
        if choices != list(dict.fromkeys(choices)):
            await ctx.respond("At least two of those things are the same. Are you trying to play games? 'Cause this ain't no fuckin' game.")
            return

        if user.last_choice_time is not None:
            td = utcnow() - user.last_choice_time
            n_choices = sorted(choices)
            if sorted(user.last_choices_list) == n_choices and td.total_seconds() <= conf.vars.choose_cmd_expiry_seconds:
                if choices != user.last_choices_list:
                    await ctx.respond(f"You're not going to fool me by just rearranging your list. I already told you my choice: ```{user.last_choice}```")
                    return
                await ctx.respond(f"Uh, I believe I already made this choice for you. I said: ```{user.last_choice}```Do you not remember?")

        confidences = [
            "I don't even know man, choose whatever.",
            "I guess go with {choice}. But it's only slightly better.",
            "I'm leaning more towards {choice}.",
            "Oh, definitely {choice}.",
            "{choice} without a doubt. No questions asked.",
            "{choice}. I'm honestly surprised you even asked.",
            "I'd go with {choice}.",
            "Are you kidding? {choice} is clearly the better option.",
            "Uh...Well, I guess {choice}, but I'm sort of on the fence about it.",
        ]

        confidence = random.choice(confidences)
        choice = random.choice(choices)
        if confidence == confidences[0]:
            choice = confidence
        elif confidences.index(confidence) in [1, 4, 7]:
            choice = confidence.format(choice=choice.capitalize())
        else:
            choice = confidence.format(choice=choice)

        user.last_choices_list = choices
        user.last_choice = choice
        user.last_dailies_time = utcnow()
        await user.asave()
        await ctx.respond(choice)


@tools.command
class Stopwatch(
    lightbulb.SlashCommand,
    name="stopwatch",
    description="Start or stop a stopwatch."
):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, user: User, locale: Locale):
        if user.stopwatch is None:
            user.stopwatch = utcnow()
            await user.asave()
            time = user.stopwatch.astimezone(zoneinfo.ZoneInfo(locale.timezone))
            await ctx.respond(f"Started at **{time.strftime('%-I:%M:%S.%f')}.")
        else:
            elapsed = utcnow() - user.stopwatch
            user.stopwatch = None
            await user.asave()
            await ctx.respond(f"Stopped at **{elapsed}**.")


@tools.command
class WhatIs(
    lightbulb.SlashCommand,
    name="whatis",
    description="Resolve a Discord snowflake ID to its associated object."
):
    id = lightbulb.string("id", "The ID to resolve.")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        self.id = self.id.strip()

        if not self.id.isdigit():
            await ctx.respond(f"`{self.id}` is not a valid Discord snowflake ID.")
            return

        if int(self.id) == ctx.user.id:
            await ctx.respond(f"`{self.id}` is your own user ID, ya doof.")
            return

        if int(self.id) == ctx.client.app.get_me().id:
            await ctx.respond(f"`{self.id}` would be me...you not have your coffee today or something?")
            return

        names = ["user", "guild", "guild_channel", "role"]
        accessors = ["username", "name", "name", "name"]
        
        for i, name in enumerate(names):
            obj = getattr(ctx.client.app.cache, f"get_{name}")(int(self.id))
            if obj is None:
                continue
            
            await ctx.respond(f"`{self.id}` resolves to the {name.replace("guild_", "")} {getattr(obj, accessors[i])}.")
            return
        
        await ctx.respond(f"`{self.id}` does not resolve to any known user, guild, channel, or role.")


@tools.command
class Timer(
    lightbulb.SlashCommand,
    name="timer",
    description="Start a timer."
):
    
    h = lightbulb.integer(
        "hours",
        "The number of hours to time for.",
        min_value=1,
        max_value=24,
        default=None
    )

    m = lightbulb.integer(
        "minutes",
        "The number of minutes to time for.",
        min_value=1,
        max_value=59,
        default=None
    )

    s = lightbulb.integer(
        "seconds",
        "The number of seconds to time for.",
        min_value=1,
        max_value=59,
        default=None
    )

    time = lightbulb.string(
        "time",
        "Set by time. Ex: 1:15 PM. Defaults to your timezone, or the server timezone if not set.",
        default=None
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, locale: Locale):
        h, m, s = tuple([getattr(self, t) for t in ["h", "m", "s"]])
        h, m, s = tuple(map(lambda t: t if t else 0, (h, m, s)))

        if not any([h, m, s, self.time]):
            await ctx.respond("You must either set an amount of time using `hours` `minutes` and/or `seconds`, or you must set a specific time using the `time` option.")
            return

        if self.time is not None and any([h, m, s]):
            await ctx.respond("You cannot use the `time` option if you're using any other options.")
            return
        
        try:
            if self.time is not None:
                timer = BackgroundTimer(ctx, time=self.time, timezone=locale.timezone)
            else:
                seconds = s + (60 * m) + (3600 * h)
                if seconds > 86400:
                    await ctx.respond("The time set is greater than 24 hours. I unfortunately cannot set timers longer than that.")
                    return
                timer = BackgroundTimer(ctx, seconds=seconds, timezone=locale.timezone)

            execute_in_background(timer.task())
        except BackgroundTimerError as e:
            await ctx.respond(str(e))


@tools.command
class Raw(
    lightbulb.SlashCommand,
    name="raw",
    description="Display text transmitted through Discord in raw form."
):

    text = lightbulb.string("text", "The text to view in raw form.")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context):
        await ctx.respond(f"```{self.text}```", flags=hikari.messages.MessageFlag.EPHEMERAL)


@tools.command
class Remind(
    lightbulb.SlashCommand,
    name="remind",
    description=f"Get a reminder from {conf.name} at some point in the future."
):

    time = lightbulb.string("in", "The time when the reminder should be sent. Ex: 30m, 4h, 3d, 20s")
    text = lightbulb.string("about", "The thing to remind you about.", default="No text was provided.")

    UNITS = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context, user: User, locale: Locale):
        self.time = self.time.replace(" ", "").lower()

        if not any([self.time.endswith(unit) for unit in self.UNITS]):
            await ctx.respond("Invalid time format. Time should be in a format like this: `30m`, `20s`, `3d`, `5h`, etc...")
            return
        try:
            delta, unit = float(self.time[:-1]), self.time[-1]
        except ValueError:
            await ctx.respond("Invalid time format. Time should be in a format like this: `30m`, `20s`, `3d`, `5h`, etc...")
            return

        delta = int(delta * self.UNITS[unit])
        time = utcnow() + datetime.timedelta(seconds=delta)
        reminder = await Reminder.objects.acreate(
            user=user,
            time=time,
            text=self.text
        )
        time = locale.aslocaltime_format(reminder.time)
        await ctx.respond(f"Reminder set for {time}.")


@tools.command
class Welcome(
    lightbulb.SlashCommand,
    name="welcome",
    description=f"Perform GOLM member onboarding."
):
    
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        view = WelcomeView()
        await ctx.respond(
            embed=WelcomeView.get_embed(),
            components=view.build(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        ctx.client.app.miru.start_view(view)
        
