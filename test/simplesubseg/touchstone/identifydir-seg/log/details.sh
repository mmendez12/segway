## segway (%[^ ]+%) run (%[0-9a-f]{32}%) at (%[0-9]{4}%)-(%[0-9]{2}%)-(%[0-9]{2}%) (%[0-9]{2}%):(%[0-9]{2}%):(%[0-9]{2}%).(%[0-9]{1,}%)
(%[^ ]+%)/gmtkTriangulate -cppCommandOptions '-DCARD_SEG=2 -DCARD_SUPERVISIONLABEL=-1 -DCARD_FRAMEINDEX=2000000 -DSEGTRANSITION_WEIGHT_SCALE=1.0 -DCARD_SUBSEG=2' -outputTriangulatedFile identifydir-seg/triangulation/segway.str.2.2.trifile -strFile traindir/segway.str -verbosity 0
(%[^ ]+%)/segway-task run viterbi identifydir-seg/viterbi/viterbi0.bed chr1 0 8000 1 0 2 2 seg ../simplesubseg.genomedata /tmp/chr1.0000.(%[0-9a-f]{32}%).float32 /tmp/chr1.0000.(%[0-9a-f]{32}%).int asinh_norm 0,1 -base 3 -cVitRegexFilter '^seg$' -cliqueTableNormalize 0.0 -componentCache F -cppCommandOptions '-DCARD_SEG=2 -DCARD_SUPERVISIONLABEL=-1 -DINPUT_PARAMS_FILENAME=traindir/params/params.params -DCARD_FRAMEINDEX=2000000 -DCARD_SUBSEG=2 -DSEGTRANSITION_WEIGHT_SCALE=1.0' -deterministicChildrenStore F -eVitRegexFilter '^seg$' -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile identifydir-seg/log/jt_info.txt -lst 100000 -mVitValsFile - -nf1 2 -nf2 0 -ni1 0 -ni2 2 -obsNAN T -of1 identifydir-seg/observations/float32.list -of2 identifydir-seg/observations/int.list -pVitRegexFilter '^seg$' -strFile traindir/segway.str -triFile identifydir-seg/triangulation/segway.str.2.2.trifile -verbosity 0 -vitCaseSensitiveRegexFilter T
(%[^ ]+%)/segway-task run posterior identifydir-seg/posterior/posterior%s.0.bed chr1 0 8000 1 0 2 2 seg ../simplesubseg.genomedata /tmp/chr1.0000.(%[0-9a-f]{32}%).float32 /tmp/chr1.0000.(%[0-9a-f]{32}%).int asinh_norm 0,1 -base 3 -cCliquePrintRange 1:1 -cliqueTableNormalize 0.0 -componentCache F -cppCommandOptions '-DCARD_SEG=2 -DCARD_SUPERVISIONLABEL=-1 -DINPUT_PARAMS_FILENAME=traindir/params/params.params -DCARD_FRAMEINDEX=2000000 -DCARD_SUBSEG=2 -DSEGTRANSITION_WEIGHT_SCALE=1.0' -deterministicChildrenStore F -doDistributeEvidence T -eCliquePrintRange 1:1 -fmt1 binary -fmt2 binary -hashLoadFactor 0.98 -inputMasterFile traindir/params/input.master -island T -iswp1 F -iswp2 F -jtFile identifydir-seg/log/jt_info.posterior.txt -lst 100000 -nf1 2 -nf2 0 -ni1 0 -ni2 2 -obsNAN T -of1 identifydir-seg/observations/float32.list -of2 identifydir-seg/observations/int.list -pCliquePrintRange 1:1 -strFile traindir/segway.str -triFile identifydir-seg/triangulation/segway.str.2.2.posterior.trifile -verbosity 0
