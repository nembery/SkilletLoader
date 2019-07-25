#!/usr/bin/env python3
import argparse
import os
import sys
import click 

from utils.exceptions import LoaderException
from utils.exceptions import LoginException
from utils.panoply import Panoply
from utils.skillet import Skillet


@click.command()
@click.option("-i", "--ip_addr", help="IP address of the device (localhost)", type=str, default="localhost")
@click.option("-r", "--port", help="Port to communicate to NGFW (443)", type=int, default=443)
@click.option("-u", "--username", help="Firewall Username (admin)", type=str, default="admin")
@click.option("-p", "--password", help="Firewall Password (admin)", type=str, default="admin")
@click.argument("skillet", type=click.Path(exists=True))
def cli(skillet,ip_addr,port,username,password):
    """
    Load the SKILLET from the command line.  Defaults values in parenthesis.  
    """

    try:
        skillet = Skillet(skillet)
        context = skillet.update_context(os.environ.copy())

        if skillet.type == 'panos':
            device = Panoply(api_username=username, api_password=password, hostname=ip_addr, api_port=port)
            for snippet in skillet.get_snippets():
                xpath, xmlstr = snippet.template(context)
                device.set_at_path(snippet.name, xpath, xmlstr)

            device.commit()
            print(f'Successfully pushed Skillet {skillet.name} to host: {ip_addr}')
            exit(0)

    except LoginException as lxe:
        print(lxe)
        exit(1)
    except LoaderException as lde:
        print(lde)
        exit(1)

    exit(1)


if __name__ == '__main__':
    cli()



   
