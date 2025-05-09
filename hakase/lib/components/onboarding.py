import hikari
import miru


class WelcomeModal(miru.Modal, title="Welcome!"):
    name = miru.TextInput(label="Your Name", placeholder="What should we call you?")
    library = miru.TextInput(label="Library Name", placeholder="What library are you from? Leave blank if none.")

    async def callback(self, ctx: miru.ModalContext) -> None:
        await ctx.respond(f"{self.name.value}, {self.library.value}")



class WelcomeView(miru.View):
    @classmethod
    def get_embed(cls) -> hikari.Embed:
        embed = hikari.Embed(title="Welcome to the Guild of Library Makers!")
        embed.description = "If you would be so kind, press the button below to set your name and library!"
        embed.set_thumbnail("https://lh4.googleusercontent.com/tfr21aepJ8ws4k-M18jahOCRgTXpY-umf5ADFaaeBrSyE4P22SE-_45mYHP2fLm001T0cvQhuQYO-SBUyIxQm9ZSK_KWJDv84inq93egbmrL5OOETuCWXA0zFNRGGucFNQ=w1280")
        embed.color = hikari.Color(0x006635)
        return embed

    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)

    @miru.button(label="Begin", style=hikari.ButtonStyle.PRIMARY, custom_id="welcome_button")
    async def modal_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        modal = WelcomeModal()
        await ctx.respond_with_modal(modal)