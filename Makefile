DOT	?= dot

all:: model.png

%.png: %.dot
	$(DOT) -Tpng -o $@ $*.dot
