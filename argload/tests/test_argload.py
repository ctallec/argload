""" Unit testing for Argload class """
from os import mkdir, path
import argparse
import shutil
from unittest import TestCase
import argload


class TestArgload(TestCase):
    """ Testing """
    def normal_test(self):
        """ Test normal use case """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('--a', type=int, nargs='*')
            parser.add_argument('--b', type=int)
            parser = argload.ArgumentLoader(parser, ['a'])
            mkdir('log')
            parser.parse_args(['--logdir', 'log', '--a', '3', '5', '--b', '2'])

            args = parser.parse_args(['--logdir', 'log'])

            self.assertTrue(args.a == [3, 5])
            self.assertTrue(args.b is None)
            self.assertTrue(args.logdir == 'log')

            args = parser.parse_args(['--logdir', 'log', '--overwrite', '--a', '4'])

            self.assertTrue(args.a == [4])
            self.assertTrue(args.b is None)
        finally:
            shutil.rmtree('log')

    def failed_overwrite_test(self):
        """ Trying to overwrite without overwrite flag """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('--a', type=int, nargs='*')
            parser.add_argument('--b', type=int)
            parser = argload.ArgumentLoader(parser, ['a'])
            mkdir('log')
            parser.parse_args(['--logdir', 'log', '--a', '3', '4', '--b', '2'])

            with self.assertRaises(ValueError) as context:
                parser.parse_args(['--logdir', 'log', '--a', '4'])

            self.assertTrue("Overwritting" in str(context.exception))
        finally:
            shutil.rmtree('log')

    def dump_test(self):
        """ Dumping modifies stored values """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('--a', type=int, nargs='*')
            parser.add_argument('--b', type=int)
            parser = argload.ArgumentLoader(parser, ['a'])
            mkdir('log')
            parser.parse_args(['--logdir', 'log', '--a', '3', '4', '--b', '2'])

            parser.parse_args(['--logdir', 'log', '--overwrite', '--dump', '--a', '3', '2'])
            args = parser.parse_args(['--logdir', 'log'])

            self.assertEqual([3, 2], args.a)
        finally:
            shutil.rmtree('log')

    def nodir_test(self):
        """ Fail if logdir does not exist """
        parser = argparse.ArgumentParser()
        parser.add_argument('--a', type=int, nargs='*')
        parser.add_argument('--b', type=int)
        parser = argload.ArgumentLoader(parser, ['a'])
        with self.assertRaises(ValueError) as context:
            parser.parse_args(['--logdir', 'log', '--a', '3', '4', '--b', '2'])

        self.assertIn("Logdir does", str(context.exception))

    def dump_no_overwrite_test(self):
        """ Fail if dump is used without overwrite """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('--a', type=int, nargs='*')
            parser.add_argument('--b', type=int)
            parser = argload.ArgumentLoader(parser, ['a'])
            mkdir('log')
            parser.parse_args(['--logdir', 'log', '--a', '3', '4', '--b', '2'])
            with self.assertRaises(ValueError) as context:
                parser.parse_args(['--logdir', 'log', '--a', '2', '4', '--b', '2', '--dump'])

            self.assertIn("Dumping is not", str(context.exception))
        finally:
            shutil.rmtree('log')

    def overwrite_no_old_test(self):
        """ Fail if overwrite or dump without first dump """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('--a', type=int, nargs='*')
            parser.add_argument('--b', type=int)
            parser = argload.ArgumentLoader(parser, ['a'])
            mkdir('log')
            with self.assertRaises(ValueError) as context:
                parser.parse_args(['--logdir', 'log', '--a', '2', '4', '--b', '2', '--overwrite'])

            self.assertIn("No old", str(context.exception))
        finally:
            shutil.rmtree('log')

    def overwrite_default_test(self):
        """ You can overwrite defaults, and it behaves properly """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('--a', type=float, default=1e-3)
            parser.add_argument('--b', type=float, default=2.)
            parser = argload.ArgumentLoader(parser, ['a', 'b'])
            mkdir('log')
            parser.parse_args(['--logdir', 'log', '--a', '1e-2', '--b', '3.'])
            args = parser.parse_args(['--logdir', 'log', '--a', '1e-3', '--overwrite'])
            self.assertEqual(args.a, 1e-3)
            self.assertEqual(args.b, 3.)
        finally:
            shutil.rmtree('log')

    def name_from_args_test(self):
        """ Test normal use case """
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument('--a', type=int, nargs='*')
            parser.add_argument('--b', type=int, default=2)
            parser = argload.ArgumentLoader(parser, ['a'])
            mkdir('log')

            args = parser.parse_args(['--logdir', 'log', '--name_from_args', '--a', '3', '5'])
            self.assertTrue(args.logdir == 'log/a=[3, 5]')

            parser.parse_args(['--logdir', 'log', '--name_from_args', '--a', '2', '5'])
            self.assertTrue(path.exists('log/a=[2, 5]') and path.exists('log/a=[3, 5]'))

            args = parser.parse_args(['--logdir', 'log/a=[3, 5]'])

            self.assertTrue(args.a == [3, 5])
            self.assertTrue(args.b == 2)
            self.assertTrue(args.logdir == 'log/a=[3, 5]')
        finally:
            shutil.rmtree('log')
