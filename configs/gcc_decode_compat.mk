# Limit GCC optimization cost for the generated decoder only.
# This changes host simulation code optimization; DUT RTL is unchanged.
VSimTop_DecodeUnit%.o: private override OPT_FAST = -O0 -fno-tree-slp-vectorize
VSimTop_DecodeUnit%.o: private override VK_PCH_I_FAST = -include VSimTop__pch.h
