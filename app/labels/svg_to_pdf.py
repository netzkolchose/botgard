import subprocess
import os
import codecs
import random


from django.conf import settings


def convert_svg_to_pdf(svg_markup):
    return convert_svg_to_format(svg_markup, "pdf")


def convert_svg_to_format(svg_markup, format):

    # if svg_markup contains non-ascii characters
    # we need to pass data through files, because Popen pipes won't do in python 2:
    # https://bugs.python.org/issue6135
    try:
        svg_markup
    except UnicodeEncodeError:
        return _convert_svg_to_format_tmpfile(svg_markup, format)

    proc = subprocess.Popen(
        ["rsvg-convert", "--format", format, "--zoom", "0.24", "--dpi-x", "300", "--dpi-y", "300"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    proc.stdin.write(bytes(svg_markup, encoding='utf8'))
    proc.stdin.write(bytes("\n", encoding='utf8'))
    proc.stdin.close()

    while proc.returncode is None:
        proc.poll()

    err = proc.stderr.read()
    if err:
        raise RuntimeError("rsvg failed\n" + err)

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
        raise RuntimeError("rsvg failed\n" + err)

    with open(outfilename) as f:
        outp = f.read()

    os.remove(outfilename)
    os.remove(infilename)
    return outp
