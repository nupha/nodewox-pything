#coding: utf-8
from thing import Thing
from node import U8
import sys
import optparse
import json
import types
import os
import zipfile
import getpass
import uuid
import traceback

def _load_profile(filename):
    path = [os.getcwd(), "/var/lib/nodewox/profiles/"]
    data = None

    for p in path:
        f = os.path.join(p, filename)
        if os.path.isfile(f):
            fh = open(f)
            try:
                data = U8(json.load(fh))
            except:
                pass
            finally:
                fh.close()

            if data:
                if data.get("key", "")=="":
                    sys.stderr.write("invalid profile %s\n" % filename)
                if data.get("rest_url", "")=="":
                    sys.stderr.write("invalid profile %s\n" % filename)
                break

    if data:
        return f, data
    else:
        sys.stderr.write("can't find profile %s\n" % filename)
        return None, None


def _profile_clear_registry(profile):
    filename, data = _load_profile(profile)
    if data!=None:
        path = os.path.dirname(filename)

        for k in ("cafile", "certfile", "keyfile"):
            if data.get(k, "")!="":
                f = os.path.join(path, data[k])
                if os.path.isfile(f):
                    os.remove(f)
                del data[k]

        # save profile
        os.umask(0o177)
        fh = open(filename, "w")
        json.dump(data, fh, ensure_ascii=False, indent=4)
        fh.close()


def _load_index(filename, default=None, show_err=True):
    if os.path.exists(filename):
        try:
            fh = open(filename, "rb")
            thindex = U8(json.load(fh))
            fh.close()
            if type(thindex)==types.DictType:
                return thindex
            elif show_err:
                sys.stderr.write("invalid index data\n")
        except:
            if show_err:
                sys.stderr.write("cannot read index\n")
    else:
        if show_err:
            sys.stderr.write("index file not exists\n")

    return default


def _load_thing_class(index, show_err=True):
    thindex = _load_index("/var/lib/nodewox/index.json", show_err=show_err)
    if thindex==None:
        if show_err:
            sys.stderr.write("cannot read thing index")
        return None

    if index not in thindex:
        if show_err:
            sys.stderr.write("thing not installed: %s\n" % index)
        return None

    res = None
    t = thindex[index]

    sys.path.append(t['package'])
    try:
        names = t['module'].split(".")
        m = __import__(t['module'], fromlist=names[:-1])
        res = getattr(m, t['class'])
        assert type(res)==types.TypeType and issubclass(res, Thing)
        return res
    except:
        if show_err:
            traceback.print_exc(file=sys.stderr)
            sys.stderr.write("fail to load class for thing %s\n" % t['package'])
    finally:
        sys.path.remove(t['package'])


def _thing_instantiate(profile, show_err=True):
    filename, data = _load_profile(profile)
    if data==None:
        sys.stderr.write("cannot load profile %s\n" % profile)
        return None

    if "index" not in data:
        sys.stderr.write("profile %s missing index field\n" % profile)
        return None

    cls = _load_thing_class(data['index'], show_err=show_err)
    if cls!=None:
        if getattr(cls, "PID", None)!=data.get("pid"):
            if show_err:
                sys.stderr.write("thing and profile don't match\n")
                return

        try:
            args = {
                    "rest_url": data['rest_url'],
                    "rest_ca": data.get("rest_ca") or "",
                    "certfile": data.get("certfile") or "",
                    "keyfile": data.get("keyfile") or "",
                    "cafile": data.get("cafile") or "",
                    "password": data.get("password") or "",
            }

            # fix fullpath
            path = os.path.dirname(filename)
            for k in ("cafile", "certfile", "keyfile", "rest_ca"):
                if args[k]!="":
                    args[k] = os.path.join(path, args[k])
            return cls(data['key'], **args)

        except:
            if show_err:
                traceback.print_exc(file=sys.stderr)
                sys.stderr.write("\nfail to make instance for profile %s\n" % profile)


