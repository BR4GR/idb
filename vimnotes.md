# Recommended only with particular settings or add-ons

vim / vi safely writes all changes. But set up vim to not write swapfiles (.swp files: temporary records of your edits) to CIRCUITPY. Run vim with vim -n, set the no swapfile option, or set the directory option to write swapfiles elsewhere. Otherwise the swapfile writes trigger restarts of your program.
