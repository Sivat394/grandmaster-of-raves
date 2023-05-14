import discord.ext

token2 = 'MTEwNTUyNTc3NjA5MjI1NDM0OQ.GNkP3H.0oFI4lsBaHziXSXIX0LFtaphIIXh6m4Gtk_znU'
allowed_users = [857270689035059232,322154204619866112,430905941043576843]

def is_allowed():
    def predicate(ctx):
        return ctx.author.id in allowed_users
    return discord.ext.commands.check(predicate)

async def error_handler(ctx, error):
    if isinstance(error, discord.ext.commands.NotOwner):
        ctx.send('You are not the owner')
