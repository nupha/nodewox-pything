#coding: utf-8
from thing import Thing
import sys
import optparse
import json
import types
import os
import zipfile
import getpass
import traceback

class ProfileExistsError(Exception): 
    pass


def _check_profile(filename):
    path = [os.getcwd(), "/var/lib/nodewox/profiles/"]
    for p in path:
        f = os.path.join(p, filename)
        if os.path.isfile(f):
            return f


def _load_index(filename, default=None, show_err=True):
    if os.path.exists(filename):
        try:
            fh = open(filename, "rb")
            thindex = json.load(fh)
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


def _load_thing_class(entry, show_err=True):
    thindex = _load_index("/var/lib/nodewox/index.json", show_err=show_err)

    if thindex==None:
        if show_err:
            sys.stderr.write("cannot read thing index")
        return None

    if entry not in thindex:
        if show_err:
            sys.stderr.write("thing not installed: %s\n" % entry)
        return None

    res = None
    t = thindex[entry]

    sys.path.append(t['package'])
    try:
        m = __import__(t['module'])
        res = getattr(m, t['class'])
        assert type(res)==types.TypeType and issubclass(res, Thing)
        return res
    except:
        if show_err:
            traceback.print_exc(file=sys.stderr)
            sys.stderr.write("fail to load class for thing %s\n" % entry)
    finally:
        sys.path.remove(t['package'])


def _make_thing(thing_name, profile, show_err=True):
    cls = _load_thing_class(thing_name, show_err=show_err)
    if cls!=None:
        pfname = _check_profile(profile)
        if pfname==None:
            if show_err:
                sys.stderr.write("profile %s not exist\n" % profile)
        else:
            # check thing/profile match
            fh = open(pfname, "rb")
            data = json.load(fh)
            fh.close()

            if getattr(cls, "PID", None)!=data.get("pid"):
                if show_err:
                    sys.stderr.write("thing and profile don't match\n")
                    return

            try:
                return cls(pfname)
            except:
                if show_err:
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.write("\nfail to make instance for thing %s\n" % thing_name)


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
            sys.stderr.write("not a valid zip file %s\n" % pkg)
            continue

        z = zipfile.ZipFile(pkg)
        mods = set()
        for n in z.namelist():
            if n.endswith("/__init__.py"):
                mods.add(n[:-len("/__init__.py")])

        sys.path.append(pkg)
        for mname in list(mods):
            m = __import__(mname)
            lst = []
            for v in vars(m).values():
                if type(v)==types.TypeType and issubclass(v, Thing):
                    lst.append(v.__name__)

            if len(lst)==1:
                sys.stdout.write("%s\n" % mname)
                thindex[mname] = {
                    "package": pkg,
                    "module": mname,
                    "class": lst[0],
                }
            else:
                for c in lst:
                    k = "%s:%s" % (mname, c)
                    sys.stdout.write("%s\n" % k)
                    thindex[k] = {
                        "package": pkg,
                        "module": mname,
                        "class": c,
                    }

        sys.path.remove(pkg)
        z.close()

    fh = open("/var/lib/nodewox/index.json", "wb")
    json.dump(thindex, fh, ensure_ascii=False, indent=4)
    fh.close()


def _cmd_list(argv):
    thindex = _load_index("/var/lib/nodewox/index.json", default={}, show_err=False)
    for k in sorted(thindex.keys()):
        sys.stdout.write("%s\n" % k)


def _cmd_profile(argv):
    p = optparse.OptionParser(usage="%prog [options] thing-name profile-name")

    p.add_option('-u', '--rest-url', 
            action="store", type="string", dest="rest_url", default="https://www.nodewox.org/api",
            help="url of nodewox REST-API, default to https://www.nodewox.org/api")

    p.add_option('-a', '--rest-ca',
            action="store", type="string", dest="rest_ca", default="",
            help="trust ca file for http rest-api, leave blank to use default cacerts")

    p.add_option('-k', '--key', 
            action="store", type="string", dest="key", default="",
            help="identity of thing, auto-generate if not specified")

    p.add_option('-s', '--secret', 
            action="store", type="string", dest="secret", default="",
            help="thing password, auto-generate if not specified")
    
    p.add_option('-p', '--path',
            action="store", type="string", dest="path", default="/var/lib/nodewox/profiles/",
            help="profile store path, default to '/var/lib/nodewox/profiles/'")

    opts, args = p.parse_args(argv[1:])

    if len(args)<2:
        sys.stderr.write("both thing-name and profile-name is required\n")
        sys.exit(-1)

    entry = args[0]
    cls = _load_thing_class(entry)
    if cls==None:
        sys.exit(-1)

    profile = args[1]
    for c in "*/?`()[]{}^&~;":
        if c in profile:
            sys.stderr.write("profile name contains invalid char %s\n" % c)
            sys.exit(-1)

    profile = os.path.join(opts.path, profile)
    if os.path.isfile(profile):
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

    try:
        f = cls.create_profile(profile, rest_url=opts.rest_url, rest_ca=opts.rest_ca, key=opts.key, secret=opts.secret)
        print("profile created %s" % f)
    except ProfileExistsError:
        sys.stderr.write("profile %s already exists\n" % args[0])
    except:
        raise


def _cmd_register(argv):
    p = optparse.OptionParser("%s [options] <thing-name> <profile-name>" % argv[0])
    p.add_option("-u", "--username", 
            action="store", type="string", dest="username", default="",
            help="your nodewox.org account name")

    p.add_option("-p", "--password", 
            action="store", type="string", dest="password", default="",
            help="your nodewox.org account password, prompt will be shown if omitted")

    try:
        opts, args = p.parse_args(argv[1:])
        assert len(args)==2
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

    thing = _make_thing(args[0], args[1])
    if thing!=None:
        thing.register(opts.username, passwd)
    else:
        sys.exit(-1)


def _cmd_start(argv):
    p = optparse.OptionParser("%s [options] <thing-name> <profile-name>" % argv[0])

    try:
        opts, args = p.parse_args(argv[1:])
        assert len(args)>1
    except:
        p.print_help(sys.stdout)
        sys.exit(-1)

    thing = _make_thing(args[0], args[1])
    if thing==None:
        sys.exit(-1)

    if not thing.is_registered:
        sys.stderr.write("this thing not registered\n")
        sys.exit(-1)

    if not thing.load_remote_profile():
        sys.stderr.write("cannot load profile from host\n")
        sys.exit(-1)

    thing.start()


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

