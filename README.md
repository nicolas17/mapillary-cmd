Mapillary commands
==================

This is (or will be) a series of command line tools for Mapillary.

Deblurring
----------

`mapillary-blurs.py` is a script that lets you clear blurs for all pictures in a sequence.
This is useful when you know you didn't capture any license plate or face,
or when you already did manual re-blurring of all photos that needed it
and you want to clear the remaining ones.

To use it, first you need to login into your account:

    python3 mapillary-blurs.py login

This will open an page in your browser where you can authorize the script to access your account.

To unblur a sequence, run:

    python3 mapillary-blurs unblur-seq SEQUENCEID

This will remove automatic blurs from all photos in the sequence.
It will skip any photos that already have manual blurs.

You can also skip additional photos by passing their IDs to the script using `--skip`:

    python3 mapillary-blurs.py unblur-seq --skip SPswc-uX3Wou8tDpk4lOZA --skip n51tS9TsmitbGtrj15IwwQ E5fc3tf0QM5KpsH8K9jkMw

This will remove blurs from photos in the sequence `E5fc3tf0QM5KpsH8K9jkMw`,
except photos `SPswc-uX3Wou8tDpk4lOZA`, `n51tS9TsmitbGtrj15IwwQ`,
and those that already have manual blurs.
