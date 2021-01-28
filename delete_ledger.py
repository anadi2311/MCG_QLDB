
from logging import basicConfig, getLogger, INFO
from time import sleep

from boto3 import client

from constants import Constants
from describe_ledger import describe_ledger

logger = getLogger(__name__)
basicConfig(level=INFO)
qldb_client = client('qldb')

LEDGER_DELETION_POLL_PERIOD_SEC = 20


def delete_ledger(ledger_name):
    """
    Send a request to QLDB to delete the specified ledger.
    :type ledger_name: str
    :param ledger_name: Name for the ledger to be deleted.
    :rtype: dict
    :return: Result from the request.
    """
    logger.info('Attempting to delete the ledger with name: {}...'.format(ledger_name))
    result = qldb_client.delete_ledger(Name=ledger_name)
    logger.info('Success.')
    return result


def wait_for_deleted(ledger_name):
    """
    Wait for the ledger to be deleted.
    :type ledger_name: str
    :param ledger_name: The ledger to check on.
    """
    logger.info('Waiting for the ledger to be deleted...')
    while True:
        try:
            describe_ledger(ledger_name)
            logger.info('The ledger is still being deleted. Please wait...')
            sleep(LEDGER_DELETION_POLL_PERIOD_SEC)
        except qldb_client.exceptions.ResourceNotFoundException:
            logger.info('Success. The ledger is deleted.')
             logger.info(" ==================== L E D G E R ======== D E L E T E D ===============")
            break


def set_deletion_protection(ledger_name, deletion_protection):
    """
    Update an existing ledger's deletion protection.
    :type ledger_name: str
    :param ledger_name: Name of the ledger to update.
    :type deletion_protection: bool
    :param deletion_protection: Enable or disable the deletion protection.
    :rtype: dict
    :return: Result from the request.
    """
    logger.info("Let's set deletion protection to {} for the ledger with name {}.".format(deletion_protection,
                                                                                          ledger_name))
    result = qldb_client.update_ledger(Name=ledger_name, DeletionProtection=deletion_protection)
    logger.info('Success. Ledger updated: {}'.format(result))


if __name__ == '__main__':
    """
    Delete a ledger.
    """
    try:
        set_deletion_protection(Constants.LEDGER_NAME, False)
        delete_ledger(Constants.LEDGER_NAME)
        wait_for_deleted(Constants.LEDGER_NAME)
    except Exception as e:
        logger.exception('Unable to delete the ledger.')
        raise e