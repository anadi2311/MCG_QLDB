from logging import basicConfig, getLogger, INFO

from boto3 import client

from constants import Constants

logger = getLogger(__name__)
basicConfig(level=INFO)
qldb_client = client('qldb')


def describe_ledger(ledger_name):
    """
    Describe a ledger.
    :type ledger_name: str
    :param ledger_name: Name of the ledger to describe.
    """
    logger.info('describe ledger with name: {}.'.format(ledger_name))
    result = qldb_client.describe_ledger(Name=ledger_name)
    result.pop('ResponseMetadata')
    logger.info('Success. Ledger description: {}.'.format(result))
    return result


if __name__ == '__main__':
    """
    Describe a QLDB ledger.
    """
    try:
        describe_ledger(Constants.LEDGER_NAME)
    except Exception:
        logger.exception('Unable to describe a ledger.')