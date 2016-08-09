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
from krux_s3.s3 import S3, NAME


class S3Test(unittest.TestCase):
    TEST_BUCKET = 'test-bucket'
    TEST_REGION = 'test-region-1'
    TEST_PREFIX = 'test'
    TEST_KEY = 'test-key'
    TEST_CONTENT = 'test-content'

    def setUp(self):
        self._logger = MagicMock()
        self._stats = MagicMock()

        self._boto = MagicMock(
            cli_region=self.TEST_REGION
        )

        with patch('krux_s3.s3.isinstance', return_value=True):
            self._s3 = S3(
                boto=self._boto,
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
        self.assertEqual(None, self._s3._conn)
        self.assertEqual({}, self._s3._buckets)

    @patch('krux_s3.s3.get_logger')
    @patch('krux_s3.s3.get_stats')
    def test_init_no_arg(self, mock_get_stats, mock_get_logger):
        """
        __init__() correctly creates a logger and a stats when not provided.
        """
        with patch('krux_s3.s3.isinstance', return_value=True):
            self._s3 = S3(
                boto=self._boto
            )

        mock_get_logger.assert_called_once_with(NAME)
        mock_get_stats.assert_called_once_with(prefix=NAME)

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
        mock_connect_to_region = self._boto.s3.connect_to_region
        expected = mock_connect_to_region.return_value
        actual = self._s3._get_connection()

        self.assertEqual(expected, actual)
        self.assertEqual(expected, self._s3._conn)
        mock_connect_to_region.assert_called_once_with(self.TEST_REGION)

    def test_get_connection_cached(self):
        """
        _get_connection() properly uses the cache when it exists
        """
        mock_connect_to_region = self._boto.s3.connect_to_region
        expected = MagicMock()
        self._s3._conn = expected

        self.assertEqual(expected, self._s3._get_connection())
        self.assertFalse(mock_connect_to_region.called)

    def test_get_bucket(self):
        """
        _get_bucket() properly returns a bucket and caches it
        """
        mock_get_bucket = self._boto.s3.connect_to_region.return_value.get_bucket
        expected = mock_get_bucket.return_value
        actual = self._s3._get_bucket(self.TEST_BUCKET)

        self.assertEqual(expected, actual)
        self.assertEqual(expected, self._s3._buckets[self.TEST_BUCKET])
        mock_get_bucket.assert_called_once_with(self.TEST_BUCKET)

    def test_get_bucket_cached(self):
        """
        _get_bucket() properly uses the cache when it exists
        """
        mock_get_bucket = self._boto.s3.connect_to_region.return_value.get_bucket
        expected = MagicMock()
        self._s3._buckets[self.TEST_BUCKET] = expected
        actual = self._s3._get_bucket(self.TEST_BUCKET)

        self.assertEqual(expected, actual)
        self.assertFalse(mock_get_bucket.called)

    def test_get_keys(self):
        mock_get_bucket = MagicMock()
        mock_get_bucket.return_value.get_all_keys.return_value = [self.TEST_KEY]

        self._s3._get_bucket = mock_get_bucket
        keys = self._s3.get_keys(self.TEST_BUCKET, prefix=self.TEST_PREFIX)

        self.assertEqual(keys, [self.TEST_KEY])
        mock_get_bucket.assert_called_once_with(self.TEST_BUCKET)
        mock_get_bucket.return_value.get_all_keys.assert_called_once_with(prefix=self.TEST_PREFIX)
        self._logger.info.assert_called_once_with('Found following keys: %s', [self.TEST_KEY])

    def test_create_key(self):
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
        mock_key = self._boto.s3.key.Key.return_value
        mock_key.exists.return_value = True

        with self.assertRaises(ValueError) as e:
            self._s3.create_key(self.TEST_BUCKET, self.TEST_KEY, self.TEST_CONTENT)

        self.assertEqual(
            'Entry {0} already exists in S3 -- delete it first'.format(self.TEST_KEY),
            str(e.exception)
        )

    def test_update_key(self):
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
        mock_get_bucket = MagicMock()

        self._s3._get_bucket = mock_get_bucket
        self._s3.remove_keys(self.TEST_BUCKET, keys=[self.TEST_KEY])

        mock_get_bucket.assert_called_once_with(self.TEST_BUCKET)
        mock_get_bucket.return_value.delete_keys.assert_called_once_with([self.TEST_KEY])
        self._logger.info.assert_called_once_with('Deleting following keys: %s', [self.TEST_KEY])
