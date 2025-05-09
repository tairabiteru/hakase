from functools import wraps
import hikari
import lightbulb
import miru
import typing as t

from .base import AuthorOnlyView
from ..linter import lint_lib


class ValidationButton(miru.Button):
    def __init__(self, label: str, style: hikari.ButtonStyle, value) -> None:
        super().__init__(label, style=style)
        self.view: Validation
        self.value = value
    
    async def callback(self, _: miru.ViewContext) -> None:
        self.view.validated = self.value


class Validation(AuthorOnlyView):
    """ """
    def __init__(self, author: hikari.User, confirm: str, cancel: str, timeout=None) -> None:
        super().__init__(author, timeout=timeout)
        self.validated: t.Optional[bool] = None
        self.add_item(ValidationButton(confirm, style=hikari.ButtonStyle.SECONDARY, value=True))
        self.add_item(ValidationButton(cancel, style=hikari.ButtonStyle.PRIMARY, value=False))


def validate(
        warning: t.Optional[str] = None,
        title: t.Optional[str] = "Confirmation",
        confirm: str = "Yes",
        cancel: str = "No",
        ephemeral: bool = False,
        timeout: t.Optional[int] = 30
) -> t.Callable:
    """
    Decorator for command methods which performs a confirmation before execution.

    Parameters
    ----------
    warning : str, optional
        The warning message to give the user.
    title : str, optional
        The title of the warning. Defaults to "Confirmation".
    confirm : str, optional
        What an "affirmative" response should be called. Defaults to "Yes".
    cancel : str, optional
        What a "negative" response should be called. Defaults to "No".
    ephemeral: bool, optional
        Whether or not the confirmation should be an ephemeral message.
    timeout : int, optional
        The time in seconds before the validation operation times out.
    
    Returns
    -------
    t.Callable
        The decorated function.
    """
    def decorator(func: t.Callable):
        @wraps(func)
        async def wrapper(self: lightbulb.CommandBase, ctx: lightbulb.Context, *args, **kwargs) -> None:
            embed = hikari.Embed(
                title=title,
                description=warning,
            )
            view = Validation(ctx.user, confirm, cancel, timeout=timeout)

            resp = await ctx.respond(embed, components=view, ephemeral=ephemeral)
            ctx.client.app.miru.start_view(view)
            await view.wait_for_input()

            await ctx.delete_response(resp)

            if view.validated is True:
                await func(self, ctx, *args, **kwargs)
            else:
                await ctx.edit_response(resp, "Operation cancelled.")
        
        return wrapper

    return decorator


def lint_before_exc():
    """
    Decorator for command methods which causes the bot to lint itself.

    This is used mainly in commands which causes restarts of the bot,
    or where the codebase will otherwise be "refreshed." It's a safety
    feature to prevent codebase changes from being made which inadvertently
    break the bot.
    
    Returns
    -------
    t.Callable
        The decorated function.
    """
    def decorator(func: callable):
        @wraps(func)
        async def wrapper(self: lightbulb.CommandBase, ctx: lightbulb.Context, *args, **kwargs) -> None:
            issues = await lint_lib()
            lines = []
            for issue in issues:
                line = f"[{issue['code']}][{issue['filename']}][Line {issue['location']['row']}]: {issue['message']}"
                lines.append(line)

            if len(issues) == 0:
                await func(self, ctx, *args, **kwargs)
            else:
                plural = "error was" if len(issues) == 1 else "errors were"
                await validate(
                    warning=f"{len(issues)} {plural} found in upstream code. Are you sure you wish to proceed?"
                )(func)(self, ctx, *args, **kwargs)

        return wrapper
    return decorator
