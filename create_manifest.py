#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import os
from simplecrypt import encrypt, DecryptionException
from base64 import b64encode
from simplecrypt import decrypt
from base64 import b64decode
from filehash import FileHash
from deepdiff import DeepDiff
import json
import logging

logger = logging.getLogger("SC.fhasher")

OUTPUT_FILENAME = 'public/prism/manifest.sistemi'
EXCLUDE_FILENAME = 'public/prism/manifest.exc'
gIoPP = "1998t$mimoFfa{}t!*&moNey0c4free"

# files that cannot be excluded from manifest
EXCLUDE_BLACKLIST = ["lente.json"]

__test_d = {}


def _encrypt(dict, output, pw=''):
    # encrypt
    logger.info("creating encrypted file {}".format(output))
    d_str = json.dumps(dict)
    ciphertext = encrypt(gIoPP.format("gIoPP") + pw, d_str)
    encoded_cipher = b64encode(ciphertext)
    try:
        with open(output, "wb") as file:
            file.write(encoded_cipher)
    except FileNotFoundError:
        logger.error("failed to create {}".format(output))
        return False
    except Exception as e:
        logger.error("failed to create {} ({})".format(output, e))
        return False
    return True


def _hashes(path):
    d = {}
    try:
        sha1hasher = FileHash('sha256')
        paths = [x[0] for x in os.walk(path)]
        for p in paths:
            hashes = sha1hasher.hash_dir(p, "*")
            for fhash in hashes:
                fname = os.path.join(p, fhash.filename)
                d[fname] = fhash.hash
        return d
    except Exception as e:
        logger.error(e)
        return None


def _hash_prism(path):
    d = {}
    try:
        sha1hasher = FileHash('sha256')
        fname = os.path.join(path, 'prism.json')
        _hash = sha1hasher.hash_file(fname)
        d[fname] = _hash
        return d
    except Exception as e:
        logger.error(e)
        return None


def _exclusions(path):
    _exclusions = []
    if path is not None:
        if not os.path.exists(path):
            logger.error("exclusion_file {} does not exist".format(path))
            return False, []

        with open(path) as f:
            content = f.readlines()
        content = [x.strip() for x in content if not x.startswith("#")]
        _exclusions += content

    # check if list of excluded files is valid
    for f in _exclusions:
        if not os.path.exists(f):
            logger.error("exclusion_file: {} does not exist".format(f))
            return False, []

    return True, _exclusions


def hashpath_manifest_create(path, exclusion_file=EXCLUDE_FILENAME, lock=True, output=OUTPUT_FILENAME, pw=''):
    """
    Create a manifest file

    :param path: path to take manifest of (typically public)
    :param exclusion_file: path to file with listed exclusions
    :param exclusions_list: list of files to exclude, path and filename required
    :param lock: True|False
    :param output: path of manifest file to create
    :param pw: additional passphrase to add
    :return: True - success, False otherwise
    """
    logger.info("path {}, lock {}".format(path, lock))

    success, excluded = _exclusions(exclusion_file)
    if not success:
        msg = "Failed to process exclusion_file: {}".format(exclusion_file)
        logger.error(msg)
        return False, msg

    excluded += excluded
    excluded.append(output)

    for excl in excluded:
        for blacklist in EXCLUDE_BLACKLIST:
            if excl.find(blacklist) > 0:
                msg = "ERROR Cannot exclude : {}".format(excl)
                logger.error(msg)
                return False, msg

    logger.info("exclusions: {}".format(excluded))

    if lock:
        d = _hashes(path)
        if d is None:
            msg = "Failed to create manifest hash"
            logger.error(msg)
            return False, msg
        for exc in excluded:
            if exc in d:
                logger.info("excluding {}".format(exc))
                d.pop(exc, None)
    else:
        # prism.json sets whether the station uses a locked
        # manifest or not, so it is always hashed and checked
        d = _hash_prism(path)
        if d is None:
            msg = "Failed to create manifest hash (unlocked)"
            logger.error(msg)
            return False, msg

    d["__lock__"] = lock

    success = _encrypt(d, output, pw)
    if not success:
        msg = "failed to create encrypted manifest"
        logger.error(msg)
        return False, msg
    __test_d.update(d)
    logger.info("succeeded")
    return True, None


def hashpath_manifest_read(path, pw=''):
    """
    Read manifest and return dict

    :param path: path to manifest file
    :param pw: additional password phrase, default is ''
    :return: dict of manifest, None on error
    """
    if not os.path.exists(path):
        logger.error("invalid path {}".format(path))
        return None

    logger.debug("reading encrypted file {}".format(path))
    with open(path, 'rb') as myfile:
        encoded_cipher = myfile.read()
    cipher = b64decode(encoded_cipher)
    try:
        decoded = decrypt(gIoPP.format("gIoPP") + pw, cipher)
    except DecryptionException:
        logger.error("Failed to decrypt with given password")
        return None

    decoded_str = "".join(chr(x) for x in bytearray(decoded))
    logger.debug("decoded: {}".format(decoded_str))
    try:
        dd = json.loads(decoded_str)
    except Exception as e:
        logger.error(e)
        return None
    return dd


