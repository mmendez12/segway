#!/usr/bin/env bash
(%[^ ]+%)/segway-task run train '' chr1 0 8000 10 0 ../simplesemi.genomedata,../simplesemi.genomedata asinh_norm 0,1 True '[((%\d+%), (%\d+%)), ((%\d+%), (%\d+%))]' '[(%\d%), (%\d%)]' -base 3 -componentCache F -cppCommandOptions (%'(?=.*-\bDCARD_SEG=4\b)(?=.*-\bDINPUT_PARAMS_FILENAME=traindir/params/params\.0\.params\.3\b)(?=.*-\bDCARD_FRAMEINDEX=200000\b)(?=.*-\bDCARD_SUBSEG=1\b)(?=.*-\bDSEGTRANSITION_WEIGHT_SCALE=1\.0\b).*'%) -deterministicChildrenStore F -dirichletPriors T -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile traindir/log/jt_info.txt -lldp 0.001 -lst 100000 -maxEmIters 1 -nf1 2 -nf2 0 -ni1 0 -ni2 4 -objsNotToTrain traindir/auxiliary/dont_train.list -obsNAN T -of1 traindir/observations/float32.list -of2 traindir/observations/int.list -storeAccFile traindir/accumulators/acc.0.0.bin -strFile traindir/segway.str -triFile traindir/triangulation/segway.str.4.1.trifile -trrng 0 -verbosity 0
