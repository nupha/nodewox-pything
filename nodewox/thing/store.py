#coding: utf-8
from thing import Thing
from UserDict import IterableUserDict
import sqlite3
import sys
import inspect
import os
import zipfile
import traceback

NODEWOX_HOME = "/var/lib/nodewox"

class PackageLoader(object):
    "read thing class from a zip file or path"

    def __init__(self, path):
        assert isinstance(path, basestring), path
        assert os.path.exists(path), path

        path = os.path.abspath(path)
        self._path = path

        if os.path.isdir(path):
            self._classes = self._check_path(path)
        elif zipfile.is_zipfile(path):
            self._classes = self._check_zipfile(path)
        else:
            self._classes = {}

    def _check_path(self, path):
        "load Thing classes from a path"
        assert os.path.isdir(path), path
        if not path.endswith("/"): 
            path = "{}/".format(path)

        mods = set()
        for dirname, subnames, filenames in os.walk(path, followlinks=True):
            if "__init__.py" in filenames:
                mods.add(dirname[len(path):])

        sys.path.insert(0, path)
        cc = self._load_classes_from_modules(mods)
        sys.path.pop(0)
        return cc

    def _check_zipfile(self, zfile):
        "load Thing classes from a zip file"
        assert zipfile.is_zipfile(zfile), zfile

        # possible modules -> mods
        z = zipfile.ZipFile(zfile)
        mods = set()
        for n in z.namelist():
            if n.endswith("/__init__.py"):
                p = n[:-len("/__init__.py")]
                if len(p)>0:
                    mods.add(p)

        sys.path.insert(0, zfile)
        cc = self._load_classes_from_modules(mods)
        z.close()
        sys.path.pop(0)
        return cc

    def _load_classes_from_modules(self, mods):
        "load thing classes from a list of module names"
        assert isinstance(mods, (list, tuple, set)), mods
        assert len(mods)>0

        ret = {}
        for path in mods:
            nn = path.split("/")
            try:
                m = __import__(".".join(nn), fromlist=nn[:-1])
                for cname, x in inspect.getmembers(m, inspect.isclass):
                    if issubclass(x, Thing) and x!=Thing:
                        modname = ".".join(nn)
                        index = "{}.{}".format(modname, cname)
                        ret[index] = (modname, x)
            except:
                continue
        return ret

    @property
    def path(self):
        return self._path

    @property
    def classes(self):
        return dict(**self._classes)

    @classmethod
    def list(ctx):
        "list installed packages"
        for dirname, subnames, filenames in os.walk(os.path.join(NODEWOX_PATH, "packages")):
            if "meta" in filenames:
                print dirname


class Storage(object):
    "db init and connect"

    def __init__(self):
        self._dbfile = os.path.join(NODEWOX_HOME, "nodewox.db")
        if not os.path.exists(self._dbfile):
            self._setup()

    def _setup(self):
        conn = sqlite3.connect(self._dbfile)

        conn.execute("""
            CREATE TABLE REMOTE (
                remote_id varchar(100) primary key not null,
                rest_url text not null,
                rest_ca text not null default '',
                pri int not null default 0
            );""")

        conn.execute("""
            CREATE TABLE META (
                meta_id varchar(100) primary key not null,
                module text not null,
                class text not null,
                name text not null,
                pid int,
                path text not null
            );""")

        conn.execute("""
            CREATE TABLE PROFILE (
                profile_id text primary key not null,
                meta_id text not null,
                name text not null,
                token text not null,
                remote_id text not null,
                password text not null default '',
                owner text not null default '',
                iot_cert text not null default '',
                iot_key text not null default '',
                iot_ca text not null default ''
            );""")

        conn.execute("""insert into REMOTE (remote_id, rest_url, rest_ca, pri) values
            ('nodewox.org', 'https://www.nodewox.org/api', '', 1)""")

        # for test
        fh = open("/home/johnray/devel/nodewox/etc/mqtt_ca.crt")
        testca = fh.read()
        fh.close()
        conn.execute("""insert into REMOTE (remote_id, rest_url, rest_ca) values
            ('test', 'https://192.168.0.7:6601/api', '%s')""" % testca)

        conn.commit()
        conn.close()
        sys.stdout.write("create nodewox storage\n")

    @property
    def conn(self):
        return sqlite3.connect(self._dbfile)


