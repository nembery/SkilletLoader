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

from utils.exceptions import LoginException
from utils.exceptions import SkilletLoaderException
from utils.panoply import Panoply
from utils.skillet.panos import PanosSkillet


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
        skillet = PanosSkillet(skillet_path)
        context = skillet.update_context(os.environ.copy())

        if skillet.type == 'panos':
            device = Panoply(api_username=target_username,
                             api_password=target_password,
                             hostname=target_ip,
                             api_port=target_port
                             )

            for snippet in skillet.get_snippets():
                # render anything that looks like a jinja template in the snippet metadata
                # mostly useful for xpaths in the panos case
                metadata = snippet.render_metadata(context)
                # check the 'when' conditional against variables currently held in the context
                if snippet.should_execute(context):
                    print(f'Loading Snippet: {snippet.name}')
                    # execute the command from the snippet definition and return the raw output
                    output = device.execute_cmd(snippet.cmd, metadata)
                    # update the context with any captured outputs defined in the snippet metadata
                    context.update(snippet.capture_outputs(output))

                else:
                    print(f'Skipping Snippet: {snippet.name}')

            print('Performing Commit')
            device.commit()
            print(f'Successfully pushed Skillet {skillet.name} to host: {target_ip}')
            exit(0)

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
