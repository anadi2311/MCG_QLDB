from logging import basicConfig, getLogger, INFO

from botocore.exceptions import ClientError

from pyqldb.driver.qldb_driver import QldbDriver
from constants import Constants

logger = getLogger(__name__)
basicConfig(level=INFO)


def create_qldb_driver(ledger_name=Constants.LEDGER_NAME, region_name=None, endpoint_url=None, boto3_session=None):
    """
    Create a QLDB driver for executing transactions.
    :type ledger_name: str
    :param ledger_name: The QLDB ledger name.
    :type region_name: str
    :param region_name: See [1].
    :type endpoint_url: str
    :param endpoint_url: See [1].
    :type boto3_session: :py:class:`boto3.session.Session`
    :param boto3_session: The boto3 session to create the client with (see [1]).
    :rtype: :py:class:`pyqldb.driver.qldb_driver.QldbDriver`
    :return: A QLDB driver object.
    [1]: `Boto3 Session.client Reference <https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html#boto3.session.Session.client>`.
    """
    qldb_driver = QldbDriver(ledger_name=ledger_name, region_name=region_name, endpoint_url=endpoint_url,
                             boto3_session=boto3_session)
    return qldb_driver


if __name__ == '__main__':
    """
    Connect to a given ledger using default settings.
    """
    try:
        with create_qldb_driver() as driver:
            logger.info('Listing table names ')
            for table in driver.list_tables():
                logger.info(table)
    except ClientError:
        logger.exception('Unable to list tables.')
