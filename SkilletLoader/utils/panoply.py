import re

import xmltodict
from pan import xapi

from .exceptions import LoaderException


class Panoply:
    """
    PANOS Device. Could be a firewall or PANORAMA.
    """

    def __init__(self, hostname, api_username, api_password, api_port):
        """
        Initialize a new panos object
        :param hostname: NAME:PORT combination (ex. l72.16.0.1:443)
        :param api_username: username
        :param api_password: password
        """
        self.hostname = hostname
        self.user = api_username
        self.pw = api_password
        self.port = api_port
        self.key = ''
        self.debug = False
        self.xapi = xapi.PanXapi(api_username=self.user, api_password=self.pw, hostname=self.hostname, port=self.port)
        self.key = self.xapi.keygen()
        self.facts = self.get_facts()

    def commit(self):
        try:
            self.xapi.commit('<commit></commit>', sync=True)
        except xapi.PanXapiError as pxe:
            print(pxe)
            raise LoaderException('Could not commit configuration')

    def set_at_path(self, name, xpath, elementvalue):

        try:
            self.xapi.set(xpath=xpath, element=self.sanitize_element(elementvalue))
            if self.xapi.status_code == '7':
                raise LoaderException(f'xpath {xpath} was NOT found for skillet: {name}')
        except xapi.PanXapiError as pxe:
            raise LoaderException(f'Could not push skillet {name} / snippet {xpath}! {pxe}')

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
        # FIXME - add better error handling here
        self.xapi.op(cmd='<show><system><info></info></system></show>')

        if self.xapi.status != 'success':
            print('We have a problem!')
            raise LoaderException('Could not get facts from device!')

        results_xml_str = self.xapi.xml_result()
        results = xmltodict.parse(results_xml_str)
        if 'system' in results:
            return results['system']

    def load_baseline(self) -> bool:
        """
        Load baseline config that contains ONLY connecting username / password
        use device facts to determine which baseline template to load
        see template/panos/baseline_80.xml for example
        :param self:
        :return: bool
        """

        if 'sw-versipon' not in self.facts:
            raise LoaderException('Could not determine sw-version to load baseline configuration!')

        version = self.facts['sw-version']
        if '8.0' in version:
            # load the 8.0 baseline with
            pass
        elif '8.1' in version:
            # load the 8.1 baseline with
            pass
        elif '9.0' in version:
            # load the 9.0 baseline with
            pass
        else:
            print('Could not determine sw-version for baseline load')
            return False

        return True

