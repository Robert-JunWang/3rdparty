import glob, re, os, os.path, shutil, string, sys

libName = 'Imlib2'
#extraFlag = '--disable-shared --enable-static --with-darwinssl --enable-threaded-resolver'
extraFlag = '--enable-amd64=no --enable-mmx=no --without-png --without-tiff --without-gif --enable-shared=no --with-x=no --without-bzip2 '
XCODEDIR = os.popen('xcode-select --print-path').read().strip()
IOS_SDK_VERSION = os.popen('xcrun --sdk iphoneos --show-sdk-version').read().strip()

MIN_SDK_VERSION='7.0'

#IPHONEOS_PLATFORM=os.popen('xcrun --sdk iphoneos --show-sdk-platform-path').read()
IPHONEOS_PLATFORM='/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform'
#IPHONEOS_SYSROOT=os.popen('xcrun --sdk iphoneos --show-sdk-path').read()
IPHONEOS_SYSROOT='/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk'

IPHONESIMULATOR_PLATFORM=os.popen('xcrun --sdk iphonesimulator --show-sdk-platform-path').read().strip()
IPHONESIMULATOR_SYSROOT=os.popen('xcrun --sdk iphonesimulator --show-sdk-path').read().strip()

# Uncomment if you want to see more information about each invocation
# of clang as the builds proceed.
# CLANG_VERBOSE="--verbose"
CLANG_VERBOSE = ''


CC='/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang'
CXX=CC

#CFLAGS='${CLANG_VERBOSE} -DNDEBUG -g -O0 -pipe -fPIC -fcxx-exceptions'
CFLAGS='-g -pipe -Os -gdwarf-2 -I/Users/robertwang/3rdtools/ios/prebuild/include/jpeg '
CXXFLAGS=CLANG_VERBOSE + CFLAGS + ' -std=c++11 -stdlib=libc++'
CPPFLAGS=''
#"-DNDEBUG -D__IPHONE_OS_VERSION_MIN_REQUIRED=" + MIN_SDK_VERSION + "0000 "
LDFLAGS='-L/Users/robertwang/3rdtools/ios/prebuild/lib'

def build_target(srcroot, buildroot, target, arch):
    print "builds " + arch + " for " + target

    os.system("tput sgr0")

    builddir = os.path.join(buildroot, target + '-' + arch)
    if not os.path.isdir(builddir):
        os.makedirs(builddir)
    currdir = os.getcwd()
    os.chdir(srcroot)

    #os.system("cd %s" % (srcroot,))
    os.system("make clean")

    configArgs = ('--host="arm-apple-darwin" ' +
                '--prefix="%s" ' +
                'CC="%s" ' +
                'CFLAGS="-arch %s -mios-version-min=%s ' +
                '-isysroot %s %s" '
                'CXX="%s" CXXFLAGS="%s ' +
                '-arch %s -isysroot %s" ' +
                'LDFLAGS="-arch %s %s -isysroot %s" '
                ) % ( 
                builddir, 
                CC, 
                arch, MIN_SDK_VERSION,  
                IPHONEOS_SYSROOT,CFLAGS,
                CXX, CXXFLAGS,
                arch, IPHONEOS_SYSROOT,
                arch, LDFLAGS, IPHONEOS_SYSROOT)


    print (configArgs + ' ' + extraFlag)
    os.system("./configure  %s %s " % (configArgs, extraFlag))

    os.system("make")
    os.system("make install")
    
    os.system("tput setaf 2")


def build_simulator(srcroot, buildroot, arch):

    target = 'iPhoneSimulator'
    #print('builds ' + arch + ' for Simulator')

    os.system("tput sgr0")

    builddir = os.path.join(buildroot, target + '-' + arch)
    if not os.path.isdir(builddir):
        os.makedirs(builddir)
    currdir = os.getcwd()
    os.chdir(srcroot)

    #os.system("cd %s" % (srcroot,))
    os.system("make clean")

    configArgs = ('--host="x86-apple-darwin" ' +
                '--prefix="%s" ' +
                'CC="%s" ' +
                'CFLAGS="-arch %s -mios-version-min=%s ' +
                '-isysroot %s %s" '
                'CXX="%s" CXXFLAGS="%s ' +
                '-arch %s -isysroot %s" ' +
                'LDFLAGS="-arch %s %s -isysroot %s" '
                ) % ( 
                builddir, 
                CC, 
                arch, MIN_SDK_VERSION,  
                IPHONESIMULATOR_SYSROOT,CFLAGS,
                CXX, CXXFLAGS,
                arch, IPHONESIMULATOR_SYSROOT,
                arch, LDFLAGS, IPHONESIMULATOR_SYSROOT)


    print (configArgs + ' ' + extraFlag)
    os.system("./configure  %s %s " % (configArgs, extraFlag))

    os.system("make")
    os.system("make install")
    
    os.system("tput setaf 2")

def put_framework_together(srcroot, dstroot):
    "constructs the framework directory after all the targets are built"

    # find the list of targets (basically, ["iPhoneOS", "iPhoneSimulator"])
    targetlist = glob.glob(os.path.join(dstroot, "build", "*"))
    targetlist = [os.path.basename(t) for t in targetlist]

    # set the current dir to the dst root
    currdir = os.getcwd()
    framework_dir = dstroot + "/" + libName + ".framework"
    if os.path.isdir(framework_dir):
        shutil.rmtree(framework_dir)
    os.makedirs(framework_dir)
    os.chdir(framework_dir)

    # form the directory tree
    dstdir = "Versions/A"
    os.makedirs(dstdir + "/Resources")

    tdir0 = dstroot + "/build/" + targetlist[0]

    # make universal static lib
    wlist = " ".join([ dstroot + "/build/" + t + "/lib/lib" + libName + ".a" for t in targetlist])
    os.system("lipo -create " + wlist + " -o " + dstdir + "/" + libName)

    # copy headers
    shutil.copytree(tdir0 + "/include" , dstdir + "/Headers")

    # copy Info.plist
    #shutil.copyfile(tdir0 + "/ios/Info.plist", dstdir + "/Resources/Info.plist")

    # make symbolic links
    os.symlink("A", "Versions/Current")
    os.symlink("Versions/Current/Headers", "Headers")
    os.symlink("Versions/Current/Resources", "Resources")
    os.symlink("Versions/Current/" + libName, libName)


def build_framework(srcroot, dstroot):
    "main function to do all the work"

    #targets = ["iPhoneOS", "iPhoneOS", "iPhoneOS", "iPhoneSimulator", "iPhoneSimulator"]
    #archs = ["armv7", "armv7s", "arm64", "i386", "x86_64"]

    archs = ["arm64","armv7s","armv7"]
    for i in range(len(archs)):
        build_target(srcroot, os.path.join(dstroot, "build"), 'iPhoneOS', archs[i])

    build_simulator(srcroot, os.path.join(dstroot, "build"), 'x86_64')
    put_framework_together(srcroot, dstroot)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print "Usage:\n\t./build_framework.py <srcdir> <outputdir>\n\n"
        sys.exit(0)

    build_framework(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]))
