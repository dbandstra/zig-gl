from __future__ import print_function
import os
import xml.etree.ElementTree as ET

required_versions = (
    "GL_VERSION_1_0",
    "GL_VERSION_1_1",
    "GL_VERSION_1_2",
    "GL_VERSION_1_3",
    "GL_VERSION_1_4",
    "GL_VERSION_1_5",
    "GL_VERSION_2_0",
    "GL_VERSION_2_1",
)

required_extensions = (
    "GL_ARB_framebuffer_object",
)

root = ET.parse(os.path.join(os.path.dirname(__file__), "gl.xml")).getroot()

all_types = {}
all_enums = {}
all_commands = {}

constants = set()
commands = set()

def add_requires(node):
    for require in node:
        if require.tag != "require":
            continue
        for child in require:
            if child.tag == "enum":
                constants.add(child.attrib["name"])
            if child.tag == "command":
                commands.add(child.attrib["name"])

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
    if node.tag == "feature" and node.attrib["name"] in required_versions:
        add_requires(node)
    if node.tag == "extensions":
        for child in node:
            if child.tag == "extension" and child.attrib["name"] in required_extensions:
                add_requires(child)

print("typedef signed char khronos_int8_t;")
print("typedef float khronos_float_t;")
print("typedef signed short int khronos_int16_t;")
print("typedef signed char khronos_int8_t;")
print("typedef signed long int khronos_intptr_t;")
print("typedef signed long int khronos_ssize_t;")
print("typedef unsigned short int khronos_uint16_t;")
print("typedef unsigned char khronos_uint8_t;")

for typename in ["GLbitfield", "GLboolean", "GLbyte", "GLchar", "GLdouble", "GLenum",
    "GLfloat", "GLint", "GLintptr", "GLshort", "GLsizei", "GLsizeiptr", "GLubyte",
    "GLuint", "GLushort"]:
    print(all_types[typename])

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
