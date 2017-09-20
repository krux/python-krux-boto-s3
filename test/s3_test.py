# -*- coding: utf-8 -*-
#
# © 2015-2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import unittest

#
# Third party libraries
#

from mock import MagicMock, call, patch

#
# Internal libraries
#

from krux_boto.boto import Boto
from krux_s3.s3 import S3, NAME, get_s3


class GetS3Test(unittest.TestCase):
    FAKE_LOG_LEVEL = 'critical'
    FAKE_ACCESS_KEY = 'FAKE_ACCESS_KEY'
    FAKE_SECRET_KEY = 'FAKE_SECRET_KEY'
    FAKE_REGION = 'us-gov-west-1'  # This is a region that Krux will never use.

    _FAKE_COMMAND = [
        'krux-boto',
        '--boto-log-level', FAKE_LOG_LEVEL,
        '--boto-access-key', FAKE_ACCESS_KEY,
        '--boto-secret-key', FAKE_SECRET_KEY,
        '--boto-region', FAKE_REGION,
        '--foo',  # Adding an extra CLI argument to make sure this gets ignored without an error
    ]

    def setUp(self):
        self.args = MagicMock(
            boto_log_level=self.FAKE_LOG_LEVEL,
            boto_access_key=self.FAKE_ACCESS_KEY,
            boto_secret_key=self.FAKE_SECRET_KEY,
            boto_region=self.FAKE_REGION
        )

        self.logger = MagicMock()
        self.stats = MagicMock()

    @patch('krux_s3.s3.get_boto')
    def test_get_s3_with_args(self, mock_get_boto):
        """
        get_s3() correctly passes the arguments to S3 contructor
        """
        mock_get_boto.return_value = MagicMock(spec=Boto)

        s3 = get_s3(self.args, self.logger, self.stats)

        self.assertEqual(self.logger, s3._logger)
        self.assertEqual(self.stats, s3._stats)
        self.assertEqual(mock_get_boto.return_value, s3.boto)

        mock_get_boto.assert_called_once_with(self.args, self.logger, self.stats)

    @patch('sys.argv', _FAKE_COMMAND)
    @patch('krux_s3.s3.get_parser')
    @patch('krux_s3.s3.get_logger')
    @patch('krux_s3.s3.get_stats')
    @patch('krux_s3.s3.get_boto')
    def test_get_s3_without_args(self, mock_get_boto, mock_get_stats, mock_get_logger, mock_get_parser):
        """
        get_s3() correctly parses the CLI arguments and pass them to S3 contructor
        """
        mock_get_parser.return_value.parse_known_args.return_value = [self.args]
        mock_get_stats.return_value = self.stats
        mock_get_logger.return_value = self.logger
        mock_get_boto.return_value = MagicMock(spec=Boto)

        s3 = get_s3()

        self.assertEqual(self.logger, s3._logger)
        self.assertEqual(self.stats, s3._stats)
        self.assertEqual(mock_get_boto.return_value, s3.boto)

        mock_get_boto.assert_called_once_with(self.args, self.logger, self.stats)


