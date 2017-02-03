# -*- coding: utf-8 -*-
#@author: mkaay

from __future__ import unicode_literals

from builtins import object
from pyload.database import DatabaseBackend, queue


class StorageMethods(object):

    @queue
    def set_storage(db, identifier, key, value):
        db.c.execute(
            "SELECT id FROM storage WHERE identifier=? AND key=?", (identifier, key))
        if db.c.fetchone() is not None:
            db.c.execute(
                "UPDATE storage SET value=? WHERE identifier=? AND key=?", (value, identifier, key))
        else:
            db.c.execute(
                "INSERT INTO storage (identifier, key, value) VALUES (?, ?, ?)", (identifier, key, value))

    @queue
    def get_storage(db, identifier, key=None):
        if key is not None:
            db.c.execute(
                "SELECT value FROM storage WHERE identifier=? AND key=?", (identifier, key))
            row = db.c.fetchone()
            if row is not None:
                return row[0]
        else:
            db.c.execute(
                "SELECT key, value FROM storage WHERE identifier=?", (identifier,))
            d = {}
            for row in db.c:
                d[row[0]] = row[1]
            return d

    @queue
    def del_storage(db, identifier, key):
        db.c.execute(
            "DELETE FROM storage WHERE identifier=? AND key=?", (identifier, key))

DatabaseBackend.register_sub(StorageMethods)