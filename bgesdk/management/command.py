import argparse

from abc import ABCMeta, abstractmethod


class BaseCommand(metaclass=ABCMeta):

    help = ''

    def __init__(self, parser, command_name=None, **kwargs):
        if command_name is not None:
            parser = parser.add_parser(
                command_name,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                help=self.help or '',
                **kwargs
            )
        parser.set_defaults(method=self.handler, parser=parser)
        self.parser = parser
        self.add_arguments(parser)

    def add_arguments(self, parser):
        pass

    @abstractmethod
    def handler(self, args):
        pass
