#coding: utf-8
from store import Storage, PackageLoader, Meta, Profile, Remote
import sys
import optparse
import json
import os
import getpass
import uuid

def _cmd_remote(argv):
    p = optparse.OptionParser("%s [options] [remote]" % argv[0])

    p.add_option('-i', '--rest-url', 
            action="store", type="string", dest="rest_url", default="",
            help="set base url to REST API for remote setting")

    p.add_option('-a', '--rest-ca', 
            action="store", type="string", dest="rest_ca", default="",
            help="set CAfile to trust REST for remote setting")

    try:
        opts, args = p.parse_args(argv[1:])
    except:
        p.print_help(sys.stdout)
        return

    conn = Storage().conn

    if len(args)==0:
        for x in Remote.list(conn):
            if x['pri']==1:
                pri = "*"
            else:
                pri = " "
            sys.stdout.write("{} {}\t{}\t{}\n".format(pri, x['remote_id'], x['rest_url'], x['rest_ca']!=""))
        return
        
    remote = Remote.find(conn, args[0])
    if not remote:
        remote = Remote(remote_id=args[0])

    if opts.rest_url!="":
        remote['rest_url'] = opts.rest_url

    if opts.rest_ca=="none":
        remote['rest_ca'] = ""
    elif opts.rest_ca!="":
        fh = open(opts.rest_ca)
        t = fh.read()
        fh.close()
        remote['rest_ca'] = t

    if remote.get("rest_url", "")=="":
        sys.stderr.write("invalid REST API url\n")
        sys.exit(-1)

    remote.save(conn)
    conn.commit()
    conn.close()


def _cmd_install(argv):
    p = optparse.OptionParser("%s [options] package-path" % argv[0])

    try:
        opts, args = p.parse_args(argv[1:])
        assert len(args)>0
    except:
        p.print_help(sys.stdout)
        return

    conn = Storage().conn
    for path in args:
        if not os.path.exists(path):
            sys.stderr.write("path '{}' not exists\n".format(path))
            continue

        pkg = PackageLoader(path)
        for index, (modname, cls) in pkg.classes.items():
            meta = Meta(**{
                "meta_id": index, 
                "path": path, 
                "module": modname, 
                "class": cls.__name__,
                "name": cls.NAME,
                "pid": cls.PID
            })
            meta.save(conn)
            sys.stdout.write("installed %s\n" % index)
    conn.commit()
    conn.close()


def _cmd_list(argv):
    conn = Storage().conn
    for meta in Meta.list(conn):
        sys.stdout.write("%s\n" % meta['meta_id'])
        for p in Profile.list(conn, meta["meta_id"]):
            sys.stdout.write("\t{}\t{}\n".format(p['name'], p['remote_id']))
    conn.close()