def _cmd_install(argv):
    p = optparse.OptionParser("%s [options] pkgfile" % argv[0])

    try:
        opts, args = p.parse_args(argv[1:])
        assert len(args)>0
    except:
        p.print_help(sys.stdout)
        return

    thindex = _load_index("/var/lib/nodewox/index.json", default={}, show_err=False)

    for pkg in args:
        pkg = os.path.abspath(pkg)
        if not zipfile.is_zipfile(pkg):
            sys.stderr.write("'%s' is not a valid package\n" % pkg)
            continue

        z = zipfile.ZipFile(pkg)
        mods = set()
        for n in z.namelist():
            if n.endswith("/__init__.py"):
                mods.add(n[:-len("/__init__.py")])

        sys.path.append(pkg)
        for path in list(mods):
            classes = []
            names = path.split("/")

            if len(names)>0:
                m = __import__(".".join(names), fromlist=names[:-1])
                for v in vars(m).values():
                    if type(v)==types.TypeType and issubclass(v, Thing):
                        if v.PID > 0:
                            classes.append((str(v.PID), v))
                        else:
                            classes.append((".".join(names+[v.__name__]), v))

            if len(classes) > 0:
                for index, c in classes:
                    sys.stdout.write("installed %s\n" % index)
                    thindex[index] = {
                            "package": pkg,
                            "module": ".".join(names),
                            "class": c.__name__,
                            "name": c.NAME,
                    }

        sys.path.remove(pkg)
        z.close()

    fh = open("/var/lib/nodewox/index.json", "wb")
    json.dump(thindex, fh, ensure_ascii=False, indent=4)
    fh.close()


def _cmd_list(argv):
    thindex = _load_index("/var/lib/nodewox/index.json", default={}, show_err=False)
    for k, v in sorted([(x,y) for x,y in thindex.items()]):
        sys.stdout.write("%s\n" % k)


def _cmd_profile(argv):
    p = optparse.OptionParser(usage="%prog [options] <thing-index> <profile-name>")

    p.add_option('-u', '--rest-url', 
            action="store", type="string", dest="rest_url", default="https://www.nodewox.org/api",
            help="url of nodewox REST-API, default to https://www.nodewox.org/api")

    p.add_option('-a', '--rest-ca',
            action="store", type="string", dest="rest_ca", default="",
            help="trust ca file for http rest-api, leave blank to use default cacerts")

    p.add_option('-k', '--key', 
            action="store", type="string", dest="key", default="",
            help="identity of thing, auto-generate if not specified")

    p.add_option('-s', '--password', 
            action="store", type="string", dest="password", default="",
            help="thing password, auto-generate if not specified")
    
    p.add_option('-p', '--path',
            action="store", type="string", dest="path", default="/var/lib/nodewox/profiles/",
            help="profile store path, default to '/var/lib/nodewox/profiles/'")

    p.add_option('-f', '--force',
            action="store_true", dest="force", default=False,
            help="override existing profile")

    opts, args = p.parse_args(argv[1:])

    if len(args)<2:
        sys.stderr.write("both thing-name and profile-name is required\n")
        sys.exit(-1)

    index = args[0]
    cls = _load_thing_class(index)
    if cls==None:
        sys.exit(-1)

    if cls.PID > 0:
        assert index==str(cls.PID)

    profile = args[1]
    for c in "*/?`()[]{}^&~;":
        if c in profile:
            sys.stderr.write("profile name contains invalid char %s\n" % c)
            sys.exit(-1)

    profile = os.path.join(opts.path, profile)
    if not opts.force and os.path.isfile(profile):
        sys.stderr.write("file %s already exists\n" % profile)
        sys.exit(-1)

    if not opts.rest_url.startswith("https://"):
        sys.stderr.write("REST-API url must starts with https://\n")
        sys.exit(-1)

    if opts.rest_ca!="" and not os.path.isfile(opts.rest_ca):
        sys.stderr.write("cannot find cafile %s\n" % opts.rest_ca)
        sys.exit(-1)
        
    if not os.path.isdir(opts.path):
        sys.stderr.write("invalid path %s\n" % opts.path)
        sys.exit(-1)

    if opts.key!="":
        if "/" in opts.key:
            print(sys.stderr, "char '/' is invalid for key")
            sys.exit(-1)

        if len(opts.key)<32:
            print(sys.stderr, "key width too small (must be greater than 32)")
            sys.exit(-1)
    else:
        opts.key = str(uuid.uuid1()).replace("-", "")

    if opts.password=="":
        opts.password = str(uuid.uuid1()).replace("-", "")

    d = {"index":index, "key":opts.key, "password":opts.password, "rest_url":opts.rest_url}
    if cls.PID > 0:
        d['pid'] = cls.PID

    if opts.rest_ca!="":
        d['rest_ca'] = os.path.abspath(opts.rest_ca)

    os.umask(0o177)
    fh = open(profile, "w")
    fh.write(json.dumps(d, ensure_ascii=False, indent=4))
    fh.close()

    sys.stdout.write("profile created %s\n" % profile)


