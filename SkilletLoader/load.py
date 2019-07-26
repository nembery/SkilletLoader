#!/usr/bin/env python3
import os

import click

from utils.exceptions import LoginException
from utils.exceptions import SkilletLoaderException
from utils.panoply import Panoply
from utils.skillet import Skillet


@click.command()
@click.option("-i", "--target_ip", help="IP address of the device (localhost)", type=str, default="localhost")
@click.option("-r", "--target_port", help="Port to communicate to NGFW (443)", type=int, default=443)
@click.option("-u", "--target_username", help="Firewall Username (admin)", type=str, default="admin")
@click.option("-p", "--target_password", help="Firewall Password (admin)", type=str, default="admin")
@click.argument("skillet_path", type=click.Path(exists=True))
def cli(skillet_path, target_ip, target_port, target_username, target_password):
    """
    Load the Skillet from the command line.  Defaults values in parenthesis.
    """

    try:
        skillet = Skillet(skillet_path)
        context = skillet.update_context(os.environ.copy())

        if skillet.type == 'panos':
            device = Panoply(api_username=target_username,
                             api_password=target_password,
                             hostname=target_ip,
                             api_port=target_port
                             )

            for snippet in skillet.get_snippets():
                xpath, xmlstr = snippet.template(context)
                device.set_at_path(snippet.name, xpath, xmlstr)

            device.commit()
            print(f'Successfully pushed Skillet {skillet.name} to host: {target_ip}')
            exit(0)

    except LoginException as lxe:
        print(lxe)
        exit(1)
    except SkilletLoaderException as lde:
        print(lde)
        exit(1)

    exit(1)


if __name__ == '__main__':
    cli()
