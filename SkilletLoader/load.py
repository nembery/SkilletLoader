#!/usr/bin/env python3
import argparse
import os
import sys

from utils.exceptions import LoaderException
from utils.exceptions import LoginException
from utils.panos import Panos
from utils.skillet import Skillet

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip_address", help="IP address of the device", type=str)
    parser.add_argument("-r", "--port", help="Port", type=str)
    parser.add_argument("-u", "--username", help="Firewall Username", type=str)
    parser.add_argument("-p", "--password", help="Firewall Password", type=str)
    parser.add_argument("-s", "--skillet", help="Skillet Path", type=str)
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        parser.exit()
        exit(1)

    ip_addr = args.ip_address
    username = args.username
    password = args.password
    skillet_path = args.skillet
    port = args.port

    if not port:
        port = '443'

    try:
        skillet = Skillet(skillet_path)
        context = skillet.update_context(os.environ)

        if skillet.type == 'panos':
            device = Panos(api_username=username, api_password=password, hostname=ip_addr, api_port=port)
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
