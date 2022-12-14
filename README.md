# PicAIsso

Installation/Run Instructions:
1. Download an instance of [Automatic1111's Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) (or make your own).
 -  A full instance (including models) can be found [here](https://rentry.org/voldy)
2. Clone this repository.
3. If you don't already have a bot user, make one. [This](https://www.upwork.com/resources/how-to-make-discord-bot) is a good resource for how to get one set up.
4. Edit your WebUI instance's `webui-user.bat`, adding `--api` to the command line args. For reference, mine looks like this:
```
@echo off

set PYTHON=
set GIT=
set VENV_DIR=
set COMMANDLINE_ARGS=--api --precision full --no-half

call webui.bat
```
5. With the stable diffusion instance running, your local URL should be visible near the bottom of the terminal.
6. In the main directory of the cloned repository, create a .env file and enter the following:
```
DISCORD_TOKEN=<YOUR BOT TOKEN HERE>
BASE_URL=<YOUR LOCAL URL HERE>
```
7. If you want to change the appearance of your bot (or have a different status), you can look in the file `aiba.py` to find where I initialize the disnake.py client. I knew I was calling my bot Aiba, so I named the classes and prompts as such, but the code is set up in such a way that you can pretty much find every instance of "aiba" or "Aiba" in the directory and change them to whatever you want. (CTRL+SHIFT+F is find in directory in most IDEs.)
8. Run your bot, and you should be good to go!
