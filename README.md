# IWYUScripts
Miscellaneous scripts used to automated include-what-you-use on the linux kernel will be found here

Run 
```bash
make LLVM=1 defconfig all compile_commands.json -j 128
```
This should give the appropriate compile_commands.json. Use this to build the .i files for the compile commands:

```bash
python build_intermediary.py compile_commands.json
```

Once that is finished run
```bash
python iwyu-kernel.py compile_commands.json ~/include-what-you-use/fix_includes.py ./filter.imp 
```
Update accordingly with the location of filter.imp and fix_includes.py.
