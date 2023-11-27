# IWYUScripts
Miscellaneous scripts used to automated include-what-you-use on the linux kernel will be found here

Run in the kernel repository
```bash
make LLVM=1 defconfig all compile_commands.json -j $(nproc)
```
This should give the appropriate compile_commands.json. Use this to build the .i files for the compile commands:

```bash
python build_intermediary.py compile_commands.json $(nproc)
```

Replace with the acutual location of compile_commands.json




Once that is finished run

```bash
python single_iwyu.py compile_commands.json ~/include-what-you-use/fix_includes.py specific_file.c
```

Replace with the with the actual locations of compile_commands.json and fix_includes.py. 
Change specific_file.c to be the file you want to change.

There are many reasons that single_iwyu may not work. These are:
* Macro was judged as not used and not included
* Intentionally repeated headers (X-Macro) removed
* Including asm-generic/header instead of asm/header or linux/header

After Diagnosing there are a few possible solutions:
* Include the header with the macro that was needed. In the symbol.imp file add symbols that were called in conjunction with the macro or inside the macro to correctly inject the header witht the macro in the future.
* Add the duplicate header that was removed back into the code.
* Change asm-generic to asm or linux. The easiest way to know how to do this is to see what includes the asm-generic. Upon making this change you should map the asm-generic header to the new header in the filter.imp file. 