class S3Test(unittest.TestCase):
    TEST_SECURITY_TOKEN = 'test-token'
    TEST_BUCKET = 'test-bucket'
    TEST_REGION = 'test-region-1'
    TEST_PREFIX = 'test'
    TEST_KEY = 'test-key'
    TEST_CONTENT = 'test-content'

    def setUp(self):
        self._logger = MagicMock()
        self._stats = MagicMock()

        self._boto = MagicMock(
            cli_region=self.TEST_REGION,
        )

        with patch('krux_s3.s3.isinstance', return_value=True):
            self._s3 = S3(
                boto=self._boto,
                security_token=self.TEST_SECURITY_TOKEN,
                logger=self._logger,
                stats=self._stats,
            )

    def test_init(self):
        """
        __init__() sets all values correctly.
        """
        self.assertEqual(NAME, self._s3._name)
        self.assertEqual(self._logger, self._s3._logger)
        self.assertEqual(self._stats, self._s3._stats)
        self.assertEqual(self._boto, self._s3.boto)
        self.assertEqual(self.TEST_SECURITY_TOKEN, self._s3._security_token)
        self.assertEqual(None, self._s3._conn)
        self.assertEqual({}, self._s3._buckets)

    def test_init_no_arg(self):
        """
        __init__() correctly creates a logger and a stats when not provided.
        """
        with patch('krux_s3.s3.isinstance', return_value=True):
            self._s3 = S3(
                boto=self._boto
            )

        self.assertIsNone(self._s3._security_token)

    def test_init_boto_error(self):

        """
        __init__() properly errors out when krux_boto.boto.Boto is not passed
        """
        with self.assertRaises(TypeError) as e:
            self._s3 = S3(
                boto=self._boto
            )

        self.assertEqual('krux_s3.s3.S3 only supports krux_boto.boto.Boto', str(e.exception))

    def test_get_connection(self):
        """
        _get_connection() properly returns a connection object and caches it
        """
        mock_connection = self._boto.s3.connection.S3Connection
        expected = mock_connection.return_value
        actual = self._s3._get_connection()

        self.assertEqual(expected, actual)
        self.assertEqual(expected, self._s3._conn)
        mock_connection.assert_called_once_with(security_token=self.TEST_SECURITY_TOKEN)

    def test_get_connection_cached(self):
        """
        _get_connection() properly uses the cache when it exists
        """
        mock_connection = self._boto.s3.connection.S3Connection
        expected = MagicMock()
        self._s3._conn = expected

        self.assertEqual(expected, self._s3._get_connection())
        self.assertFalse(mock_connection.called)

    def test_get_bucket(self):
        """
        _get_bucket() properly returns a bucket and caches it
        """
        mock_get_bucket = self._boto.s3.connection.S3Connection.return_value.get_bucket
        expected = mock_get_bucket.return_value
        actual = self._s3._get_bucket(self.TEST_BUCKET)

        self.assertEqual(expected, actual)
        self.assertEqual(expected, self._s3._buckets[self.TEST_BUCKET])
        mock_get_bucket.assert_called_once_with(self.TEST_BUCKET)

    def test_get_bucket_cached(self):
        """
        _get_bucket() properly uses the cache when it exists
        """
        mock_get_bucket = self._boto.s3.connection.S3Connection.return_value.get_bucket
        expected = MagicMock()
        self._s3._buckets[self.TEST_BUCKET] = expected
        actual = self._s3._get_bucket(self.TEST_BUCKET)

        self.assertEqual(expected, actual)
        self.assertFalse(mock_get_bucket.called)

    def test_get_keys(self):
        """
        get_keys() properly returns a list of keys
        """
        mock_get_bucket = MagicMock()
        mock_get_bucket.return_value.get_all_keys.return_value = [self.TEST_KEY]

        self._s3._get_bucket = mock_get_bucket
        keys = self._s3.get_keys(self.TEST_BUCKET, prefix=self.TEST_PREFIX)

        self.assertEqual(keys, [self.TEST_KEY])
        mock_get_bucket.assert_called_once_with(self.TEST_BUCKET)
        mock_get_bucket.return_value.get_all_keys.assert_called_once_with(prefix=self.TEST_PREFIX)
        self._logger.info.assert_called_once_with('Found following keys: %s', [self.TEST_KEY])

    def test_create_key(self):
        """
        create_key() properly creates a key under the given bucket with the given content
        """
        mock_get_bucket = MagicMock()
        self._s3._get_bucket = mock_get_bucket

        mock_key = self._boto.s3.key.Key.return_value
        mock_key.exists.return_value = False

        key = self._s3.create_key(self.TEST_BUCKET, self.TEST_KEY, self.TEST_CONTENT)

        self.assertEqual(mock_key, key)
        mock_get_bucket.assert_called_once_with(self.TEST_BUCKET)
        self._boto.s3.key.Key.assert_called_once_with(mock_get_bucket.return_value)
        self.assertEqual(self.TEST_KEY, key.key)
        mock_key.set_contents_from_string.assert_called_once_with(self.TEST_CONTENT)
        self._logger.info.assert_called_once_with(
            'Created a key %s in bucket %s with following contents: %s',
            self.TEST_KEY, self.TEST_BUCKET, self.TEST_CONTENT
        )

    def test_create_key_duplicate(self):
        """
        create_key() properly throws an error when there is another key with the same name
        """
        mock_key = self._boto.s3.key.Key.return_value
        mock_key.exists.return_value = True

        with self.assertRaises(ValueError) as e:
            self._s3.create_key(self.TEST_BUCKET, self.TEST_KEY, self.TEST_CONTENT)

        self.assertEqual(
            'Entry {0} already exists in S3 -- delete it first'.format(self.TEST_KEY),
            str(e.exception)
        )

    def test_update_key(self):
        """
        update_key() properly update a key under the given bucket with the given content
        """
        mock_get_bucket = MagicMock()
        mock_key = mock_get_bucket.return_value.get_key.return_value
        self._s3._get_bucket = mock_get_bucket

        key = self._s3.update_key(self.TEST_BUCKET, self.TEST_KEY, self.TEST_CONTENT)

        self.assertEqual(mock_key, key)
        mock_get_bucket.assert_called_once_with(self.TEST_BUCKET)
        mock_get_bucket.return_value.get_key.assert_called_once_with(self.TEST_KEY)
        mock_key.set_contents_from_string.assert_called_once_with(self.TEST_CONTENT)
        self._logger.info.assert_called_once_with(
            'Updated a key %s in bucket %s with following contents: %s',
            self.TEST_KEY, self.TEST_BUCKET, self.TEST_CONTENT
        )

    def test_update_key_none(self):
        """
        update_key() properly throws an error when there is no key with the same name
        """
        mock_get_bucket = MagicMock()
        mock_get_bucket.return_value.get_key.return_value = None
        self._s3._get_bucket = mock_get_bucket

        with self.assertRaises(ValueError) as e:
            self._s3.update_key(self.TEST_BUCKET, self.TEST_KEY, self.TEST_CONTENT)

        self.assertEqual(
            'There are no key with name {0}'.format(self.TEST_KEY),
            str(e.exception)
        )

    def test_remove_keys(self):
        """
        remove_keys() properly deletes the keys under the given bucket
        """
        mock_get_bucket = MagicMock()

        self._s3._get_bucket = mock_get_bucket
        self._s3.remove_keys(self.TEST_BUCKET, keys=[self.TEST_KEY])

        mock_get_bucket.assert_called_once_with(self.TEST_BUCKET)
        mock_get_bucket.return_value.delete_keys.assert_called_once_with([self.TEST_KEY])
        self._logger.info.assert_called_once_with('Deleting following keys: %s', [self.TEST_KEY])
