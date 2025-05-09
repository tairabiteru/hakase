import hikari
import miru


class AuthorOnlyView(miru.View):
    """A view constrained to only the original author.
    
    This view class can be extended to allow components to only be interacted
    with by the original author of a command.

    Args:

    Returns:

    """
    def __init__(self, author: hikari.User, *args, **kwargs):
        self.author: hikari.User = author
        super().__init__(*args, **kwargs)
    
    async def view_check(self, context: miru.ViewContext) -> bool:
        if self.author.id != context.author.id:
            return False
        return True