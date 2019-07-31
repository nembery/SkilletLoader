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

# Authors: Nathan Embery


import re
import time
from pathlib import Path
from xml.etree import ElementTree
from xml.etree import ElementTree as elementTree

import requests
import requests_toolbelt
import xmltodict
from pan import xapi
from pan.xapi import PanXapiError

from .exceptions import SkilletLoaderException
from .exceptions import LoginException
from .skillet.base import Skillet


class Panoply:
    """
    Panoply is a wrapper around pan-python PanXAPI class to provide additional, commonly used functions
    """

    def __init__(self, hostname, api_username, api_password, api_port=443, serial_number=None):
        """
        Initialize a new panos object
        :param hostname: hostname or ip address of target device`
        :param api_username: username
        :param api_password: password
        :param api_port: port to use for target device
        :param serial_number: Serial number of target device if proxy through panorama
        """
        self.hostname = hostname
        self.user = api_username
        self.pw = api_password
        self.port = api_port
        self.serial_number = serial_number
        self.key = ''
        self.debug = False
        self.serial = serial_number
        self.connected = False
        self.facts = {}

        try:
            self.xapi = xapi.PanXapi(api_username=self.user, api_password=self.pw, hostname=self.hostname,
                                     port=self.port, serial=self.serial_number)
        except PanXapiError:
            print('Invalid Connection information')
            raise LoginException('Invalid connection parameters')
        else:
            self.connect(allow_offline=True)

    def connect(self, allow_offline=False) -> None:
        """
        Attempt to connect to this device instance
        :param allow_offline: Do not raise an exception if this device is offline
        :return: None
        """
        try:
            self.key = self.xapi.keygen()
            self.facts = self.get_facts()
        except PanXapiError as pxe:
            err_msg = str(pxe)
            if '403' in err_msg:
                raise LoginException('Invalid credentials logging into device')
            else:
                if allow_offline:
                    print('FYI - Device is not currently available')
                    self.connected = False
                else:
                    raise SkilletLoaderException('Could not connect to device!')
        else:
            self.connected = True

    def commit(self) -> None:
        """
        Perform a commit operation on this device instance
        :return: None
        """
        try:
            self.xapi.commit(cmd='<commit></commit>', sync=True, timeout=600)
            results = self.xapi.xml_result()
            doc = elementTree.XML(results)
            embedded_result = doc.find('result')
            if embedded_result is not None:
                commit_result = embedded_result.text
                print(f'Commit result is {commit_result}')
                if commit_result == 'FAIL':
                    raise SkilletLoaderException(self.xapi.status_detail)
        except PanXapiError as pxe:
            print(pxe)
            raise SkilletLoaderException('Could not commit configuration')

    def set_at_path(self, name: str, xpath: str, xml_str: str) -> None:
        """
        Insert XML into the configuration tree at the specified xpath
        :param name: name of the snippet - used in logging and debugging only
        :param xpath: full xpath where the xml element will be inserted
        :param xml_str: string representation of the XML element to insert
        :return: None
        """

        try:
            print(f'Loading xpath {xpath}')
            self.xapi.set(xpath=xpath, element=self.sanitize_element(xml_str))
            if self.xapi.status_code == '7':
                raise SkilletLoaderException(f'xpath {xpath} was NOT found for skillet: {name}')
        except PanXapiError as pxe:
            raise SkilletLoaderException(f'Could not push skillet {name} / snippet {xpath}! {pxe}')

    def execute_cmd(self, cmd: str, params: dict) -> bool:
        """
        Execute the given cmd using the xapi.
        :param cmd: Valid options are 'set', 'edit', 'override', 'move', 'rename', 'clone'
        :param params: valid parameters for the given cmd type
        :return: bool True on success, raises SkilletLoaderException
        """
        if cmd not in ('set', 'edit', 'override', 'move', 'rename', 'clone'):
            raise SkilletLoaderException('Invalid cmd type given to execute_cmd')

        # this code happily borrowed from ansible-pan module
        # https://raw.githubusercontent.com/PaloAltoNetworks/ansible-pan/develop/library/panos_type_cmd.py
        cmd = params['cmd']
        func = getattr(self.xapi, cmd)

        kwargs = {
            'xpath': ''.join(params['xpath'].strip().split('\n')),
            'extra_qs': params.get('extra_qs', dict())
        }

        try:
            if cmd in ('set', 'edit', 'override'):
                kwargs['element'] = params['element'].strip()

            if cmd in ('move',):
                kwargs['where'] = params['where']
                # dst is optional
                kwargs['dst'] = params.get('dst', None)

            if cmd in ('rename', 'clone'):
                if 'new_name' in params:
                    kwargs['newname'] = params['new_name']
                else:
                    kwargs['newname'] = params['newname']

            if cmd in ('clone',):
                kwargs['xpath_from'] = params['xpath_from']

        except KeyError as ke:
            print(f'Invalid parameters passed to execute_cmd')
            print(ke)
            return False

        try:
            print('here we go')
            func(**kwargs)
        except PanXapiError as e:
            print(e)
            print(f'Could not execute {cmd}')
            return False
        else:
            return True
        
    @staticmethod
    def sanitize_element(element: str) -> str:
        """
        Eliminate some undeeded characters out of the XML snippet if they appear.
        :param element: element str
        :return: sanitized element str
        """
        element = re.sub(r"\n\s+", "", element)
        element = re.sub(r"\n", "", element)

        return element

    def get_facts(self) -> dict:
        """
        Gather system info and keep on self.facts
        This gets called on every connect
        :return: dict containing all system facts
        """
        facts = {}

        # FIXME - add better error handling here
        self.xapi.op(cmd='<show><system><info></info></system></show>')

        if self.xapi.status != 'success':
            print('We have a problem!')
            raise SkilletLoaderException('Could not get facts from device!')

        results_xml_str = self.xapi.xml_result()
        results = xmltodict.parse(results_xml_str)
        if 'system' in results:
            facts.update(results['system'])

        self.xapi.show(xpath="./devices/entry[@name='localhost.localdomain']/deviceconfig/system")
        results_xml_str = self.xapi.xml_result()
        results = xmltodict.parse(results_xml_str)
        if 'system' in results:
            facts['timezone'] = results['system'].get('timezone', 'US/Pacific')
        try:
            facts['dns-primary'] = results['system']['dns-setting']['servers']['primary']
            facts['dns-secondary'] = results['system']['dns-setting']['servers']['secondary']
        except KeyError:
            # DNS is not configured on the host, but we will need it later for some noob operations
            facts['dns-primary'] = '1.1.1.1'
            facts['dns-secondary'] = '1.0.0.1'

        return facts

    def load_baseline(self) -> bool:
        """
        Load baseline config that contains ONLY connecting username / password
        use device facts to determine which baseline template to load
        see template/panos/baseline_80.xml for example
        :param self:
        :return: bool true on success
        """
        if not self.connected:
            self.connect()

        if 'sw-version' not in self.facts:
            raise SkilletLoaderException('Could not determine sw-version to load baseline configuration!')

        version = self.facts['sw-version']
        context = dict()
        context['FW_NAME'] = self.facts['hostname']
        context['ADMINISTRATOR_USERNAME'] = self.user
        context['ADMINISTRATOR_PASSWORD'] = self.pw
        if self.facts['is-dhcp'] == 'no':
            context['MGMT_TYPE'] = 'static'
            context['MGMT_IP'] = self.facts['ip-address']
            context['MGMT_MASK'] = self.facts['netmask']
            context['MGMT_DG'] = self.facts['default-gateway']
            context['DNS_1'] = self.facts['dns-primary']
            context['DNS_2'] = self.facts['dns-secondary']

        if '8.0' in version:
            # load the 8.0 baseline with
            skillet_dir = 'baseline_80'
        elif '8.1' in version:
            # load the 8.1 baseline with
            skillet_dir = 'baseline_81'
        elif '9.0' in version:
            # load the 9.0 baseline with
            skillet_dir = 'baseline_90'
        else:
            print('Could not determine sw-version for baseline load')
            return False

        template_path = Path(__file__).parent.joinpath('..', 'skillets', 'panos', skillet_dir)
        print(f'{template_path.resolve()}')
        baseline_skillet = Skillet(str(template_path.resolve()))
        snippets = baseline_skillet.get_snippets()
        snippet = snippets[0]
        print(f'Loading {snippet.name}')
        file_contents = snippet.template(context)
        self.import_file(snippet.name, file_contents, 'configuration')
        self.load_config(snippet.name)

        return True

    def import_file(self, filename: str, file_contents: (str, bytes), category: str) -> bool:
        """
        Import the given file into this device
        :param filename:
        :param file_contents:
        :param category: 'configuration'
        :return: bool True on success
        """
        params = {
            'type': 'import',
            'category': category,
            'key': self.key
        }

        mef = requests_toolbelt.MultipartEncoder(
            fields={
                'file': (filename, file_contents, 'application/octet-stream')
            }
        )

        r = requests.post(
            'https://' + self.hostname + '/api/',
            verify=False,
            params=params,
            headers={'Content-Type': mef.content_type},
            data=mef
        )

        # if something goes wrong just raise an exception
        r.raise_for_status()

        resp = ElementTree.fromstring(r.content)

        if resp.attrib['status'] == 'error':
            raise SkilletLoaderException(r.content)

        return True

    def load_config(self, filename: str) -> bool:
        """
        Loads the named configuration file into this device
        :param filename: name of the configuration file on the device to load. Note this filename must already exist
        on the target device
        :return: bool True on success
        """

        cmd = f'<load><config><from>{filename}</from></config></load>'
        self.xapi.op(cmd=cmd)
        if self.xapi.status == 'success':
            return True
        else:
            return False

    def wait_for_device_ready(self, interval=30, timeout=600) -> bool:
        """
        Loop and wait until device is ready or times out
        :param interval: how often to check in seconds
        :param timeout: how long to wait until we declare a timeout condition
        :return: boolean true on ready, false on timeout
        """
        mark = time.time()
        timeout_mark = mark + timeout

        while True:
            print(f'Checking {self.hostname} if ready...')
            try:
                self.xapi.op(cmd='<show><chassis-ready></chassis-ready></show>')
                resp = self.xapi.xml_result()
                if self.xapi.status == 'success':
                    if resp.strip() == 'yes':
                        return True
            except PanXapiError:
                print(f'{self.hostname} is not yet ready...')

            if time.time() > timeout_mark:
                return False

            print(f'Waiting for {self.hostname} to become ready...')
            time.sleep(interval)

    def update_dynamic_content(self, content_type: str) -> bool:
        """
        Check for newer dynamic content and install if found
        :param content_type: type of content to check. can be either: 'content', 'anti-virus', 'wildfire'
        :return: bool True on success
        """
        try:
            version_to_install = self.check_content_updates(content_type)
            if version_to_install is None:
                print('Latest content version is already installed')
                return True

            print('Downloading latest and greatest')
            cmd = f'<request>' \
                  f'<{content_type}><upgrade><download><latest/></download></upgrade></{content_type}>' \
                  f'</request>'

            self.xapi.op(cmd=cmd)
            results_element = self.xapi.element_result
            job_element = results_element.find('.//job')
            if job_element is not None:
                job_id = job_element.text
                if not self.wait_for_job(job_id):
                    raise SkilletLoaderException('Could not update dynamic content')

            print(f'Installing latest and greatest ')
            install_cmd = f'<request><content><upgrade><install>' \
                          f'<version>latest</version><commit>no</commit></install></upgrade></content></request>'

            self.xapi.op(cmd=install_cmd)
            results_element = self.xapi.element_result
            job_element = results_element.find('.//job')
            if job_element is not None:
                job_id = job_element.text
                if not self.wait_for_job(job_id):
                    raise SkilletLoaderException('Could not install dynamic content')
            else:
                print(f'No job returned to track')

            return True

        except PanXapiError:
            print('Could not check for updated dynamic content')
            return False

    def check_content_updates(self, content_type: str) -> (str, None):
        """
        Iterate through all available content of the specified type, locate and return the version with the highest
        version number. If that version is already installed, return None as no further action is necessary
        :param content_type: type of content to check
        :return: version-number to download and install or None if already at the latest
        """
        latest_version = ''
        latest_version_first = 0
        latest_version_second = 0
        latest_version_current = 'no'
        try:
            print('Checking for latest content...')
            self.xapi.op(cmd=f'<request><{content_type}><upgrade><check/></upgrade></{content_type}></request>')
            er = self.xapi.element_root
            for entry in er.findall('.//entry'):
                version = entry.find('./version').text
                current = entry.find('./current').text
                # version will have the format 1234-1234
                version_parts = version.split('-')
                version_first = int(version_parts[0])
                version_second = int(version_parts[1])
                if version_first > latest_version_first and version_second > latest_version_second:
                    latest_version = version
                    latest_version_first = version_first
                    latest_version_second = version_second
                    latest_version_current = current

            if latest_version_current == 'yes':
                return None
            else:
                return latest_version

        except PanXapiError:
            return None

    def wait_for_job(self, job_id: str, interval=10, timeout=600) -> bool:
        """
        Loops until a given job id is completed. Will timeout after the timeout period if the device is
        offline or otherwise unavailable.
        :param job_id: id the job to check and wait for
        :param interval: how long to wait between checks
        :param timeout: how long to wait with no response before we give up
        :return: bool true on content updated, false otherwise
        """
        mark = time.time()
        timeout_mark = mark + timeout
        print(f'Waiting for job id: {job_id} to finish...')
        while True:
            try:
                self.xapi.op(cmd=f'<show><jobs><id>{job_id}</id></jobs></show>')
            except PanXapiError:
                print(f'Could not locate job with id: {job_id}')
                return False

            if self.xapi.status == 'success':
                job_element = self.xapi.element_result
                job_status_element = job_element.find('.//status')
                if job_status_element is not None:
                    job_status = job_status_element.text
                    if job_status == 'FIN':
                        print('Job is now complete')
                        return True
                    elif job_status == 'ACT':
                        job_progress_element = job_element.find('.//progress')
                        if job_progress_element is not None:
                            job_progress = job_progress_element.text
                            print(f'Progress is currently: {job_progress}')
                else:
                    print('No job status element to be found!')
                    return False
            else:
                print(f'{self.xapi.xml_result()}')
                if time.time() > timeout_mark:
                    return False
                print('Waiting a bit longer')

            time.sleep(interval)
