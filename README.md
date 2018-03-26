# Argload, easy reloading of command line arguments
Argload is a python package facilitating the reloading of command line
arguments.

As an example is worth a thousand words, let's explain the use cases of
**argload** with an example bit of code.

Say you have a bunch of experiments to run depending on two hyperparameters,
`a` and `b`. You define your parser with `argparse` as follow:
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--a', type=float, default=1e-3)
parser.add_argument('--b', type=float, default=2.)
args = parser.parse_args()
```

Now say you have 2 very long experiments to run, one with
`a=1e-3`, `b=3`, and the other one with `a=1e-4`, `b=1`. If both
experiments were very short, everything would be fine, you would
launch each of them independantly, and even if they crash, simply
restarting them using your bash history is both simple and fast.

But if they are very long, there is a non negligible chance for your command
line not to be in your bash history anymore, or for you to have forgotten
your exact hyperparameters (OK, two is easy, 32 less so, 32 hyperparameters on
54 experiments even less so...).

That's where **argload** can come in handy. Now simply wrap your
parser in an ArgumentLoader instance in the following way:
```python
import argparse
import argload

parser = argparse.ArgumentParser()
parser.add_argument('--a', type=float, default=1e-3)
parser.add_argument('--b', type=float, default=2.)
parser = argload.ArgumentLoader(parser, to_reload=['a', 'b'])
args = parser.parse_args()
```
Your script takes one additional required argument `logdir`, the
directory where your current argument will be stored (and typically
the directory where all your results will be stored), and two
optional flags `overwrite` and `dump`. Say you want to store the
results of your first experiment in the `exp1`. After creating this
directory, the first time you run your script, with the `logdir` argument
properly set, 
```
python script.py --logdir exp1 --a 1e-3 --b 3
```
argload stores your arguments in the `exp1` directory. Now, the
next time you run your script in `exp1`,
```
python script.py --logdir exp1
```
your hyperparameters will be automatically loaded.

I you specify the `overwrite` flag, you can overwrite previous values
of your hyperparameters. For instance, running
```
python script.py --logdir exp1 --overwrite --a 1e-2
```
will relaunch `script.py` with arguments `a=1e-2`, `b=3`.
However, the new value for `a` will not be stored in your directory,
if you relaunch
```
python script.py --logdir exp1
```
the values you will be using are still `a=1e-3`, `b=3`.

If you want to store your new setting inside of your experiment directory,
issue the command
```
python script.py --logdir exp1 --overwrite --dump --a 1e-2
```
The next time you will launch your script in `exp1`, the values used
will be `a=1e-2`, `b=3`.
