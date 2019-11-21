import time
import logging
from .sensordoc import generate_hash

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def query_sensor_db(sensor_db, event_time_range):
    """Query Sensor DB for Event's time range and generate Sensor Document's Hash

    :param: sensor_db: Sensor Database Client
    :type: InfluxDBClient instance
    :param: event_time_range: A dictionary of ISO Format Timestamps and name of `bizLocation`
    :param: event_time_range:
            {
                'from_time': '2019-01-01T00:00:00.000Z',
                'to_time': '2019-01-01T00:01:00Z.000',
                'bizLocation: 'urn:epc:id:sgln:bizLocation.ACME.1'
            }
    :type: dict
    :returns: dictionary with a list of data points for selected `bizLocation`, if they exist and generated hash
                {
                    'data_points': list of data points for `bizLocation`,
                    'hash': SHA256 string of generated Sensor Document
                }
    :rtype: dict
    """

    logger.info('Querying Sensor DB for obtained Time Range between Events')

    # Generalized Query for Sensor DB to get data points between a particular time range
    QUERY = 'SELECT * FROM env WHERE time >= $from_time AND time <= $to_time AND (bizLocation=$prev OR bizLocation=$present)'

    # Set Binding Parameters viz. `from_time` and `to_time` for query
    params = {
        'from_time': event_time_range['from_time'],
        'to_time': event_time_range['to_time'],
        'prev': event_time_range['bizLocation']['prev'],
        'present': event_time_range['bizLocation']['present']
    }

    # Query the Sensor DB
    results = sensor_db.query(QUERY, bind_params=params)

    if len(list(results)) > 0:
        # If Data Points do Exist.
        # Query the Data with Meta-Data (tags) `bizLocation`
        # prev_bizloc_points = list(results.get_points(tags={'bizLocation': event_time_range['bizLocation']['prev']}))
        # logger.debug('No. of Data Points for Previous Event Time Range: {}'.format(len(prev_bizloc_points)))
        # present_bizloc_points = list(results.get_points(tags={'bizLocation': event_time_range['bizLocation']['present']}))
        # logger.debug('No. of Data Points for Present Event Time Range: {}'.format(len(present_bizloc_points)))
        # bizloc_points = prev_bizloc_points + present_bizloc_points
        bizloc_points = list(results)[0]
        # pprint.pprint(bizloc_points)
        logger.debug('No. of Data Points for Previous Event Time Range: {}'.format(len(bizloc_points)))
        # generate SHA256 Hash for Sensor Document
        hash_of_doc = generate_hash(bizloc_points)

        return {'data_points': bizloc_points, 'hash': hash_of_doc}
    else:
        logger.info('No Data Points Exist for the given Event Time Range')
        return None


def update_sensordb(sensor_db, database_name, results):
    """Update the Sensor DB with the Generated Hash that was sent to Blockchain

    :param: sensor_db: Sensor Database Client
    :type: InfluxdbClient instance
    :param: database_name: database name where the data needs to be sent
    :type: str
    :param: results: dictionary returned by `query_sensor_db`
    :type: dict
    :returns: True, if successful Write back into Sensor DB with new `hash` field
    :rtype: bool
    """
    # Empty list to accumulate all the data points
    batch = []

    for point in results['data_points']:
        # Structure according to `influxdb-python` API
        _update_json_body = {
            'measurement': 'env',
            'time': point['time'],
            'tags': {
                'bizLocation': point['bizLocation'],
                'city': point['city'],
                'country': point['country'],
                'company': point['company'],
                'sID': point['sID'],
                'sName': point['sName'],
                'site': point['site']
            },
            'fields': {
                'temp': float(point['temp']),
                'humid': float(point['humid']),
                'hash': results['hash']
            }
        }
        # add each point into the batch list
        batch.append(_update_json_body)
    try:
        time.sleep(2.0)
        if sensor_db.write_points(batch, time_precision='s', database=database_name):
            return True
        else:
            logger.error('Cannot Re-Write to Sensor DB')
            return False
    except Exception as e:
        logger.error('Error while re-writing data back to Sensor DB')
        logger.error(e)
        return False
