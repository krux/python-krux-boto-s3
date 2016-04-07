# -*- coding: utf-8 -*-
#
# © 2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import
import os

#
# Internal libraries
#

from krux.cli import get_group
import krux_boto.cli
from krux_s3.s3 import add_s3_cli_arguments, get_s3, NAME


class Application(krux_boto.cli.Application):

    def __init__(self, name=NAME):
        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name)

        self.s3 = get_s3(self.args, self.logger, self.stats)

    def add_cli_arguments(self, parser):
        # Call to the superclass
        super(Application, self).add_cli_arguments(parser)

        add_s3_cli_arguments(parser, include_boto_arguments=False)

    def run(self):
        print self.s3.get_keys(
            bucket_name='krux-tmp'
        )


def main():
    app = Application()
    with app.context():
        app.run()


# Run the application stand alone
if __name__ == '__main__':
    main()
