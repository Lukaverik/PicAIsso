from aiba import aiba
from cogs.config import Config
from cogs.generate import Generate
from cogs.misc import Misc
from settings import token


def register_cogs():
    aiba.add_cog(Misc(bot=aiba))
    aiba.add_cog(Generate(bot=aiba))
    aiba.add_cog(Config(bot=aiba))


if __name__ == "__main__":
    register_cogs()
    aiba.run(token)