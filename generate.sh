#!/usr/bin/env bash
set -e

THIS_DIR="$(dirname "$0")"

python "$THIS_DIR/make_c_header.py" "$@" > "$THIS_DIR/gl_pre.h"

zig translate-c "$THIS_DIR/gl_pre.h" > "$THIS_DIR/gl_post.zig"

echo "// this file was generated by https://github.com/dbandstra/zig-gl"
echo "//  version: $1"
shift
for GL_EXTENSION in "$@"; do
    echo "//  + $GL_EXTENSION"
done
echo ""
echo "const builtin = @import(\"builtin\");"
echo ""
echo "const cc: builtin.CallingConvention = if (builtin.os.tag == .windows and builtin.arch == .i386)"
echo "    .StdCall"
echo "else"
echo "    .C;"
echo ""
< "$THIS_DIR/gl_post.zig" perl -n -e '
    if (m/^pub const (khronos.+)$/) {
        print "const $1\n";
    }
' | sort
echo ""
OPAQUE_TYPES=$(< "$THIS_DIR/gl_post.zig" perl -n -e '
    if (m/^pub (const struct___GL[^_].+)$/) {
        print "$1";
    }
' | sort)
if [ ! -z "$OPAQUE_TYPES" ]; then
    echo "$OPAQUE_TYPES"
    echo ""
fi
echo "pub const namespace = struct {"
< "$THIS_DIR/gl_post.zig" perl -n -e '
    if (m/^pub const GL[^_]/) {
        print "    $_";
    }
' | sort
echo ""
< "$THIS_DIR/gl_post.zig" perl -n -e '
    if (m/^pub const GL_/) {
        print "    $_";
    }
' | sort
echo ""
< "$THIS_DIR/gl_post.zig" perl -n -e '
    if (m/^pub extern var (gl[a-zA-Z0-9_]+): \?fn \((.+)\) (.+);$/) {
        $_ = "    pub var $1: fn ($2) $3 = undefined;";
        s/callconv\(\.C\)/callconv(cc)/;
        print "$_\n";
    }
' | sort
echo "};"
echo ""
if [ -z "$@" ]; then
    echo "pub const extensions = [_][:0]const u8{};"
else
    echo "pub const extensions = [_][:0]const u8{"
    for GL_EXTENSION in "$@"; do
        echo "    \"$GL_EXTENSION\","
    done
    echo "};"
fi
echo ""
echo "pub const Command = struct {"
echo "    name: [:0]const u8,"
echo "    ptr: **const c_void,"
echo "};"
echo ""
echo "pub const commands = [_]Command{"
< "$THIS_DIR/gl_post.zig" perl -n -e '
    if (m/^pub extern var (gl[a-zA-Z0-9_]+): \?fn/) {
        print "    Command{ .name = \"$1\", .ptr = \@ptrCast(**const c_void, &namespace.$1) },\n";
    }
' | sort
echo "};"
