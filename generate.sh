#!/bin/sh

THIS_DIR=`dirname "$0"`

python "$THIS_DIR/make_c_header.py" "$@" > "$THIS_DIR/gl_pre.h" || exit 1

zig translate-c "$THIS_DIR/gl_pre.h" > "$THIS_DIR/gl_post.zig" || exit 1

bash "$THIS_DIR/postprocess.sh" "$THIS_DIR/gl_post.zig" "$@" | zig fmt --stdin
