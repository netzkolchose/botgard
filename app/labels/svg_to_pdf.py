import subprocess
import os
import re
import sys
import codecs
import random
import time

from django.conf import settings


def convert_svg_to_pdf(svg_markup):
    return convert_svg_to_format(svg_markup, "pdf")


def convert_svg_to_format(svg_markup: str, format: str):

    # if svg_markup contains non-ascii characters
    # we need to pass data through files, because Popen pipes won't do in python 2:
    # https://bugs.python.org/issue6135
    if sys.version_info[0] < 3:
        try:
            svg_markup.encode("ascii")
        except UnicodeEncodeError:
            return _convert_svg_to_format_tmpfile(svg_markup, format)

    version = subprocess.check_output(["rsvg-convert", "--version"]).decode()
    version = tuple(int(g) for g in re.match(r".*(\d+)\.(\d+)\.(\d+).*", version).groups())

    command_args = ["rsvg-convert", "--format", format, "--dpi-x", "300", "--dpi-y", "300"]

    if version <= (2, 45, 0):
        # fix dpi setting for rsvg-convert below version 2.46
        # https://gitlab.gnome.org/GNOME/librsvg/-/issues/514
        command_args += ["--zoom", "0.24"]

    proc = subprocess.Popen(
        command_args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    proc.stdin.write(bytes(svg_markup, encoding='utf8'))
    proc.stdin.write(bytes("\n", encoding='utf8'))
    proc.stdin.close()

    start_time = time.time()
    while proc.returncode is None:
        proc.poll()
        time.sleep(.01)
        if time.time() - start_time >= 3.:
            raise RuntimeError(f"rsvg timeout")

    err = proc.stderr.read()
    if err:
        raise RuntimeError("rsvg failed\n" + err.decode())

    return proc.stdout.read()


def _convert_svg_to_format_tmpfile(svg_markup, format):

    infilename = os.path.join(settings.MEDIA_ROOT, "_tmp_%s.svg" % random.randrange(10000, 1000000))
    outfilename = os.path.join(settings.MEDIA_ROOT, "_tmp_%s.pdf" % random.randrange(10000, 1000000))

    with codecs.open(infilename, "wt", encoding="utf-8") as f:
        f.write(svg_markup)

    proc = subprocess.Popen(
        ["rsvg-convert", "--format", format, "--zoom", "0.24", "--dpi-x", "300", "--dpi-y", "300",
         "--output", outfilename, infilename],
        stderr=subprocess.PIPE,
    )

    while proc.returncode is None:
        proc.poll()

    err = proc.stderr.read()
    if err:
        os.remove(outfilename)
        raise RuntimeError(f"rsvg failed\n{err}")

    with open(outfilename) as f:
        outp = f.read()

    os.remove(outfilename)
    os.remove(infilename)
    return outp
