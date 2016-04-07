# -*- coding: utf-8 -*-
#
# © 2015 Krux Digital, Inc.
#

# TODO: This is currently inside krux_manage_instance library.
# However, consider breaking this into a separate library or add it to krux_boto library.

#
# Standard libraries
#

from __future__ import absolute_import
from pprint import pprint

#
# Third party libraries
#

import boto.s3

#
# Internal libraries
#

from krux_boto import Boto, add_boto_cli_arguments
from krux.logging import get_logger
from krux.stats import get_stats
from krux.cli import get_parser, get_group


NAME = 'krux-s3'


def add_s3_cli_arguments(parser, include_boto_arguments=True):
    """
    Utility function for adding S3 specific CLI arguments.
    """
    if include_boto_arguments:
        # GOTCHA: Since EC2 and S3 both uses Boto, the Boto's CLI arguments can be included twice,
        # causing an error. This creates a way to circumvent that.

        # Add all the boto arguments
        add_boto_cli_arguments(parser)

    # Add those specific to the application
    group = get_group(parser, NAME)


class S3(object):
    """
    A manager to handle all S3 related functions.
    Each instance is locked to a connection to a designated region (self.boto.cli_region).
    """

    def __init__(
        self,
        boto,
        logger=None,
        stats=None,
    ):
        # Private variables, not to be used outside this module
        self._name = NAME
        self._logger = logger or get_logger(self._name)
        self._stats = stats or get_stats(prefix=self._name)

        # Add the boto connector
        if not isinstance(boto, Boto):
            raise TypeError('krux_s3.s3.S3 only supports krux_boto.boto.Boto')

        self.boto = boto

        # Set up default cache
        self._conn = None
        self._buckets = {}

    def _get_connection(self):
        """
        Returns a connection to the designated region (self.boto.cli_region).
        The connection is established on the first call for this instance (lazy) and cached.
        """
        if self._conn is None:
            self._conn = self.boto.s3.connect_to_region(self.boto.cli_region)

        return self._conn

    def _get_bucket(self, bucket_name):
        """
        Returns a bucket with the given name.
        The bucket is fetched on the first call (lazy) and cached.
        """
        if bucket_name not in self._buckets or self._buckets[bucket_name] is None:
            self._buckets[bucket_name] = self._get_connection().get_bucket(bucket_name)

        return self._buckets[bucket_name]

    def get_keys(self, bucket_name, prefix=None):
        """
        Returns a list of keys with the given prefix under the given bucket.
        """
        bucket = self._get_bucket(bucket_name)

        keys = bucket.get_all_keys(prefix=prefix)

        self._logger.info('Found following keys: %s', keys)
        return keys

    def create_key(self, bucket_name, key, str_content):
        """
        Creates a key in the given bucket.

        The key parameter is used as the key of the newly created key.
        The str_content parameter is used as the content of the newly created key.

        If there is another key with the same key in the given bucket, an error is thrown.
        """
        bucket = self._get_bucket(bucket_name)

        k = self.boto.s3.key.Key(bucket)
        k.key = key

        if k.exists():
            raise ValueError('Entry {0} already exists in S3 -- delete it first'.format(key.Key))

        k.set_contents_from_string(str_content)

        self._logger.info(
            'Created a key %s in bucket %s with following contents: %s',
            key, bucket_name, str_content
        )

        return k

    def update_key(self, bucket_name, key, str_content):
        """
        Updates a key in the given bucket.

        The key parameter is used to fetch the key.
        The str_content parameter overwrites the content of the key.
        """
        bucket = self._get_bucket(bucket_name)

        k = bucket.get_key(key)

        if k is None:
            raise ValueError('There are no key with name {0}'.format(key))

        k.set_contents_from_string(str_content)

        self._logger.info(
            'Updated a key %s in bucket %s with following contents: %s',
            key, bucket_name, str_content
        )

        return k

    def remove_keys(self, bucket_name, keys):
        """
        Deletes the given keys from the given bucket.
        """
        bucket = self._get_bucket(bucket_name)

        self._logger.info('Deleting following keys: %s', keys)
        bucket.delete_keys(keys)