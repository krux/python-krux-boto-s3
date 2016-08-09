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
    TEST_BUCKET = 'krux-tmp'
    TEST_KEY = 'TEST-KEY-{timestamp}'
    TEST_CONTENT = 'TEST-TEST'

    def setUp(self):
        self._logger = MagicMock()
        self._stats = MagicMock()

        self._boto = MagicMock()

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
