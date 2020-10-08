from __future__ import print_function
import os
import sys
import xml.etree.ElementTree as ET

profiles = {
    "2.1": {
        "required_versions": set([
            "GL_VERSION_1_0",
            "GL_VERSION_1_1",
            "GL_VERSION_1_2",
            "GL_VERSION_1_3",
            "GL_VERSION_1_4",
            "GL_VERSION_1_5",
            "GL_VERSION_2_0",
            "GL_VERSION_2_1",
        ]),
        "extra_khronos_types": set(),
        "extra_types": set(),
    },
    "3.2": {
        "required_versions": set([
            "GL_VERSION_1_0",
            "GL_VERSION_1_1",
            "GL_VERSION_1_2",
            "GL_VERSION_1_3",
            "GL_VERSION_1_4",
            "GL_VERSION_1_5",
            "GL_VERSION_2_0",
            "GL_VERSION_2_1",
            "GL_VERSION_3_0",
            "GL_VERSION_3_1",
            "GL_VERSION_3_2",
        ]),
        "extra_khronos_types": set(["khronos_int64_t", "khronos_uint64_t"]),
        "extra_types": set(["GLsync", "GLint64", "GLuint64"]),
    },
}

if len(sys.argv) < 2:
    profiles = sorted(profiles.keys())
    sys.stderr.write("usage: {} VERSION [EXTENSIONS...]\n".format(sys.argv[0]))
    sys.stderr.write("supported versions: {}\n".format(", ".join(profiles)))
    sys.exit(1)

required_extensions = set(sys.argv[2:])

try:
    profile = profiles[sys.argv[1]]
except:
    sys.stderr.write("unrecognized profile: '{}'\n".format(sys.argv[1]))
    sys.exit(1)

root = ET.parse(os.path.join(os.path.dirname(__file__), "gl.xml")).getroot()

all_types = {}
all_enums = {}
all_commands = {}

all_khronos_types = {
    "khronos_float_t": "float",
    "khronos_int16_t": "signed short int",
    "khronos_int64_t": "int64_t",
    "khronos_int8_t": "signed char",
    "khronos_int8_t": "signed char",
    "khronos_intptr_t": "signed long int",
    "khronos_ssize_t": "signed long int",
    "khronos_uint16_t": "unsigned short int",
    "khronos_uint64_t": "uint64_t",
    "khronos_uint8_t": "unsigned char",
}

default_khronos_types = set(["khronos_float_t", "khronos_int16_t", "khronos_int8_t",
    "khronos_int8_t", "khronos_intptr_t", "khronos_ssize_t", "khronos_uint16_t",
    "khronos_uint8_t"])

default_types = set(["GLbitfield", "GLboolean", "GLbyte", "GLchar", "GLdouble",
    "GLenum", "GLfloat", "GLint", "GLintptr", "GLshort", "GLsizei", "GLsizeiptr",
    "GLubyte", "GLuint", "GLushort"])

constants = set()
commands = set()

all_extensions = set()

def add_requires(node):
    for n in node:
        if n.tag == "require":
            for child in n:
                if child.tag == "enum":
                    constants.add(child.attrib["name"])
                if child.tag == "command":
                    commands.add(child.attrib["name"])
        if n.tag == "remove":
            for child in n:
                if child.tag == "enum":
                    constants.remove(child.attrib["name"])
                if child.tag == "command":
                    commands.remove(child.attrib["name"])

for node in root:
    if node.tag == "types":
        for type_ in node:
            if type_.tag != "type":
                continue
            try:
                name = next(c.text for c in type_ if c.tag == "name")
                all_types[name] = "".join(type_.itertext())
            except:
                pass
    if node.tag == "enums":
        for enum in node:
            if enum.tag != "enum":
                continue
            all_enums[enum.attrib["name"]] = enum.attrib["value"]
    if node.tag == "commands":
        for command in node:
            if command.tag != "command":
                continue
            proto = next(c for c in command if c.tag == "proto")
            name = next(c.text for c in proto if c.tag == "name")
            params = []
            for c in command:
                if c.tag == "param":
                    params.append({
                        "name": next(d.text for d in c if d.tag == "name"),
                        "decl": "".join(c.itertext()),
                    })
            all_commands[name] = {
                "name": name,
                "decl": "".join(proto.itertext()),
                "params": params,
            }
    if node.tag == "feature" and \
       node.attrib["name"] in profile["required_versions"]:
        add_requires(node)
    if node.tag == "extensions":
        for child in node:
            if child.tag == "extension":
                all_extensions.add(child.attrib["name"])
                if child.attrib["name"] in required_extensions:
                    add_requires(child)

bad_extensions = required_extensions - all_extensions
if bad_extensions:
    desc = ", ".join(sorted(bad_extensions))
    sys.stderr.write("unrecognized extension(s): {}\n".format(desc))
    sys.exit(1)

print("#include <inttypes.h>")

for name in default_khronos_types | profile["extra_khronos_types"]:
    print("typedef {} {};".format(all_khronos_types[name], name))

for name in default_types | profile["extra_types"]:
    print(all_types[name])

for name in constants:
    print("#define {} {}".format(name, all_enums[name]))

for name in commands:
    command = all_commands[name]
    print("extern {}(".format(
        command["decl"].replace(command["name"], "(*{})".format(command["name"]))
    ), end="")
    if len(command["params"]) > 0:
        print(", ".join(param["decl"] for param in command["params"]), end="")
    else:
        print("void", end="")
    print(");")
