import re

from pan import xapi

from .exceptions import LoaderException


class Panos:
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
        self.url = "https://{}/api".format(hostname)
        self.hostname = hostname
        self.user = api_username
        self.pw = api_password
        self.port = api_port
        self.key = ''
        self.debug = False
        self.xapi = None
        self.connect()

    def connect(self):
        """
        Connect to a PANOS device and retrieve an API key.
        :return: API Key
        """

        self.xapi = xapi.PanXapi(api_username=self.user, api_password=self.pw, hostname=self.hostname, port=self.port)
        self.key = self.xapi.keygen()
        return self.key

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
    def sanitize_element(element):
        """
        Eliminate some undeeded characters out of the XML snippet if they appear.
        :param element: element str
        :return: sanitized element str
        """
        element = re.sub("\n\s+", "", element)
        element = re.sub("\n", "", element)

        return element
