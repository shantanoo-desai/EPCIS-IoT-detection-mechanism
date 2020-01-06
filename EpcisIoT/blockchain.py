import requests
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def send_to_bc(api, generated_hash):
    """Send Generated Hash to Blockchain API

    :param api: the endpoint for the Blockchain Network
    :type: str
    :param generated_hash: the generated hash of the sensor document
    :type: str
    :returns: True, if HTTP POST is successful
    :rtype: bool
    """

    data = {'hash': generated_hash}
    r = requests.post(api, data=data)
    if r.status_code == 200:
        logger.info('BC Response: ' + r.text)
        return True
    else:
        return False
