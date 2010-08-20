import sys
import os
import subprocess
import readline

# Here you can create play commands that are specific to the module, and extend existing commands

MODULE = 'play-debian'

# Commands that are specific to your module

COMMANDS = ['deb:debianize', 'deb:debianize-cluster', 'deb:debianize-module']

HELP = {
    "deb:debianize": "Debianize your application",
    "deb:debianize-cluster": "Debianize your application for a cluster",
    "deb:debianize-module": "Debianize your module"
}

resources = os.path.join(os.path.dirname(os.path.abspath( __file__ )), "resources")

def rl(prompt, preput):
    readline.add_history(preput)
    readline.set_startup_hook(lambda : readline.insert_text(preput))
    return raw_input(prompt)

def execute(**kargs):
    command = kargs.get("command")
    app = kargs.get("app")
    args = kargs.get("args")
    env = kargs.get("env")
    major_version = env.get("version")[:3]
    major_version = rl("Play version: ", major_version)
    print "~ Building for Play version: " + env.get("version") +" (" + major_version +")"
    print "~ Resources path: " + resources

    if os.path.exists("debian") : 
        print "Error: the debian directory already exists, please remove it"
        sys.exit(1)

    user_name = os.getenv("DEBFULLNAME") or os.getenv("NAME") or "Maintainer"
    user_name = rl("Maintainer name: ", user_name)
    email = os.getenv("DEBEMAIL") or os.getenv("EMAIL") or "your.email@localhost"
    email = rl("Maintainer email: ", email)

    os.mkdir("debian")
    if command == "deb:debianize":
        app_name = rl("Application name: ", app.name())
        app_version = rl("Application version: ", "1.0")
        app_user = rl("User to run the application as: ", app_name)
        print "~ Generating debian setup for " + app_name
        # the changelog
        subprocess.check_call(["dch", "--create", "--preserve", "--newversion", app_version, "--package", app_name, "Initial release"])
        files=[]
        # compat
        copy(["debian", "compat"], ["debian", "compat"], files)
        # processed
        copy(["debian", "app.conffiles.in"], ["debian", app_name + ".conffiles"], files)
        copy(["debian", "app.default.in"], ["debian", app_name + ".default"], files)
        copy(["debian", "app.init.d.in"], ["debian", app_name + ".init.d"], files)
        copy(["debian", "control.in"], ["debian", "control"], files)
        copy(["debian", "postinst.in"], ["debian", "postinst"], files)
        copy(["debian", "rules.in"], ["debian", "rules"], files)
        copy(["conf", "application.conf.in"], ["conf", "application.conf.ex"], files)
        copy(["conf", "log4j-prod.properties.in"], ["conf", "log4j-prod.properties.ex"], files)
        # now process
        subprocess.check_call(["perl", "-pi", "-e", 
                               "s'@APP@'"+app_name+"'g; s'@NAME@'"+user_name+"'g; s'@EMAIL@'"+email+"'g; s'@PLAY_MAJOR_VERSION@'"+major_version+"'; s'@USER@'"+app_user+"'", 
                               ] + files)
        for m in app.conf.getAllKeys("module."):
            mod_name = m[7:]
            mod_path = app.conf.get(m)
            if(mod_path.find("${play.path}") != 0 or not (mod_name in ["console", "crud", "docviewer", "pdf-head", "secure", "testrunner"])):
                print "~ Do not forget to also package the module " + mod_name + " and add it as a dependency in debian/control"
        print "~ Your application has been debianized, now do the following:"
        print "~  - Do not forget to check the files in debian/*"
        print "~  - Include the configuration from conf/application.conf.ex into your own conf/application.conf"
        print "~  - Edit (if appropriate) and rename conf/log4j-prod.properties.ex into conf/log4j-prod.properties"
    elif command == "deb:debianize-cluster":
        app_name = rl("Application name: ", app.name())
        app_version = rl("Application version: ", "1.0")
        app_user = rl("User to run the application as: ", app_name)
        print "~ Generating debian setup for cluster of " + app_name
        # the changelog
        subprocess.check_call(["dch", "--create", "--preserve", "--newversion", app_version, "--package", app_name, "Initial release"])
        # compat
        files = []
        files1 = []
        files2 = []
        copy(["debian", "compat"], ["debian", "compat"], files)
        # processed
        for cluster, cfiles in [["cluster1", files1], ["cluster2", files2]]:
            copy(["debian-cluster", "app.conffiles.in"], ["debian", app_name + "-" + cluster + ".conffiles"], cfiles)
            copy(["debian", "app.default.in"], ["debian", app_name + "-" + cluster + ".default"], cfiles)
            copy(["debian", "app.init.d.in"], ["debian", app_name + "-" + cluster + ".init.d"], cfiles)
            copy(["debian", "postinst.in"], ["debian", app_name + "-" + cluster + ".postinst"], cfiles)
            copy(["conf", "log4j-prod-cluster.properties.in"], ["conf", "log4j-prod-" + cluster + ".properties.ex"], files)
        copy(["debian-cluster", "control.in"], ["debian", "control"], files)
        copy(["debian-cluster", "rules.in"], ["debian", "rules"], files)
        copy(["conf", "application-cluster.conf.in"], ["conf", "application.conf.ex"], files)
        # now process
        subprocess.check_call(["perl", "-pi", "-e", 
                               "s'@APP@'"+app_name+"'g; s'@NAME@'"+user_name+"'g; s'@EMAIL@'"+email+"'g; s'@PLAY_MAJOR_VERSION@'"+major_version+"'; s'@USER@'"+app_user+"'", 
                               ] + files + files1 + files2)
        subprocess.check_call(["perl", "-pi", "-e", 
                               "s'@CLUSTER@'cluster1'g", 
                               ] + files1)
        subprocess.check_call(["perl", "-pi", "-e", 
                               "s'@CLUSTER@'cluster2'g", 
                               ] + files2)
        for m in app.conf.getAllKeys("module."):
            mod_name = m[7:]
            mod_path = app.conf.get(m)
            if(mod_path.find("${play.path}") != 0 or not (mod_name in ["console", "crud", "docviewer", "pdf-head", "secure", "testrunner"])):
                print "~ Do not forget to also package the module " + mod_name + " and add it as a dependency in debian/control"
        print "~ Your application has been debianized, now do the following:"
        print "~  - Do not forget to check the files in debian/*"
        print "~  - Include the configuration from conf/application.conf.ex into your own conf/application.conf"
        print "~  - Edit (if appropriate) and rename conf/log4j-prod-clusterX.properties.ex into conf/log4j-prod-clusterX.properties"
    elif command == "deb:debianize-module":
        module_name = rl("Module name: ", os.path.basename(app.path))
        module_version = rl("Module version: ", "1.0")
        app_name = "play-" + major_version + "-" + module_name + "-module-" + module_version
        app_name = rl("Debian package name: ", app_name)
        print "~ Generating debian setup for module " + module_name + " (deb package: "+app_name+")"
        # the changelog
        subprocess.check_call(["dch", "--create", "--preserve", "--newversion", module_version, "--package", app_name, "Initial release"])
        files=[]
        # compat
        copy(["debian", "compat"], ["debian", "compat"], files)
        # processed
        copy(["debian-module", "control.in"], ["debian", "control"], files)
        copy(["debian-module", "rules.in"], ["debian", "rules"], files)
        # now process
        subprocess.check_call(["perl", "-pi", "-e", 
                               "s'@APP@'"+app_name+"'g; s'@NAME@'"+user_name+"'g; s'@EMAIL@'"+email+"'g; s'@PLAY_MAJOR_VERSION@'"+major_version+"'g; s'@MODULE@'"+module_name+"'g; s'@VERSION@'"+module_version+"'g", 
                               ] + files)
        print "~ Your module has been debianized, now do the following:"
        print "~  - Do not forget to check the files in debian/*"

def copy(from_path, to_path, files):
    to_file = os.path.join(*to_path)
    subprocess.check_call(["cp", os.path.join(resources, *from_path), to_file])
    files.append(to_file)

# This will be executed before any command (new, run...)
def before(**kargs):
    command = kargs.get("command")
    app = kargs.get("app")
    args = kargs.get("args")
    env = kargs.get("env")


# This will be executed after any command (new, run...)
def after(**kargs):
    command = kargs.get("command")
    app = kargs.get("app")
    args = kargs.get("args")
    env = kargs.get("env")

    if command == "new":
        pass