def hashpath_manifest_check(path, pw=''):
    """
    Checks whether a manifest is valid or not

    :param path: path to manifest file
    :param pw: additional password phrase, default is ''
    :return: True - passed check, otherwise False
    """
    d = hashpath_manifest_read(path)
    if d is None:
        logger.error("Failure to read manifest")
        return False

    if d.get("__lock__", None) is None:
        logger.error("manifest missing required field (__lock__)")
        return False

    prism = os.path.join(os.path.dirname(path), 'prism.json')
    if d.get(prism, None) is None:
        logger.error("manifest missing required field (prism)")
        return False

    if not d["__lock__"]:
        # check if this is allowed by checking if prism.json passes hash
        # TMIServer creates the manifest, and it will check the prism.json:config:manifest_locked
        # value, and if that is set, then __lock__ should be set.  We don't need to explicitly
        # check manifest_locked, cause if it passes hash, then __lock__ has the right value
        sha1hasher = FileHash('sha256')
        _hash = sha1hasher.hash_file(prism)
        if d[prism] != _hash:
            logger.error("hash check failed on {}".format(prism))
            return False
        logger.info("manifest is not locked")
        return True

    d.pop("__lock__", None)
    # manifest is locked, check hashes
    sha1hasher = FileHash('sha256')
    for file, hash in d.items():
        _hash = sha1hasher.hash_file(file)
        if hash != _hash:
            logger.error("hash check failed on {}".format(file))
            return False

    # check for any new files
    # TODO: is this necessary?  think not....

    return True


def manifest_create():
    """

    :return:
    """
    def read_json_file_to_dict(file):
        if os.path.isfile(file):
            content = []
            with open(file) as json_data:
                for line in json_data:
                    if line.strip().startswith('//'):
                        content.append("\n")
                    else:
                        content.append(line)

            try:
                _dict = json.loads("".join(content))

            except Exception as e:
                logger.error(e)
                return False, e

        else:
            msg = "Unable to find json file %s" % file
            logger.error(msg)
            return False, msg
        return True, _dict

    success, prism = read_json_file_to_dict('public/prism/prism.json')
    if not success:
        logger.error("Failed to read prism.json")
        return False, prism

    #if prism.get("config", None) is None:
    #    logger.error("prism.json, missing required field config")
    #    return False, prism

    #if prism['config'].get("manifest_locked", None) is None:
    #    logger.error("prism.json, missing required field config.manifest_locked")
    #    return False, prism

    _locked = prism["manifest_locked"]
    if not isinstance(_locked, bool):
        logger.error("prism.json:config.manifest_locked is not boolean")
        return False, prism

    logger.info("prism.json config.manifest_locked: {}".format(_locked))

    success, msg = hashpath_manifest_create('public/prism',
                                       lock=_locked,
                                       output='public/prism/manifest.sistemi',
                                       exclusion_file='public/prism/manifest.exc')
    if not success:
        logger.error("Failed to create manifest: {}".format(msg))
        return False, msg
    return True, None


# Creating scripts manifest:
# 1) copy this file to root of scripts directory
# 2) change False to True
# 3) run it: python3 file_hasher.py
# 4) remove this file
if True and __name__ == '__main__':
    import sys

    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

    success = manifest_create()
    if success: sys.exit(0)
    sys.exit(1)

if __name__ == '__main__':
    import sys

    logging.basicConfig()
    logger.setLevel(logging.DEBUG)

    # testing stuff

    if False:
        # manually modify a file and confirm that check fails
        success = hashpath_manfest_check('../public/prism/manifest.sistemi')
        if not success:
            print("hashpath_manfest_check FAILED")
            sys.exit(1)
        print("hashpath_manfest_check PASSED")
        sys.exit(1)

    # ------ test 1: Create and check manifest
    logger.info("Test 1:")

    success = hashpath_manifest_create('../public/prism',
                                       output='../public/prism/manifest.sistemi',
                                       exclusion_file='../public/prism/manifest.exc')
    if not success:
        logger.error("Failed to create manifest")
        sys.exit(1)

    dd = hashpath_manifest_read('../public/prism/manifest.tmi')
    if dd is None:
        logger.error("failed to read manifest")
        sys.exit(1)
    logger.info(dd)

    ddiff = DeepDiff(__test_d, dd)
    logger.info(ddiff)

    if ddiff:
        logger.info("FAIL")
        sys.exit(1)
    else:
        logger.info("PASS")

    success = hashpath_manifest_check('../public/prism/manifest.sistemi')
    if not success:
        logger.info("hashpath_manfest_check FAILED")
        sys.exit(1)

    logger.info("hashpath_manfest_check PASSED")

    # ------ test 2: Create and check an UNLOCKED manifest
    logger.info("Test 2:")

    success = hashpath_manifest_create('../public/prism',
                                       lock=False,
                                       output='../public/prism/manifest.sistemi',
                                       exclusion_file='../public/prism/manifest.exc')
    if not success:
        logger.error("Failed to create manifest")
        sys.exit(1)

    success = hashpath_manifest_check('../public/prism/manifest.tmi')
    if not success:
        logger.info("hashpath_manfest_check FAILED")
        sys.exit(1)
    logger.info(dd)

    sys.exit(0)
