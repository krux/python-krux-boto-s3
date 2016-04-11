# krux_s3

`krux_s3` is a library that provides wrapper functions for common S3 usage. It uses `krux_boto` to connect to AWS S3.

## Warning

In the current version, `krux_s3.s3.S3` is only compatible with `krux_boto.boto.Boto` object. Passing other objects, such as `krux_boto.boto.Boto3`, will cause an exception.

## Application quick start

The most common use case is to build a CLI script using `krux_s3.cli.Application`.
Here's how to do that:

```python

import krux_s3.cli

# This class inherits from krux.cli.Application, so it provides
# all that functionality as well.
class Application(krux_s3.cli.Application):
    def run(self):
        for key in self.s3.get_keys(bucket_name='my-test-bucket'):
            print key.get_contents_as_string()

def main():
    # The name must be unique to the organization.
    app = Application(name='krux-my-s3-script')
    with app.context():
        app.run()

# Run the application stand alone
if __name__ == '__main__':
    main()

```

As long as you get an instance of `krux_boto.boto.Boto`, the rest are the same. Refer to `krux_boto` module's [README](https://github.com/krux/python-krux-boto/blob/master/README.md) on various ways to instanciate the class.
