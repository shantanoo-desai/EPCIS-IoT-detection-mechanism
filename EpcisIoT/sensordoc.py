import logging
import hashlib
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def generate_hash(data_points):
    """create a Sensor Document and its SHA256 hash

    :param: data_points: a list of data points from Sensor DB
    :type: list of dictionaries from Sensor DB's query ResultSet
    :returns: doc_hash: a SHA256 hash of the Sensor Document
    :rtype: str
    """
    """Document Format:
        [
            {
                'bizLocation': <str>,
                'sensor': {
                    'ID': <str>,
                    'make': <str>
                },
                'measurement': {
                        'timestamp': <rfc3339_str>,
                        'humid': <float>,
                        'temp': <float>
                }
            }
        ]
    """
    sensor_doc = []

    for point in data_points:
        _sub_doc = {
            'bizLocation': point['bizLocation'],
            'sensor': {
                'ID': point['sID'],
                'make': point['sName']
            },
            'measurement': {
                'timestamp': point['time'],
                'humid': point['humid'],
                'temp': point['temp']
            }
        }

        sensor_doc.append(_sub_doc)
    # print(sensor_doc)
    logger.info('Generating Hash of Sensor Document')
    doc_hash = hashlib.sha256(json.dumps(sensor_doc).encode('utf-8')).hexdigest()
    logger.debug('SHA256 Hash for Sensor Doc: {}'.format(doc_hash))

    return doc_hash
