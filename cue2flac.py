#!/usr/bin/python3
import argparse
import os
import re
import subprocess


class Cue2Flac(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            "path_to_cue",
            help="path to the cue file describing the desired split")
        self.parser.add_argument(
            "output_dir",
            nargs="?",
            help="path to the output directory where resulting files will be saved"
                 + " (default is the same directory where the cue file is stored)")

        args = self.parser.parse_args()
        self.cuepath = args.path_to_cue
        self.outputpath = None if not args.output_dir else args.output_dir

    def split(self):
        if not os.path.exists(self.cuepath):
            raise IOError("Specified .cue file doesn't exist!")

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
        currentfile = None

        for line in cue:
            if line.startswith('REM GENRE '):
                commonmeta['genre'] = ' '.join(line.strip().split(' ')[2:]).strip()
            elif line.startswith('REM DATE '):
                commonmeta['date'] = ' '.join(line.strip().split(' ')[2:]).strip()
            elif line.startswith('PERFORMER '):
                commonmeta['artist'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
            elif line.startswith('TITLE '):
                commonmeta['album'] = ' '.join(line.strip().split(' ')[1:]).replace('"', '')
            elif line.startswith('FILE '):
                currentfile = inputdir + ' '.join(line.strip().split(' ')[1:-1]).replace('"', '')

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

        for i in range(len(tracks) - 1):
            tracks[i]['duration'] = tracks[i + 1]['start'] - tracks[i]['start']

        for track in tracks:
            metadata = {
                'artist': track['artist'],
                'title': track['title'],
                'album': track['album'],
                'track': str(track['track']) + '/' + str(len(tracks))
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

            cmd = 'ffmpeg'
            cmd += ' -i "' + str(currentfile) + '"'
            cmd += ' -ss ' + str(int(track['start'] / 60 / 60)).zfill(2) \
                     + ':' + str(int(track['start'] / 60) % 60).zfill(2) \
                     + ':' + str(int(track['start'] % 60)).zfill(2)

            if 'duration' in track:
                cmd += ' -t ' + str(int(track['duration'] / 60 / 60)).zfill(2) \
                        + ':' + str(int(track['duration'] / 60) % 60).zfill(2) \
                        + ':' + str(int(track['duration'] % 60)).zfill(2)

            cmd += ' ' + ' '.join('-metadata ' + str(k) + '="' + str(v) + '"'
                                  for (k, v) in metadata.items())
            cmd += ' -acodec copy'
            cmd += ' "' + outputdir + trackname + '"'

            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError:
                break

if __name__ == """__main__""":
    c2f = Cue2Flac()
    c2f.split()
