# zig-gl
Script to generate a Zig file from the Khronos OpenGL Registry. The generated file includes types, function pointers, and a table to help you load the function pointers.

For now, the file is hardcoded to assume OpenGL 2.1 + GL_ARB_framebuffer_object. But it shouldn't be too hard to support any version that's in the XML registry.

The generated file (`gl.zig`) is included in this repository for convenience.

`gl.xml` is from https://github.com/KhronosGroup/OpenGL-Registry

```bash
bash generate.sh > gl.zig
```

## SDL example
```zig
usingnamespace @cImport({
    @cInclude("SDL2/SDL.h");
});
const gl = @import("gl.zig");

pub fn main() u8 {
    _ = SDL_GL_SetAttribute(@intToEnum(SDL_GLattr, SDL_GL_CONTEXT_PROFILE_MASK), SDL_GL_CONTEXT_PROFILE_COMPATIBILITY);
    _ = SDL_GL_SetAttribute(@intToEnum(SDL_GLattr, SDL_GL_CONTEXT_MAJOR_VERSION), 2);
    _ = SDL_GL_SetAttribute(@intToEnum(SDL_GLattr, SDL_GL_CONTEXT_MINOR_VERSION), 1);

    // SDL_CreateWindow()...
    // SDL_GL_CreateContext()...
    // SDL_GL_MakeCurrent()...

    if (@enumToInt(SDL_GL_ExtensionSupported("GL_ARB_framebuffer_object")) == 0) {
        return 1; // not supported
    }

    // initialize all the gl function pointers
    for (gl.commands) |command| {
        command.ptr.* = SDL_GL_GetProcAddress(command.name) orelse {
            return 1; // failed to load function
        };
    }

    // rest of program
}
```

Then, in other files:

```zig
usingnamespace @import("gl.zig").namespace;

pub fn draw() void {
    // use opengl symbols as normal
    glClearColor(0, 0, 0, 0);
    glClear(GL_COLOR_BUFFER_BIT);
}
```
