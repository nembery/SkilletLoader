#!/usr/bin/env python3
# Copyright (c) 2018, Palo Alto Networks
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Authors: Edward Arcuri, Nathan Embery

import os

import click
from skilletlib import SkilletLoader
from skilletlib import Panos
from skilletlib.exceptions import LoginException
from skilletlib.exceptions import SkilletLoaderException


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
        sl = SkilletLoader()
        skillet = sl.load_skillet_from_path(skillet_path)
        context = skillet.update_context(os.environ.copy())

        if skillet.type == 'panos':
            device = Panos(api_username=target_username,
                           api_password=target_password,
                           hostname=target_ip,
                           api_port=target_port
                           )

            skillet.panoply = device
            output = skillet.execute(context)
            # FIXME - context should always include a key indicating success / failure of the given skillet
            # we may need situations where a failure doesn't necessarily raise an exception and we should handle
            # this here. Possibly for things likes like - skillet already applied, no action taken, or some
            # check failed...
            if output.get('result', 'failure') == 'success':
                msg = device.commit()
                # msg = 'no commit for testing, commit commented out for now'
                print(f'Successfully executed Skillet {skillet.name} for host: {target_ip}')
                print(f'commit message was: {msg}')
                print(f'output was: {context}')
                exit(0)
            else:
                exit(1)

    except LoginException as lxe:
        print(lxe)
        exit(1)
    except SkilletLoaderException as lde:
        print(lde)
        exit(1)

    # failsafe
    exit(1)


if __name__ == '__main__':
    cli()
