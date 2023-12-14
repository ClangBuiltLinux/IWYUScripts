# IWYUScripts
Miscellaneous scripts used to automated include-what-you-use on the linux kernel will be found here

To run any of these scripts. Run in the kernel repository
```bash
make LLVM=1 defconfig all compile_commands.json -j $(nproc)
```

## single_iwyu.py

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
* Headers often need to be detangled. This means that structs may need to be moved around, and new headers may need to be created, etc. This must be done by hand, but error messages indicate what is causing the problem.

When to Modify Tables:
1. Use the -d flag for debug mode. 
2. Examine the source of the issue. If it is an asm file that's not present in multiple architectures being included or an asm-generic file find that file and check who includes it.
3. Try setting the problematic file as private in filter.imp. This is done by adding the line:
   ```{ include: ["@[\"<]asm-generic/PROBLEM-FILE.h[\">]", private, "<asm/SOLUTION-FILE.h>", "public"] },```
   replace asm-generic/PROBLEM-FILE.h and asm/SOLUTION-FILE.h accordingly. Examples are found in filter.imp.
4. Try rerunning single-iwyu.py after reverting the previously made changes.
5. If there are still problems. Find the source of the problematic file and replace all tokens that IWYU associates with that file with a better file. An example of this is asm-generic/percpu.h. It has many tokens that need to be manually associated with linux/percpu.h. Add the following line to symbol.imp force an association between a token and a header:
   ```{ symbol: ["TOKEN", private, "asm/SOLUTION-FILE", public]},```
   Examples are found in symbol.imp

## auto_iwyu.py
```
python auto-iwyu.py -c compile_commands.json
```
The auto-iwyu script will attempt to build your whole compile_commands.json file and make changes automatically.


## build_intermediary.py
```
python build_intermediary.py -c compile_commands.json -j $(nproc) -e .ll
```
The build intermediary file will build files with a specific file extension for the entire compile_commands.json. The default extension is .i but can be changed with the -e flag.