#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys


class Cue2Flac(object):

    CUE2FLAC_DESCRIPTION = "cue2flac - Split a FLAC image into tracks according to a .cue file."

    def __init__(self):
        self.parser = argparse.ArgumentParser(description=Cue2Flac.CUE2FLAC_DESCRIPTION)
        self.parser.add_argument(
            "path_to_cue",
            help="path to the cue file describing the desired split")
        self.parser.add_argument(
            "output_dir",
            nargs="?",
            help="path to the output directory where resulting files will be saved"
                 + " (default is the same directory where the cue file is stored)")
        self.parser.add_argument(
            "-r", "--reencode",
            action="store_true",
            help="reencode the files instead of copying the stream directly"
                 + " (retains original encoding settings, fixes durations of tracks)")
        self.parser.add_argument(
            "-q", "--quiet",
            action="store_true",
            help="don't print the output or errors from ffmpeg (\033[1mimplies -f\033[0m)")
        self.parser.add_argument(
            "-f", "--force",
            action="store_true",
            help="force overwriting the output files"
                 + " (in case you run the script on the same cue file multiple times)")

        args = self.parser.parse_args()
        self.cuepath = args.path_to_cue
        self.outputpath = None if not args.output_dir else args.output_dir
        self.reencode = args.reencode
        self.quiet = args.quiet
        self.force = args.force

    def split(self):
        if not os.path.exists(self.cuepath):
            raise IOError("Specified .cue file doesn't exist!")
        if not shutil.which('ffmpeg'):
            raise RuntimeError("ffmpeg has not been found in $PATH!")

        cue = ''
        with open(self.cuepath) as cuefile:
            cue = cuefile.read().splitlines()

        inputdir = os.path.dirname(os.path.expanduser(self.cuepath))
        if inputdir != '':
            inputdir += '/'
        outputdir = os.path.expanduser(self.outputpath)
        if not outputdir:
            outputdir = inputdir
        if outputdir != '' and outputdir[-1] != '/':
            outputdir += '/'
        if not os.path.exists(self.outputpath):
            os.makedirs(self.outputpath)

        commonmeta = {}
        tracks = []
        files = {}
        currentfile = None

        for line in cue:
            if line.startswith('REM GENRE '):
                commonmeta['genre'] = ' '.join(line.strip().split(' ')[2:]).strip().replace('"', '')
            elif line.startswith('REM DATE '):
                commonmeta['date'] = ' '.join(line.strip().split(' ')[2:]).strip().replace('"', '')
            elif line.startswith('PERFORMER '):
                commonmeta['artist'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
            elif line.startswith('TITLE '):
                commonmeta['album'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
            elif line.startswith('FILE '):
                currentfile = inputdir + ' '.join(line.strip().split(' ')[1:-1]).replace('"', '')
                tracks = []
                files[currentfile] = tracks

            elif line.startswith('  TRACK '):
                track = commonmeta.copy()
                track['track'] = int(line.strip().split(' ')[1], 10)

                tracks.append(track)

            elif line.startswith('    TITLE '):
                tracks[-1]['title'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
            elif line.startswith('    PERFORMER '):
                tracks[-1]['artist'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
            elif line.startswith('    INDEX 01 '):
                t = list(map(int, ' '.join(line.strip().split(' ')[2:]).replace('"', '').split(':')))
                tracks[-1]['start'] = 60 * t[0] + t[1] + t[2] / 100.0

        trackcount = sum([len(tracks) for flacs, tracks in files.items()])

        for flacname, tracks in files.items():
            for i in range(len(tracks) - 1):
                tracks[i]['duration'] = tracks[i + 1]['start'] - tracks[i]['start']

            for track in tracks:
                metadata = {
                    'artist': track['artist'],
                    'title': track['title'],
                    'album': track['album'],
                    'track': str(track['track']) + '/' + str(trackcount)
                }

                if 'genre' in track:
                    metadata['genre'] = track['genre']
                if 'date' in track:
                    metadata['date'] = track['date']

                trackname = str(track['track']).zfill(2) \
                            + '. ' + str(track['artist']) \
                            + ' - ' + str(track['title']) \
                            + '.flac'
                trackname = re.sub('[<>:"\\/|?*]', ' ', trackname)

                cmd = ''

                cmd += 'ffmpeg'
                cmd += ' -i "' + str(flacname) + '"'
                cmd += ' -ss ' + str(int(track['start'] / 60 / 60)).zfill(2) \
                         + ':' + str(int(track['start'] / 60) % 60).zfill(2) \
                         + ':' + str(int(track['start'] % 60)).zfill(2)

                if 'duration' in track:
                    cmd += ' -t ' + str(int(track['duration'] / 60 / 60)).zfill(2) \
                            + ':' + str(int(track['duration'] / 60) % 60).zfill(2) \
                            + ':' + str(int(track['duration'] % 60)).zfill(2)

                if self.quiet or self.force:
                    cmd += ' -y'

                if not self.reencode:
                    cmd += ' -acodec copy'

                cmd += ' ' + ' '.join('-metadata ' + str(k) + '="' + str(v) + '"'
                                      for (k, v) in metadata.items())

                cmd += ' "' + outputdir + trackname + '"'

                try:
                    subprocess.run(cmd,
                                   shell=True,
                                   check=True,
                                   stdout=subprocess.DEVNULL if self.quiet else None,
                                   stderr=subprocess.DEVNULL if self.quiet else None)
                except subprocess.CalledProcessError:
                    break

def main():
    if sys.version_info[0] != 3 or sys.version_info[1] < 3:
        print("This tool requires Python version 3.3 or later.")
        sys.exit(1)

    c2f = Cue2Flac()
    c2f.split()

if __name__ == """__main__""":
    main()
