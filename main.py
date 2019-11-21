import sys
import os
import time
import logging
import concurrent.futures

import toml
from pymongo import MongoClient
from influxdb import InfluxDBClient

from EpcisIoT.documentdb import obtain_time_duration
from EpcisIoT.sensordb import query_sensor_db, update_sensordb
from EpcisIoT.blockchain import send_to_bc

# Disable InsecureRequestWarning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
)
stream_handler = logging.StreamHandler(stream=sys.stdout)
stream_handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)


def insert_change_stream(bc_endpoint, sensor_database_name):
    """Listen to any Insertion changes to Document DB and perform Depending Tasks

    :param: bc_endpoint: Blockchain Endpoint
    :type: str
    :param: sensor_database_name
    :type: str
    """
    logger.debug('Listening Changes for DB:{}, Collection: {}'.format(
        docdb_conf['dbName'], docdb_conf['collection']))

    epc_repo = document_db[docdb_conf['dbName']]
    eventdata_collection = epc_repo[docdb_conf['collection']]

    # Stream Pipeline
    pipeline = [
        {'$match': {'operationType': 'insert'}}
    ]

    try:
        for document in eventdata_collection.watch(
                pipeline=pipeline, full_document='updateLookup'):

            logger.debug('New Event for EPC ID: {}'.format(
                document['fullDocument']['epcList'][0]['epc']))

            event_duration = obtain_time_duration(
                eventdata_collection,
                document['fullDocument'])
            time.sleep(0.1)

            if event_duration is not None:
                with concurrent.futures.ThreadPoolExecutor() as executor:

                    # Generate Sensor Doc and Hash
                    sensordb_result = executor.submit(
                        query_sensor_db,
                        sensor_db,
                        event_duration).result()

                    # Submit Hash to Blockchain API
                    if sensordb_result is not None:
                        bc_result = executor.submit(
                            send_to_bc,
                            bc_endpoint,
                            sensordb_result['hash']).result()
                        if bc_result:
                            logger.info('Sent Hash to Blockchain')

                        # Update SensorDB with Hash
                        updated_sensor_db = executor.submit(
                            update_sensordb,
                            sensor_db,
                            sensor_database_name,
                            sensordb_result).result()

                        if updated_sensor_db:
                            logger.info('Successful Re-Write to Sensor DB with Hash')
                            logger.info('Saving Information to Document Database')
                            hash_meta_data = {
                                'epc': document['fullDocument']['epcList'][0]['epc'],
                                'sensor': {
                                    'hash': sensordb_result['hash']
                                },
                                'event': event_duration
                            }
                            inserted_doc_id = document_db.blockchain.HashData.insert_one(hash_meta_data).inserted_id
                            logger.debug('Blockchain + Sensor Data inserted into Database with ID: {}'.format(inserted_doc_id))
    except KeyboardInterrupt:
        keyboard_shutdown()


def keyboard_shutdown():
    logger.info('Interrupted by CTRL+C')
    try:
        document_db.close()
        sensor_db.close()
        sys.exit(0)
    except SystemExit:
        os._exit(0)


if __name__ == '__main__':
    logger.info('Starting Script for EPCIS+Sensor+Blockchain Application')
    time.sleep(1.0)

    logger.info('Reading Configuration File')

    with open('config.production.toml') as conf_file:
        CONF = toml.load(conf_file)

    # all subsystem configurations
    docdb_conf = CONF['DocumentDB']
    sensordb_conf = CONF['SensorDB']
    blockchain_conf = CONF['Blockchain']

    logger.info('Setting up Document DB Connection')
    try:

        if 'credentials' in docdb_conf:
            logger.info('Creating Client for Document DB with Credentials')
            document_db = MongoClient(
                        host=docdb_conf['host'],
                        port=docdb_conf['port'],
                        username=docdb_conf['credentials']['username'],
                        password=docdb_conf['credentials']['password']
            )
        else:
            logger.info('Creating Client for Document DB without Credentials')
            document_db = MongoClient(
                        host=docdb_conf['host'],
                        port=docdb_conf['port']
            )
    except Exception as e:
        logger.error('Error while creating Client for Document DB')
        logger.error(e)
        sys.exit(1)
    time.sleep(0.1)

    logger.info('Creating SensorDB Connection')
    try:
        if 'credentials' in sensordb_conf:
            logger.info('Creating Client for Sensor DB with Credentials')
            sensor_db = InfluxDBClient(
                        host=sensordb_conf['host'],
                        port=sensordb_conf['port'],
                        ssl=sensordb_conf['credentials']['ssl'],
                        verify_ssl=sensordb_conf['credentials']['verify_ssl'],
                        username=sensordb_conf['credentials']['username'],
                        password=sensordb_conf['credentials']['password'],
                        database=sensordb_conf['dbName']
            )
        else:
            logger.info('Creating Client for Sensor DB without Credentials')
            sensor_db = InfluxDBClient(
                        host=sensordb_conf['host'],
                        port=sensordb_conf['port'],
                        database=sensordb_conf['dbName']
            )
    except Exception as e:
        logger.error('Error while creating Client for Sensor DB')
        logger.error(e)
        document_db.close()
        sys.exit(1)

    logger.info('Listening for new EPC Document Insertions in Document DB')
    time.sleep(1.0)
    insert_change_stream(blockchain_conf['endpoint'], sensordb_conf['dbName'])
