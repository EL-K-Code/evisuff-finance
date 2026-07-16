.PHONY: pdf clean

pdf:
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
	cp main.pdf EviSuff-Finance-v0.pdf

clean:
	latexmk -C
	rm -f EviSuff-Finance-v0.pdf
