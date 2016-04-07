# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
from datetime import datetime
import unittest

#
# Internal libraries
#

from krux_boto.boto import Boto
from krux_s3.s3 import S3


class S3Test(unittest.TestCase):
    TEST_BUCKET = 'krux-tmp'
    TEST_KEY = 'TEST-KEY-{timestamp}'
    TEST_CONTENT = 'TEST-TEST'

    def setUp(self):
        self._s3 = S3(
            boto=Boto()
        )

        self._timestamp = (datetime.utcnow() - datetime.utcfromtimestamp(0)).total_seconds()

    def test_get_keys(self):
        """
        S3 data is correctly returned as a list
        """
        # TODO: This test needs to be improved using mock and stuff. But for the interest of time,
        # let's leave it at this minimal state.
        self.assertIsInstance(self._s3.get_keys(bucket_name=self.TEST_BUCKET), list)

    def test_create_update_delete_keys(self):
        """
        Keys can be created, updated, and deleted from S3
        """
        # TODO: This test needs to be improved using mock and stuff. But for the interest of time,
        # let's leave it at this minimal state.
        self._s3.create_key(
            bucket_name=self.TEST_BUCKET,
            key=self.TEST_KEY.format(timestamp=self._timestamp),
            str_content=self.TEST_CONTENT,
        )
        self._s3.update_key(
            bucket_name=self.TEST_BUCKET,
            key=self.TEST_KEY.format(timestamp=self._timestamp),
            str_content=self.TEST_CONTENT,
        )
        self._s3.remove_keys(
            bucket_name=self.TEST_BUCKET,
            keys=[self.TEST_KEY.format(timestamp=self._timestamp)],
        )
