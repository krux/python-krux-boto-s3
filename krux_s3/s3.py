# -*- coding: utf-8 -*-
#
# © 2015-2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
from pprint import pprint

#
# Third party libraries
#

import boto.s3
import boto.s3.connection

#
# Internal libraries
#

from krux_boto import Boto, add_boto_cli_arguments
from krux.logging import get_logger
from krux.stats import get_stats
from krux.cli import get_parser, get_group


NAME = 'krux-s3'


def get_s3(args=None, logger=None, stats=None):
    """
    Return a usable S3 object without creating a class around it.

    In the context of a krux.cli (or similar) interface the 'args', 'logger'
    and 'stats' objects should already be present. If you don't have them,
    however, we'll attempt to provide usable ones for the SQS setup.

    (If you omit the add_s3_cli_arguments() call during other cli setup,
    the Boto object will still work, but its cli options won't show up in
    --help output)

    (This also handles instantiating a Boto object on its own.)
    """
    if not args:
        parser = get_parser()
        add_s3_cli_arguments(parser)
        args = parser.parse_args()

    if not logger:
        logger = get_logger(name=NAME)

    if not stats:
        stats = get_stats(prefix=NAME)

    boto = Boto(
        log_level=args.boto_log_level,
        access_key=args.boto_access_key,
        secret_key=args.boto_secret_key,
        region=args.boto_region,
        logger=logger,
        stats=stats,
    )
    return S3(
        boto=boto,
        logger=logger,
        stats=stats,
    )


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
        security_token=None,
        logger=None,
        stats=None,
    ):
        # Private variables, not to be used outside this module
        self._name = NAME
        self._logger = logger or get_logger(self._name)
        self._stats = stats or get_stats(prefix=self._name)

        # Throw exception when Boto2 is not used
        # TODO: Start using Boto3 and reverse this check
        if not isinstance(boto, Boto):
            raise TypeError('krux_s3.s3.S3 only supports krux_boto.boto.Boto')

        self.boto = boto
        self._security_token = security_token

        # Set up default cache
        self._conn = None
        self._buckets = {}

    def _get_connection(self):
        """
        Returns a connection to the designated region (self.boto.cli_region).
        The connection is established on the first call for this instance (lazy) and cached.
        """
        if self._conn is None:
            self._conn = self.boto.s3.connection.S3Connection(
                security_token=self._security_token,
            )

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
            raise ValueError('Entry {0} already exists in S3 -- delete it first'.format(k.key))

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
