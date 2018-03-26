""" Defining ArgumentLoader class """
import os.path as path
from copy import copy
import pickle
from argparse import Namespace

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
        self._parser.add_argument('--dump', action='store_true',
                                  help='Flag specifying that overwritten arguments will replace '
                                  'previous reloading arguments')
        self._to_reload = to_reload

    def parse_known_args(self, args=None, namespace=None):
        """ Parses known command line arguments, and reloads appropriately """
        # starts by parsing current arguments
        args, argv = self._parser.parse_known_args(args, namespace)

        # if logdir does not exist, throw exception
        if not path.exists(args.logdir):
            raise ValueError("Logdir does not exist.")

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
        args = self._fuse_args(dumped_args, args, overwrite)

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

    def _fuse_args(self, dumped_args, args, overwrite):
        fused_args = {}
        for k in list(dumped_args.keys()) + list(args.keys()):
            if k in dumped_args and k in args and dumped_args[k] != args[k]:
                if overwrite:
                    fused_args[k] = args[k]
                elif args[k] == self._parser.get_default(k):
                    fused_args[k] = dumped_args[k]
                else:
                    raise ValueError("Overwritting a dumped value requires the overwrite flag.")
            elif k in dumped_args:
                fused_args[k] = dumped_args[k]
            else:
                fused_args[k] = args[k]

        return Namespace(**fused_args)


    def parse_args(self, args=None, namespace=None):
        """ Parse args """
        args, argv = self.parse_known_args(args, namespace)
        if argv:
            raise ValueError('unrecognized arguments: %s' % ' '.join(argv))
        return args
