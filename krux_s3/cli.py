# -*- coding: utf-8 -*-
#
# © 2015-2016 Krux Digital, Inc.
#

#
# Standard libraries
#

from __future__ import absolute_import

#
# Internal libraries
#

import krux_boto.cli
from krux_s3 import VERSION
from krux_s3.s3 import add_s3_cli_arguments, get_s3, NAME


class Application(krux_boto.cli.Application):

    def __init__(self, name=NAME):
        # XXX: This is intended to be using NAME. name parameter is designed to be something you can override.
        #      However, in order to handle CLI inheritance, we need to have a way to distinguish this CLI class from
        #      the CLI class that is inheriting this class. Thus, we use NAME here.
        self._VERSIONS[NAME] = VERSION

        # Call to the superclass to bootstrap.
        super(Application, self).__init__(name=name)

        self.s3 = get_s3(self.args, self.logger, self.stats)

    def add_cli_arguments(self, parser):
        # Call to the superclass
        super(Application, self).add_cli_arguments(parser)

        add_s3_cli_arguments(parser, include_boto_arguments=False)

    def run(self):
        print(self.s3.get_keys(bucket_name='krux-tmp'))


def main():
    app = Application()
    with app.context():
        app.run()


# Run the application stand alone
if __name__ == '__main__':
    main()
