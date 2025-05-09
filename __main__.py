"""Main executable

This file starts the entire initialization process off, and comes with
the following commands:

    * mvc - Accesses the underlying Django MVC
    * run - Run hakase directly.
    * daemon - Run hakase as a daemon.
    * init_systemd - Create a SystemD service file.
    * init_bash - Create a bash script for the SystemD service.
"""
import click
import os
import pidfile
import sys
import setproctitle
import uvloop

from hakase.core.conf import Config


conf = Config.load(orm=True)
os.chdir(conf.root_dir)


def main(daemon: bool=False):
    """
    The main function which starts the bot.

    Args:
      daemon:  (bool) Whether or not the bot should be run as a daemon.

    Returns:
        None
    """
    try:
        uvloop.install()
        if os.path.exists(os.path.join(conf.root, "lock")):
            os.remove(os.path.join(conf.root, "lock"))

        from hakase.core.bot import Bot
        conf.daemon = daemon
        bot = Bot(conf)

        with pidfile.PIDFile():
            setproctitle.setproctitle(conf.name)
            bot.run()
            if not os.path.exists(os.path.join(conf.root, "lock")):
                if os.path.exists(os.path.join(conf.root, "pidfile")):
                    os.remove(os.path.join(conf.root, "pidfile"))
                os.system(f"{sys.executable} {' '.join(sys.argv)}")
            else:
                bot.logger.warning("Lock file exists, permanent shutdown.")
            sys.exit(0)

    except pidfile.AlreadyRunningError:
        bot.logger.critical(f"{conf.name} is already running.")


@click.group()
def hakase():
    """Group for click commands."""
    pass


@hakase.command()
@click.option('--exec_path', 'exec_path', default=f"./{conf.name.lower()}.sh")
@click.option('--uid', 'uid', default=os.getuid())
@click.option('--gid', 'gid', default=os.getgid())
@click.option('--stdout', 'stdout', default=f"{conf.logs}/{conf.name.lower()}.log")
@click.option('--stderr', 'stderr', default=f"{conf.logs}/{conf.name.lower()}.log")
@click.option('--output', 'output', default="./")
@click.option('--service_name', 'service_name', default=conf.name.lower())
def init_systemd(
        exec_path: str,
        uid: int,
        gid: int,
        stdout: str, 
        stderr: str,
        output_path: str,
        service_name: str
    ):
    """
    Create a systemd unit file from the template.

    Args:
      exec_path (str): POSIX path to the executable, usually a bash script.
      uid (str): The POSIX ID of the user that the bot runs under.
      gid (str): The POSIX ID of the group that the bot runs under.
      stdout (str): The path to a file where stdout will be appended.
      stderr (str): The path to a file where stderr will be appended.
      output_path (str): POSIX path where the unit file will be saved.
      service_name (str): The name to assign to the service.

    Returns:
        None
    """
    from hakase.core.init import generate_systemd_service

    generate_systemd_service(
        exec_path=exec_path,
        service_name=service_name,
        output_path=output_path,
        uid=uid,
        gid=gid,
        stdout_log_path=stdout,
        stderr_log_path=stderr
    )
    print("Systemd configuration generated.")


@hakase.command()
@click.option('--script_name', 'script_name', default=f"{conf.name.lower()}.sh")
@click.option('--output', 'output', default="./")
@click.option('--exec_dir', 'exec_dir', default="./")
@click.option('--venv', 'venv', default=".venv")
def init_bash(
        script_name: str,
        output_path: str,
        exec_dir: str,
        venv
    ):
    """
    Create a bash file which starts the bot.

    Args:
      script_name (str): The name to give to the script.
      output_path (str): A POSIX path where the file should be saved.
      exec_dir (str): A POSIX path to a directory where execution
        should take place.
      venv: (str): A POSIX path designating the location of the virtualenv.

    Returns:
        None
    """
    from hakase.core.init import generate_bash_script

    generate_bash_script(
        script_name=script_name,
        output_path=output_path,
        exec_directory=exec_dir,
        venv_directory=venv
    )
    print("Bash script generated.")


@hakase.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('subcommand', nargs=-1)
def mvc(subcommand):
    """Model-View Controller subcommands."""
    from django.core.management import execute_from_command_line
    execute_from_command_line([""] + sys.argv[2:])


@hakase.command()
def run():
    """'run' command."""
    main()


@hakase.command()
def daemon():
    """'daemon' command."""
    main(daemon=True)
    

if __name__ == "__main__":
    hakase()