""" Defining ArgumentLoader class """
import os.path as path
import os
from copy import copy, deepcopy
import pickle
from argparse import Namespace
import sys


class ArgumentLoader(object):
    """ Wrap around a parser, to make it automatically reload arguments.

    :args parser: parser to wrap around
    :args to_reload: the arguments that will be dumped and reloaded when
        you parse with an appropriate logdir

    """
    def __init__(self, parser, to_reload):
        self._parser = parser
        self._parser.add_argument('--logdir', type=str, required=True,
                                  help='Experiment directory: this is where your command line '
                                  'arguments will be stored and reloaded from.')
        self._parser.add_argument('--overwrite', action='store_true',
                                  help='Flag explicitly specifying that specified arguments must '
                                  'overwrite reloaded arguments.')
        self._parser.add_argument('--name_from_args', action='store_true',
                                  help='Create sub-logdir name from non-default arguments ')
        self._parser.add_argument('--dump', action='store_true',
                                  help='Flag specifying that overwritten arguments will replace '
                                  'previous reloading arguments')
        self._to_reload = to_reload

    def parse_known_args(self, args=None, namespace=None):
        """ Parses known command line arguments, and reloads appropriately """
        # not very clean, use _parse_known_args to only retrieve specified args
        specified_args = Namespace()
        raw_args = sys.argv[1:] if args is None else args
        self._parser._parse_known_args(raw_args, specified_args)
        specified_keys = vars(specified_args).keys()

        # starts by parsing current arguments
        args, argv = self._parser.parse_known_args(args, namespace)

        # if logdir does not exist, throw exception
        if not path.exists(args.logdir):
            raise ValueError("Logdir does not exist.")

        if args.name_from_args:
            args.logdir = path.join(args.logdir, self._make_name(specified_args))
            if not path.exists(args.logdir):
                os.makedirs(args.logdir)

        # retrieve logdir overwrite and dump and delete them from args: we don't
        # want to store them in the args file
        logdir = args.logdir
        overwrite = args.overwrite
        dump = args.dump

        args_file = path.join(logdir, 'args')
        readable_args_file = path.join(logdir, 'args_readable')

        # if logdir does not contain an args file, assume this is
        # the first time the script is launched, create the file
        # and dump all arguments
        if not path.exists(args_file):
            # if either overwrite or dumps are activated, raise an exception
            if overwrite or dump:
                raise ValueError("No old arguments: you cannot overwrite or dump.")

            self._dump_args(args, args_file, readable_args_file)

            return args, argv

        # if you dump, you must overwrite
        if dump and not overwrite:
            raise ValueError("Dumping is not allowed without overwritting.")

        # reload arguments
        with open(args_file, 'rb') as f:
            dumped_args = vars(pickle.load(f))

        args = vars(args)
        args = self._fuse_args(dumped_args, args, specified_keys, overwrite)

        if dump:
            self._dump_args(args, args_file, readable_args_file)

        return args, argv

    def _dump_args(self, args, args_file, readable_args_file):
        args_to_dump = copy(args)

        for k in vars(args):
            if k not in self._to_reload:
                delattr(args_to_dump, k)

        # dump pickle to args file
        with open(args_file, 'wb') as f:
            pickle.dump(args_to_dump, f)

        # dump print to readable args file
        with open(readable_args_file, 'w') as f:
            print(vars(args_to_dump), file=f)

    def _fuse_args(self, dumped_args, args, specified_keys, overwrite):
        fused_args = {}
        for k in list(dumped_args.keys()) + list(args.keys()):
            if k in dumped_args and k in specified_keys and dumped_args[k] != args[k]:
                if overwrite:
                    fused_args[k] = args[k]
                else:
                    raise ValueError("Overwritting a dumped value requires the overwrite flag.")
            elif k in dumped_args:
                fused_args[k] = dumped_args[k]
            else:
                fused_args[k] = args[k]

        return Namespace(**fused_args)

    def _make_name(self, specified_args):
        specified_args = vars(deepcopy(specified_args))
        for key in ['root', 'logdir', 'overwrite', 'dump', 'name_from_args']:
            try:
                del specified_args[key]
            except KeyError:
                pass

        if not specified_args:
            raise ValueError("When using '--name_from_args' flag, at least "
                             "one argument must be provided")

        # BEWARE: this naming is dependent on the order of arguments.
        # Maybe use on ordered dictionnary instead, ordered lexicographically
        name = ''
        for key, arg in specified_args.items():
            if (arg is True) or (arg is False):
                name += key + '_'
            else:
                name += key + '=' + str(arg) + '_'
        return name[:-1]

    def parse_args(self, args=None, namespace=None):
        """ Parse args """
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            raise ValueError('unrecognized arguments: %s' % ' '.join(argv))
        return args
