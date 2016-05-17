#!/usr/bin/python3

# WARNING this still needs more testing / cleanup / documentation,
# use under your own risk.

# Merge Mapillary sequences before uploading
# Copyright (C) 2016 Nicolás Alvarez <nicolas.alvarez@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import sys
import json
import argparse
from gi.repository import GExiv2

parser = argparse.ArgumentParser(description='Changes the sequence UUID of all given Mapillary photos to the same value, merging them into a single sequence.')
parser.add_argument('dir', help='Directory to work on.')
args = parser.parse_args()

try:
    dircontent = os.listdir(args.dir)
except FileNotFoundError:
    print("Directory {} not found".format(args.dir), file=sys.stderr)
    sys.exit(1)

dircontent.sort()

def is_mapillary_photo(path):
    return (
        path.endswith('.jpg')
        and not path.endswith('-thumb.jpg')
        and os.path.isfile(path)
    )

iterdir = filter(is_mapillary_photo, iter(os.path.join(args.dir, filename) for filename in dircontent))

# get the sequence UUID of the first photo in the directory
try:
    first_path = next(iterdir)
except StopIteration:
    print("No usable photos found!", file=sys.stderr)
    sys.exit(1)

class MapiImage():
    def __init__(self, path):
        self.exif = GExiv2.Metadata(path)
        self.desc = json.loads(self.exif.get_tag_string('Exif.Image.ImageDescription'))

    def seqUUID(self):
        return self.desc['MAPSequenceUUID']

    def setSeqUUID(self, newuuid):
        self.desc['MAPSequenceUUID'] = newuuid

    def save(self):
        self.exif.set_tag_string('Exif.Image.ImageDescription', json.dumps(self.desc))
        self.exif.save_file()

first_photo = MapiImage(first_path)
print("{} UUID is {}".format(first_path, first_photo.seqUUID()))

for filename in iterdir:
    photo = MapiImage(filename)
    if photo.seqUUID() == first_photo.seqUUID():
        print("{} already has correct UUID".format(filename))
    else:
        print("{} needs to be fixed".format(filename))
        photo.setSeqUUID(first_photo.seqUUID())
        photo.save()
