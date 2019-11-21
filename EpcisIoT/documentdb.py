import logging
from pymongo import DESCENDING

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def obtain_time_duration(collection, new_document):
    """obtain a time duration between the recent events of the same bizLocation

    :param: collection: MongoDB collection to parse
    :type: pymongo.collection
    :param: new inserted document detected by change streams
    :type: dict
    :returns: dictionary of timestamps relevant for sensor DB
    :rtype: dict
    """

    # Obtain the previously existing two document for the incoming bizLocation
    # Sort them in descending order
    # The first in the list is the newly inserted document detected by Change Streams
    # the second document is of interest
    prev_documents = collection.find({'epcList.epc': new_document['epcList'][0]['epc']}).limit(2).sort([("eventTime", DESCENDING)])

    if prev_documents is not None:
        # if there is a previous set of documents
        prev_doc_list = list(prev_documents)
        # print(prev_doc_list)
        if len(prev_doc_list) == 1:
            logger.info('Only Single entry exists for Product.. It implies it is the a new product with no previous events.')
            return None
        else:
            logger.debug('Previous BizLocation of Product: {}, Present BizLocation of Product: {}'.format(
                prev_doc_list[1]['bizLocation']['id'], new_document['bizLocation']['id']))
            logger.debug('Time Duration: From {} to {}'.format(prev_doc_list[1]['eventTime'], new_document['eventTime']))

            # make the dictionary to return
            duration = {
                'bizLocation': {
                    'prev': prev_doc_list[1]['bizLocation']['id'],
                    'present': new_document['bizLocation']['id']
                },
                'from_time':  prev_doc_list[1]['eventTime'].isoformat(timespec='milliseconds') + 'Z',
                'to_time': new_document['eventTime'].isoformat(timespec='milliseconds') + 'Z'
            }
            # print(duration)
            return duration
    else:
        logger.info('No Previous Information of Event Found')
        return None
