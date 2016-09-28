#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Maketx in multiprocess
#


import multiprocessing
import subprocess
import argparse
import sys
import os


parser = argparse.ArgumentParser(
    description='maketx command in multiprocessing')
parser.add_argument('input', default='', nargs="+")
args = parser.parse_args()
files = [os.path.abspath(i) for i in args.input]


def convert(input_file, num, lock, returnObj):
    """ Convert image to tx.

    Args:
        input_file (str) : Input file path
        num (Multiprocessing.Value) : A value to count
        lock (Multiprocessing.Lock) : Lock
        returnObj (Manager.dict) : Dict to store return values

    Return:
        None

    """

    try:
        output_file = os.path.splitext(input_file)[0] + ".tx"
        subprocess.call(['maketx', '--oiio', '-o', output_file, input_file])
    except subprocess.CalledProcessError:
        returnObj[input_file] = "Failed"
        return
    except OSError:
        print "maketx command not found"
        sys.exit()

    lock.acquire()
    num.value += 1
    lock.release()

    returnObj[input_file] = "Successed"
    return


def updateProgress(percent):
    """ Update progrss bar.

    Args:
        percent (float): Percentage of progress in range of 0.0-1.0

    Returns:
        None

    Raises:
        KeyError: Raises an exception.
    """

    length = 40
    space = ' '

    progress = "#" * int(round(percent * length))
    left = space * (length - len(progress))
    label = 'Now converting...'
    complete = int(percent * 100)

    sys.stdout.write(
        "\r{label}: [{bar}] {percent}%".format(
            label=label, bar=progress+left, percent=complete))
    sys.stdout.flush()


def main():
    """ main """

    num = multiprocessing.Value('i', 0)
    lock = multiprocessing.Lock()
    manager = multiprocessing.Manager()
    returnDict = manager.dict()

    jobs = []
    for img in files:
        p = multiprocessing.Process(
            target=convert, args=(img, num, lock, returnDict, ))
        jobs.append(p)
        p.start()

    counter = 0
    while True:
        if num.value == len(files):
            break
        if counter == num.value:
            continue
        else:
            counter += 1
            percent = float(counter) / len(files)
            updateProgress(percent)

    updateProgress(1)
    sys.stdout.write('\n')
    sys.stdout.write('\n')

    resultDict = dict(returnDict)

    fails = [i for i in resultDict if resultDict[i] == "Failed"]

    if len(fails) == 0:
        print "All files are successfully converted to tx."
        sys.stdout.write('\n')
        return
    else:
        print "%s of %s files were failed to converted to tx." % (
            len(fails), len(files))
        for i in fails:
            print i

        sys.stdout.write('\n')
        return


if __name__ == "__main__":
    main()
