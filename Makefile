.PHONY: all check build md html pdf overview overview-pdf clean stats

all: check build md html pdf overview overview-pdf

check:
	python3 scripts/check_source.py

build:
	python3 scripts/build_xml.py

md: build
	python3 scripts/render_md.py

html: build
	python3 scripts/render_html.py

# WeasyPrint is not usable in this environment (conda fontconfig/pango mismatch);
# headless Chrome is used instead. See AGENTS.md "PDF pipeline".
pdf: html
	mkdir -p build/.chrome
	google-chrome --headless=new --disable-gpu --no-sandbox \
	  --allow-file-access-from-files --no-pdf-header-footer \
	  --user-data-dir="$$PWD/build/.chrome" \
	  --print-to-pdf="$$PWD/build/debate.pdf" "file://$$PWD/build/debate.html"
	python3 scripts/add_outline.py

overview: build
	python3 scripts/render_overview.py

overview-pdf: overview
	mkdir -p build/.chrome
	google-chrome --headless=new --disable-gpu --no-sandbox \
	  --allow-file-access-from-files --no-pdf-header-footer \
	  --user-data-dir="$$PWD/build/.chrome" \
	  --print-to-pdf="$$PWD/build/overview.pdf" "file://$$PWD/build/overview.html"

stats:
	python3 scripts/transcript.py

clean:
	rm -rf build/*.xml build/*.md build/*.html build/*.pdf build/preview build/.chrome
