#!/bin/sh

SOURCEFILE="$1"
shift

if [ ! -f "$SOURCEFILE" ]; then
    echo "error: no SOURCEFILE" >&2
    exit 1
fi

echo "// this file was generated by https://github.com/dbandstra/zig-gl"
echo "//  version: $1"
shift
for GL_EXTENSION in "$@"; do
    echo "//  + $GL_EXTENSION"
done
echo
echo "const builtin = @import(\"builtin\");"
echo
echo "const cc: builtin.CallingConvention ="
echo "    if (builtin.os.tag == .windows and builtin.arch == .i386)"
echo "        .StdCall"
echo "    else"
echo "        .C;"
echo
grep '^pub const khronos' "$SOURCEFILE" | sed 's/^pub //' | sort
echo
grep '^pub const struct___GL' "$SOURCEFILE" | sed 's/^pub //' | sort
if [ ! -z "$PARANOID" ]; then
    echo
    echo "fn checkError(func_name: []const u8) void {"
    echo "    const panic = @import(\"std\").debug.panic;"
    echo "    const err_name = switch (namespace._glGetError()) {"
    echo "        0 => return," # GL_NO_ERROR
    echo "        0x0500 => \"GL_INVALID_ENUM\","
    echo "        0x0501 => \"GL_INVALID_VALUE\","
    echo "        0x0502 => \"GL_INVALID_OPERATION\","
    echo "        0x0503 => \"GL_STACK_OVERFLOW\","
    echo "        0x0504 => \"GL_STACK_UNDERFLOW\","
    echo "        0x0505 => \"GL_OUT_OF_MEMORY\","
    echo "        0x0506 => \"GL_INVALID_FRAMEBUFFER_OPERATION\","
    echo "        0x0507 => \"GL_CONTEXT_LOST\","
    echo "        else => |code| panic(\"{} returned invalid error code {}\", .{func_name, code}),"
    echo "    };"
    echo "    panic(\"{} returned {}\", .{func_name, err_name});"
    echo "}"
fi
echo
echo "pub const namespace = struct {"
grep '^pub const GL[^_]' "$SOURCEFILE" | sort
echo
grep '^pub const GL_' "$SOURCEFILE" | sort
echo
perl -n -e '
if (/^pub extern var (gl[a-zA-Z0-9_]+): \?fn \((.*)\) callconv\(.+?\) (.+);$/) {
    print "var _$1: fn ($2) callconv(cc) $3 = undefined;\n";
}' < "$SOURCEFILE" | sort
echo
perl -n -e '
if (/^pub extern var (gl[a-zA-Z0-9_]+): \?fn \((.*)\) callconv\(.+?\) (.+);$/) {
    my $name = $1;
    my @args = split(/, ?/, $2);
    my $ret = $3;
    for my $i (0 .. $#args) {
        $args[$i] = "arg$i: ${args[$i]}";
    }
    my $args = join(", ", @args);
    print "pub inline fn $name($args) $ret { ";
    if ($ret ne "void") {
        if ($ENV{PARANOID}) {
            print "const result = ";
        } else {
            print "return ";
        }
    }
    print "_$name(";
    for my $i (0 .. $#args) {
        if ($i > 0) {
            print ", ";
        }
        print "arg$i";
    }
    print "); ";
    if ($ENV{PARANOID}) {
        if ($name ne "glGetError") {
            print "checkError(\"$name\"); ";
        }
        if ($ret ne "void") {
            print "return result; ";
        }
    }
    print "}\n";
}' < "$SOURCEFILE" | sort
echo "};"
echo
echo "pub const extensions = [_][:0]const u8{"
for GL_EXTENSION in "$@"; do
    echo "\"$GL_EXTENSION\","
done
echo "};"
echo
echo "pub const Command = struct {"
echo "    name: [:0]const u8,"
echo "    ptr: **const c_void,"
echo "};"
echo
echo "pub const commands = [_]Command{"
perl -n -e '
if (/^pub extern var (gl[a-zA-Z0-9_]+): \?fn/) {
    print ".{ .name = \"$1\", .ptr = \@ptrCast(**const c_void, &namespace._$1) },\n";
}' < "$SOURCEFILE" | sort
echo "};"