def _cmd_register(argv):
    p = optparse.OptionParser("%s [options] thing" % argv[0])

    p.add_option('-r', '--remote', 
            action="store", type="string", dest="remote", default="",
            help="remote settings, default to the primary one")

    p.add_option('-t', '--token', 
            action="store", type="string", dest="token", default="",
            help="identity token of thing, auto-generate one if not given")

    p.add_option('-o', '--profile',
            action="store", type="string", dest="profile", default="",
            help="profile name that used to store register results")

    p.add_option('-f', '--force',
            action="store_true", dest="force", default=False,
            help="force to override if profile name is existed")

    p.add_option("-U", "--username", 
            action="store", type="string", dest="username", default="",
            help="username of your account")

    p.add_option("-P", "--password", 
            action="store", type="string", dest="password", default="",
            help="password your account, prompt to ask if omitted")

    try:
        opts, args = p.parse_args(argv[1:])
        assert len(args)>0
    except:
        p.print_help(sys.stdout)
        sys.exit(-1)

    conn = Storage().conn

    # check thing
    meta = Meta.find(conn, args[0])
    if not meta:
        if os.path.exists(args[0]):
            pkg = PackageLoader(args[0])
            if len(pkg.classes)>1:
                sys.stderr.write("more than one thing found in {}\n".format(args[0]))
                for k in pkg.classes:
                    sys.stderr.write("    {}\n".format(k))
                sys.stderr.write("don't known which one to register, abort.\n".format(args[0]))
                sys.exit(-1)
            elif len(pkg.classes)==0:
                sys.stderr.write("no thing class found in {}, abort.\n".format(args[0]))
                sys.exit(-1)
            else:
                meta = Meta.find(conn, pkg.classes.keys()[0])
                if meta==None:
                    sys.stdout.write("thing '{}' is not installed yet.\nlet's install it first ...".format(pkg.classes.keys()[0]))
                    meta_id, (modname, cls) = pkg.classes.items()[0]
                    meta = Meta(**{
                        "meta_id": meta_id, 
                        "path": pkg.path, 
                        "module": modname, 
                        "class": cls.__name__,
                        "name": cls.NAME,
                        "pid": cls.PID
                    })
                    meta.save(conn)
                    sys.stdout.write(" done\n")

    if not meta:
        sys.stderr.write("unkown thing {}\n".format(args[0]))
        sys.exit(-1)

    meta_id = meta._id
    cls = meta.get_class()
    if cls==None:
        sys.stderr.write("can't load thing {}\n".format(meta_id))
        sys.exit(-1)

    # check profile
    profile = opts.profile
    if profile == "":
        profile_id = meta_id
    else:
        for c in "*/?`()[]{}^&~;.":
            if c in opts.profile:
                sys.stderr.write("profile name contains invalid char %s\n" % c)
                sys.exit(-1)
        profile_id = "{}/{}".format(meta_id, opts.profile)

    prf = Profile.find(conn, profile_id)
    if prf:
        if not opts.force:
            sys.stderr.write("profile %s already existed\n" % profile_id)
            sys.exit(-1)

        # use existing profile attrs
        if prf['meta_id']!=meta_id:
            sys.stderr.write(
                    "thing name mismatch: '{}' vs '{}' in profile {}\n"
                    .format(meta_id, prf['meta_id'], profile_id)
            )
            sys.exit(-1)

        if opts.token=="":
            opts.token = prf['token']
        elif opts.token!=prf['token']:
            sys.stderr.write("token mismatch\n")
            sys.exit(-1)

        if opts.remote=="":
            opts.remote = prf['remote_id']
        elif opts.remote!=prf['remote_id']:
            sys.stderr.write("remote mismatch\n")
            sys.exit(-1)

    # check for remote
    if opts.remote=="":
        remote = Remote.primary(conn)
        if not remote:
            sys.stderr.write("no primary remote setting\n")
            sys.exit(-1)
    else:
        remote = Remote.find(conn, opts.remote)
        if not remote:
            sys.stderr.write("unkown remote setting {}\n".format(opts.remote))
            sys.exit(-1)

    if opts.token!="":
        if "/" in opts.token:
            print(sys.stderr, "char '/' is invalid for token")
            sys.exit(-1)
    else:
        opts.token = str(uuid.uuid1()).replace("-", "")

    secret = str(uuid.uuid1()).replace("-", "")

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

    # print register info
    sys.stdout.write("registering:\n")
    sys.stdout.write("    thing:   {}\n".format(meta_id))
    sys.stdout.write("    token:   {}\n".format(opts.token))
    sys.stdout.write("    remote:  {} ({})\n".format(remote._id, remote['rest_url']))
    sys.stdout.write("    owner:   {}\n".format(opts.username))
    sys.stdout.write("    profile: {}\n".format(profile_id))

    # make thing instance & register
    thing = cls(opts.token, secret=secret)
    thing.set_rest(remote['rest_url'], remote['rest_ca'])
    status, content = thing.register(opts.username, passwd)
    if status != 200:
        sys.stderr.write("register fail ({}): {}\n".format(status, content))
        sys.exit(-1)

    ack = None
    try:
        d = json.loads(content)
    except:
        sys.stderr.write("invalid response message %s\n" % content)
        sys.exit(-1)

    if d.get('status') != 0:
        sys.stderr.write("ERROR(%d): %s\n" % (d['status'], d.get('response',"")))
        sys.exit(-1)

    ack = d['response']

    # save profile
    pfile = Profile(profile_id=profile_id, meta_id=meta_id, name=opts.profile, token=opts.token, \
            password=secret, remote_id=opts.remote, owner=opts.username)

    if "cert" in ack:
        pfile['iot_cert'] = ack['cert'][0]
        pfile['iot_key'] = ack['cert'][1]
    else:
        pfile["iot_cert"] = ""
        pfile["iot_key"] = ""

    if "trust" in ack:
        pfile['iot_ca'] = ack['trust']
    else:
        pfile['iot_ca'] = ""

    pfile.save(conn)
    conn.commit()
    conn.close()

    sys.stdout.write("successfully registered as '{}'\n".format(profile_id))


def _cmd_start(argv):
    p = optparse.OptionParser("%s [options] <thing> <profile>" % argv[0])

    try:
        opts, args = p.parse_args(argv[1:])
        assert len(args)>=1
    except:
        p.print_help(sys.stdout)
        sys.exit(-1)

    conn = Storage().conn

    profile = Profile.find(conn, args[0])
    if not profile:
        sys.stderr.write("can't load profile {}\n".format(args[0]))
        sys.exit(-1)

    profile.show_info(sys.stdout)
    thing = profile.make_thing(conn)
    if thing==None:
        sys.stderr.write("can't load make thing for {}\n".format(args[0]))
        sys.exit(-1)

    status, resp = thing.load_remote_profile()
    if status == 0:
        conn.close()
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
        sys.stderr.write("\nwhere cmd may be: install, list, remote, register, start\n")
        sys.exit(-1)

    cmd = args[0]
    if cmd=="install":
        _cmd_install(args)
    elif cmd=="list":
        _cmd_list(args)
    elif cmd=="remote":
        _cmd_remote(args)
    elif cmd=="register":
        _cmd_register(args)
    elif cmd=="start":
        _cmd_start(args)
    else:
        sys.stderr.write("unknown command %s\n" % cmd)
        p.print_help(sys.stderr)
        sys.exit(-1)