class _TableORM(IterableUserDict):
    "base wrapper for data table"
    PKEY = ""
    TABLE = ""

    def __init__(self, **kwargs):
        assert self.PKEY!=""
        assert self.TABLE!=""
        self._id = kwargs[self.PKEY]
        if len(kwargs)==1 and self.PKEY in kwargs:
            self.data = {}
        else:
            self.data = dict(kwargs)

    @property
    def is_empty(self):
        return len(self.data)==0

    def load(self, conn):
        cur = conn.execute("select * from {} where {}=?".format(self.TABLE, self.PKEY), (self._id,))
        self.data = self._cursor_to_dict(cur) or {}

    def exists(self, conn, key):
        cus = conn.execute(
                "select %(f)s from %(t)s where %(f)s=?" % {"t":self.TABLE, "f":self.PKEY}, \
                (self._id,))
        return cus.fetchone()!=None

    def save(self, conn):
        assert len(self.data)>0
        if self._id not in self.data:
            self.data[self.PKEY] = self._id
        else:
            assert self.data[self.PKEY] == self._id, (self.data, self._id)
        if self.exists(conn, self._id):
            sets = ",".join("{}=:{}".format(x,x) for x in self.data)
            s = "update {} set {} where {}=:{}".format(self.TABLE, sets, self.PKEY, self.PKEY)
        else:
            fields = ",".join(self.data.keys())
            vals = ",".join(":%s" % x for x in self.data.keys())
            s = "insert into {} ({}) values ({})".format(self.TABLE, fields, vals)
        conn.execute(s, self.data)

    @classmethod
    def _cursor_to_dict(cls, cursor):
        vals = cursor.fetchone()
        if vals:
            desc = dict((i,x[0]) for i,x in enumerate(cursor.description))
            return dict((desc[i],x) for i,x in enumerate(vals))

    @classmethod
    def _cursor_to_dictlist(cls, cursor):
        res = []
        lst = cursor.fetchall()
        if len(lst)>0:
            desc = dict((i,x[0]) for i,x in enumerate(cursor.description))
            for vals in lst:
                res.append(dict((desc[i],x) for i,x in enumerate(vals)))
        return res

    @classmethod
    def list(cls, conn):
        cur = conn.execute("select * from {} order by {}".format(cls.TABLE, cls.PKEY))
        return [cls(**x) for x in cls._cursor_to_dictlist(cur)]

    @classmethod
    def find(cls, conn, key):
        cur = conn.execute("select * from {} where {}=?".format(cls.TABLE, cls.PKEY), (key,))
        data = cls._cursor_to_dict(cur)
        if data:
            return cls(**data)


class Remote(_TableORM):
    "a remote setting"
    TABLE = "REMOTE"
    PKEY = "remote_id"

    @classmethod
    def primary(self, conn):
        cur = conn.execute("select * from REMOTE where pri=1")
        data = self._cursor_to_dict(cur)
        if data:
            return Remote(**data)


class Meta(_TableORM):
    "a thing meta"
    TABLE = "META"
    PKEY = "meta_id"

    def __init__(self, **kwargs):
        assert "/" not in kwargs['meta_id']
        assert not kwargs['meta_id'].startswith(".")
        assert not kwargs['meta_id'].endswith(".")
        _TableORM.__init__(self, **kwargs)

    def get_class(self):
        "load and return thing class"
        pkg = PackageLoader(self.data['path'])
        if self.data['meta_id'] in pkg.classes:
            return pkg.classes[self.data['meta_id']][1]


class Profile(_TableORM):
    "a thing registry profile"
    TABLE = "PROFILE"
    PKEY = "profile_id"

    def show_info(self, file=sys.stdout):
        file.write("profile : {}\n".format(self.data['profile_id']))
        file.write("thing   : {}\n".format(self.data['meta_id']))
        file.write("token   : {}\n".format(self.data['token']))
        file.write("remote  : {}\n".format(self.data['remote_id']))
        file.write("owner   : {}\n".format(self.data['owner']))

    def make_thing(self, conn):
        "make thing instance according to profile config"
        assert not self.is_empty
        remote = Remote.find(conn, self.data['remote_id'])
        if not remote:
            return

        meta = Meta.find(conn, self.data['meta_id'])
        if not meta:
            return

        cls = meta.get_class()
        if not cls:
            return

        thing = cls(str(self.data['token']), secret=str(self.data['password']))
        thing.set_rest(str(remote['rest_url']), str(remote['rest_ca']))

        args = [None, None, None]
        for i, k in enumerate(("iot_ca", "iot_cert", "iot_key")):
            if self.data[k] not in (None, ""):
                args[i] = str(self.data[k])
        thing.set_tls(*args)
        return thing

    @classmethod
    def list(cls, conn, meta_id):
        cur = conn.execute( \
                "select * from {} where meta_id=? order by {}".format(cls.TABLE, cls.PKEY), \
                (meta_id,))
        return [cls(**x) for x in cls._cursor_to_dictlist(cur)]

