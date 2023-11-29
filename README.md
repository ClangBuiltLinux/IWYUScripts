# IWYUScripts
Miscellaneous scripts used to automated include-what-you-use on the linux kernel will be found here

Run in the kernel repository
```bash
make LLVM=1 defconfig all compile_commands.json -j $(nproc)
```

Once that is finished run

```bash
./single_iwyu.py -c compile_commands.json -s specific_file.c
```

Replace with the with the actual locations of compile_commands.json and fix_includes.py. 
Change specific_file.c to be the file you want to change. Optionally add -d to see debug outputs and what IWYU changes are being suggested and made.

There are many reasons that single_iwyu may not work. These are:
* Macro was judged as not used and not included
* Intentionally repeated headers (X-Macro) removed
* Including asm-generic/header instead of asm/header or linux/header
* Other Macro Issues (not defined, implicit declarations, etc)


After Diagnosing there are a few possible solutions:
* Include the header with the macro that was needed. In the symbol.imp file add symbols that were called in conjunction with the macro or inside the macro to correctly inject the header witht the macro in the future.
* Add the duplicate header that was removed back into the code.
* Change asm-generic to asm or linux. The easiest way to know how to do this is to see what includes the asm-generic. Upon making this change you should map the asm-generic header to the new header in the filter.imp file. 
* Headers often need to be detangled. This means that structs may need to be moved around, new headers may need to be created etc. This must be done by hand but error messages indicate what is causing the problem.