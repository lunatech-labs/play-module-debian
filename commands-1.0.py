#    This file is part of debian-play-module.
#    
#    Copyright Lunatech Research 2010
#
#    debian-play-module is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    debian-play-module is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Lesser Public License
#    along with debian-play-module.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import subprocess
import readline

resources = os.path.join(os.path.abspath(module), "resources")

def rl(prompt, preput):
    readline.add_history(preput)
    readline.set_startup_hook(lambda : readline.insert_text(preput))
    return raw_input(prompt)

def copy(from_path, to_path, files):
    to_file = os.path.join(*to_path)
    subprocess.check_call(["cp", os.path.join(resources, *from_path), to_file])
    files.append(to_file)

def getAllKeys(key):
    result = []
    if application_path:
        for line in open(os.path.join(application_path, 'conf/application.conf')).readlines():
            if line.startswith(key):
                result.append(line[:line.find('=')].strip())
        for line in open(os.path.join(application_path, 'conf/application.conf')).readlines():
            prefix = '%' + play_id + '.'
            if line.startswith(prefix + key):
                result.append(line[len(prefix):line.find('=')].strip())
    return result

if (play_command == "deb:debianize" or play_command == "deb:debianize-module" or play_command == "deb:debianize-cluster") :
    application_name = readConf('application.name')
    if not application_name:
        application_name = os.path.dirname(application_path)
    major_version = play_version[:3]
    major_version = rl("Play version: ", major_version)
    print "~ Building for Play version: " + major_version +" (" + major_version +")"
    print "~ Resources path: " + resources

    if os.path.exists("debian") : 
        print "Error: the debian directory already exists, please remove it"
        sys.exit(1)

    user_name = os.getenv("DEBFULLNAME") or os.getenv("NAME") or "Maintainer"
    user_name = rl("Maintainer name: ", user_name)
    email = os.getenv("DEBEMAIL") or os.getenv("EMAIL") or "your.email@localhost"
    email = rl("Maintainer email: ", email)

    os.mkdir("debian")
    if play_command == "deb:debianize":
        app_name = rl("Application name: ", application_name)
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
        copy(["debian", "preinst.in"], ["debian", "preinst"], files)
        copy(["debian", "postinst.in"], ["debian", "postinst"], files)
        copy(["debian", "rules.in"], ["debian", "rules"], files)
        copy(["conf", "application.conf.in"], ["conf", "application.conf.ex"], files)
        copy(["conf", "log4j-prod.properties.in"], ["conf", "log4j-prod.properties.ex"], files)
        # now process
        subprocess.check_call(["perl", "-pi", "-e", 
                               "s'@APP@'"+app_name+
                               "'g; s'@NAME@'"+user_name+
                               "'g; s'@EMAIL@'"+email+
                               "'g; s'@PLAY_MAJOR_VERSION@'"+major_version+
                               "'g; s'@CLUSTER@'"+
                               "'g; s'@USER@'"+app_user+"'", 
                               ] + files)
        for m in getAllKeys("module."):
            mod_name = m[7:]
            mod_path = readConf(m)
            if(mod_path.find("${play.path}") != 0 or not (mod_name in ["console", "crud", "docviewer", "pdf-head", "secure", "testrunner"])):
                print "~ Do not forget to also package the module " + mod_name + " and add it as a dependency in debian/control"
        print "~ Your application has been debianized, now do the following:"
        print "~  - Do not forget to check the files in debian/*"
        print "~  - Include the configuration from conf/application.conf.ex into your own conf/application.conf"
        print "~  - Edit (if appropriate) and rename conf/log4j-prod.properties.ex into conf/log4j-prod.properties"
    elif play_command == "deb:debianize-cluster":
        app_name = rl("Application name: ", application_name)
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
            copy(["debian", "preinst.in"], ["debian", app_name + "-" + cluster + ".preinst"], cfiles)
            copy(["debian", "postinst.in"], ["debian", app_name + "-" + cluster + ".postinst"], cfiles)
            copy(["conf", "log4j-prod-cluster.properties.in"], ["conf", "log4j-prod-" + cluster + ".properties.ex"], files)
        copy(["debian-cluster", "control.in"], ["debian", "control"], files)
        copy(["debian-cluster", "rules.in"], ["debian", "rules"], files)
        copy(["conf", "application-cluster.conf.in"], ["conf", "application.conf.ex"], files)
        # now process
        subprocess.check_call(["perl", "-pi", "-e", 
                               "s'@APP@'"+app_name+
                               "'g; s'@NAME@'"+user_name+
                               "'g; s'@EMAIL@'"+email+
                               "'g; s'@PLAY_MAJOR_VERSION@'"+major_version+
                               "'g; s'@USER@'"+app_user+"'", 
                               ] + files + files1 + files2)
        subprocess.check_call(["perl", "-pi", "-e", 
                               "s'@CLUSTER@'cluster1'g", 
                               ] + files1)
        subprocess.check_call(["perl", "-pi", "-e", 
                               "s'@CLUSTER@'cluster2'g", 
                               ] + files2)
        for m in getAllKeys("module."):
            mod_name = m[7:]
            mod_path = readConf(m)
            if(mod_path.find("${play.path}") != 0 or not (mod_name in ["console", "crud", "docviewer", "pdf-head", "secure", "testrunner"])):
                print "~ Do not forget to also package the module " + mod_name + " and add it as a dependency in debian/control"
        print "~ Your application has been debianized, now do the following:"
        print "~  - Do not forget to check the files in debian/*"
        print "~  - Include the configuration from conf/application.conf.ex into your own conf/application.conf"
        print "~  - Edit (if appropriate) and rename conf/log4j-prod-clusterX.properties.ex into conf/log4j-prod-clusterX.properties"
    elif play_command == "deb:debianize-module":
        module_name = rl("Module name: ", os.path.basename(application_path))
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
                               "s'@APP@'"+app_name+
                               "'g; s'@NAME@'"+user_name+
                               "'g; s'@EMAIL@'"+email+
                               "'g; s'@PLAY_MAJOR_VERSION@'"+major_version+
                               "'g; s'@MODULE@'"+module_name+
                               "'g; s'@VERSION@'"+module_version+"'g", 
                               ] + files)
        print "~ Your module has been debianized, now do the following:"
        print "~  - Do not forget to check the files in debian/*"
    sys.exit(0)
fi