def _cmd_register(argv):
    p = optparse.OptionParser("%s [options] <profile>" % argv[0])
    p.add_option("-u", "--username", 
            action="store", type="string", dest="username", default="",
            help="your nodewox.org account name")

    p.add_option("-p", "--password", 
            action="store", type="string", dest="password", default="",
            help="your nodewox.org account password, prompt will be shown if omitted")

    try:
        opts, args = p.parse_args(argv[1:])
        assert len(args)==1
    except:
        p.print_help(sys.stdout)
        sys.exit(-1)

    if opts.username=="":
        sys.stderr.write("username is required\n")
        sys.exit(-1)

    passwd = opts.password
    while passwd=="":
        try:
            passwd = getpass.getpass("password for %s: " % opts.username)
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.exit(-1)

    profile = args[0]
    thing = _thing_instantiate(profile)

    if thing==None:
        sys.exit(-1)

    # do thing register
    status, content = thing.register(opts.username, passwd)

    if status != 200:
        sys.stderr.write("register fail (status=%d) %s" % (status, content))
        sys.exit(-1)

    ack = None
    try:
        d = json.loads(content)
    except:
        sys.stderr.write("invalid response message %s" % content)
        sys.exit(-1)

    if d.get('status') != 0:
        sys.stderr.write("ERROR(%d): %s\n" % (d['status'], d.get('response',"")))
        sys.exit(-1)

    # update local profile
    ack = d['response']
    filename, data = _load_profile(profile)
    path = os.path.dirname(filename)
    os.umask(0o177)

    for k in ("cafile", "certfile", "keyfile"):
        if k in data:
            fname = os.path.join(path, data[k])
            if os.path.isfile(fname):
                del data[k]
                os.remove(fname)

    if "cert" in ack:
        # save mqtt client cert
        fname = "%s.pem" % os.path.basename(profile)
        fh = open(os.path.join(path, fname), "w")
        fh.write(ack['cert'])
        fh.close()
        data['certfile'] = fname
        data['keyfile'] = fname

    if "key" in ack:
        # save mqtt client cert
        fname = "%s.key.pem" % os.path.basename(profile)
        fh = open(os.path.join(path, fname), "w")
        fh.write(ack['key'])
        fh.close()
        data['keyfile'] = fname

    if "trust" in ack:
        # save mqtt ca
        fname = os.path.join("/var/lib/nodewox/trust/", "%s.pem" % os.path.basename(profile))
        fh = open(fname, "w")
        fh.write(ack['trust'])
        fh.close()
        data['cafile'] = fname

        # c_rehash for new ca
        # TODO...

    fh = open(filename, "w")
    json.dump(data, fh, ensure_ascii=False, indent=4)
    fh.close()

    sys.stdout.write("registered\n")


def _cmd_start(argv):
    p = optparse.OptionParser("%s [options] <thing-name> <profile-name>" % argv[0])

    try:
        opts, args = p.parse_args(argv[1:])
        assert len(args)>=1
    except:
        p.print_help(sys.stdout)
        sys.exit(-1)

    profile = args[0]
    thing = _thing_instantiate(profile)
    if thing==None:
        sys.exit(-1)

    if not thing.is_registered:
        sys.stderr.write("thing is not registered\n")
        sys.exit(-1)

    status, resp = thing.load_remote_profile()
    if status == 0:
        thing.start()
    elif status == 404:
        sys.stderr.write("can't find register info on host, clear registry for '%s'\n" % profile)
        _profile_clear_registry(profile)
    else:
        sys.stderr.write("cannot load profile from host: %s %s\n" % (status, resp))
        sys.exit(-1)


def commands():
    p = optparse.OptionParser(usage="%prog cmd [options]")

    p.disable_interspersed_args()
    opts, args = p.parse_args()

    if len(args)==0:
        p.print_help(sys.stderr)
        sys.stderr.write("\nwhere cmd may be: install, list, profile, register, start\n")
        sys.exit(-1)

    cmd = args[0]
    if cmd=="install":
        _cmd_install(args)
    elif cmd=="list":
        _cmd_list(args)
    elif cmd=="profile":
        _cmd_profile(args)
    elif cmd=="register":
        _cmd_register(args)
    elif cmd=="start":
        _cmd_start(args)
    else:
        sys.stderr.write("unknown command %s\n" % cmd)
        p.print_help(sys.stderr)
        sys.exit(-1)

