# Makefile for program source directory in GNU NLS utilities package.
# Copyright (C) 1995-1997, 2000, 2001 by Ulrich Drepper <drepper@gnu.ai.mit.edu>
#
# This file be copied and used freely without restrictions.  It can
# be used in projects which are not available under the GNU Public License
# but which still want to provide support for the GNU gettext functionality.
# Please note that the actual code is *not* freely available.

include ../common.mk
prefix = /usr
exec_prefix = ${prefix}
datadir = $(prefix)/share
localedir = $(datadir)/locale
gettextsrcdir = $(prefix)/share/gettext/po
subdir = po
srcdir = .

INSTALL = /usr/bin/install -c

MSGFMT = /usr/bin/msgfmt --statistics
XGETTEXT = /usr/bin/xgettext
MSGMERGE = msgmerge
MSGFMT = msgfmt

POFILES =  $(wildcard *.po)
MOFILES =  $(patsubst %.po,%.mo,$(POFILES))

SRCFILES = ../apt-listchanges.py $(wildcard ../apt-listchanges/*.py) \
	../apt-listchanges/apt-listchanges.ui

all: $(PACKAGE).pot $(MOFILES)

.SUFFIXES: .po .mo

.po.mo:
	$(MSGFMT) -o $@ $<

$(PACKAGE).pot: $(SRCFILES)
	if test -f $(XGETTEXT); then \
	    $(XGETTEXT) $(XGETTEXT_COMMON_OPTIONS) \
	                -k_ $(SRCFILES) -o$@; \
	else \
	    echo "Warning: $@ is not updated"; \
	    touch $@; \
	fi

install: all
	for file in $(MOFILES); do \
	    lang=`echo $$file | sed 's/\.mo//'`; \
	    install -d $(DESTDIR)$(localedir)/$$lang/LC_MESSAGES/; \
	    install -m 0644 $$file $(DESTDIR)$(localedir)/$$lang/LC_MESSAGES/$(PACKAGE).mo; \
        done

clean:
	rm -f core core.* *.pox $(PACKAGE).po *.new.po
	rm -fr *.o *.mo

distclean: clean
	rm -f $(PACKAGE).pot

update-po: Makefile
	rm -f $(PACKAGE).pot
	$(MAKE) $(PACKAGE).pot
	if test "$(PACKAGE)" = "gettext"; then PATH=`pwd`/../src:$$PATH; fi; \
        cd $(srcdir); \
        catalogs='$(MOFILES)'; \
        for cat in $$catalogs; do \
            cat=`basename $$cat`; \
            lang=`echo $$cat | sed 's/\.mo$$//'`; \
            echo "$$lang:"; \
            if $(MSGMERGE) --previous  $$lang.po $(PACKAGE).pot -o $$lang.new.po; then \
                mv -f $$lang.new.po $$lang.po; \
                $(MSGFMT) --statistics $$lang.po; rm -f messages.mo; \
            else \
                echo "msgmerge for $$cat failed!"; \
                rm -f $$lang.new.po; \
            fi; \
        done

