# zig-gl
Script to generate a Zig file from the Khronos OpenGL Registry. The generated file includes types, function pointers, and a table to help you load the function pointers.

`gl.xml` is from https://github.com/KhronosGroup/OpenGL-Registry

To generate a file, call `generate.sh`. The first argument is the OpenGL version (currently only 2.1 and 3.2 are supported). Any subsequent arguments are extension names.

```sh
sh generate.sh 2.1 GL_ARB_framebuffer_object > generated/2.1+fbo.zig
sh generate.sh 3.2 > generated/3.2.zig
```

The generated files for the above profiles are included in this repository for convenience.

## SDL usage example
```zig
usingnamespace @cImport({
    @cInclude("SDL2/SDL.h");
});
const gl = @import("generated/2.1+fbo.zig");

pub fn main() u8 {
    // note: for 3.2, you would pass SDL_GL_CONTEXT_PROFILE_CORE here
    _ = SDL_GL_SetAttribute(@intToEnum(SDL_GLattr, SDL_GL_CONTEXT_PROFILE_MASK),
                                                   SDL_GL_CONTEXT_PROFILE_COMPATIBILITY);
    _ = SDL_GL_SetAttribute(@intToEnum(SDL_GLattr, SDL_GL_CONTEXT_MAJOR_VERSION), 2);
    _ = SDL_GL_SetAttribute(@intToEnum(SDL_GLattr, SDL_GL_CONTEXT_MINOR_VERSION), 1);

    // SDL_CreateWindow()...
    // SDL_GL_CreateContext()...
    // SDL_GL_MakeCurrent()...

    for (gl.extensions) |extension| {
        if (@enumToInt(SDL_GL_ExtensionSupported(extension)) == 0) {
            std.debug.warn("Extension {} not supported.\n", .{extension});
            return 1;
        }
    }
    for (gl.commands) |command| {
        command.ptr.* = SDL_GL_GetProcAddress(command.name) orelse {
            std.debug.warn("Failed to load proc {}.\n", .{command.name});
            return 1;
        };
    }

    // rest of program
}
```

Then, in other files:

```zig
usingnamespace @import("generated/2.1+fbo.zig").namespace;

pub fn draw() void {
    // use opengl symbols as normal
    glClearColor(0, 0, 0, 0);
    glClear(GL_COLOR_BUFFER_BIT);
}
```
