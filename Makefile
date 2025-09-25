.PHONY: add-to-path

BASH_DIR := $(abspath $(CURDIR)/bash)

add-to-path:
	@ZSHRC="$$HOME/.zshrc"; \
	ANCHOR="# CSV Utilities"; \
	rel_path=$$(printf '%s\n' "$(BASH_DIR)" | sed -e "s:^$$HOME/::"); \
	export_line="export PATH=\$$PATH:\"\$$HOME/$$rel_path\""; \
	[ -f "$$ZSHRC" ] || : > "$$ZSHRC"; \
	STATUS_FILE=$$(mktemp); \
	awk -v anchor="$$ANCHOR" -v line="$$export_line" -v status_file="$$STATUS_FILE" ' \
		BEGIN { found=0; after_anchor=0; action="" } \
		{ \
		  if (after_anchor==1) { \
		    if ($$0 ~ /^export PATH=/) { \
		      print line; \
		      after_anchor=0; \
		      action="updated"; \
		      next; \
		    } else { \
		      print line; \
		      after_anchor=0; \
		      action="added"; \
		    } \
		  } \
		  if ($$0 == anchor) { \
		    print $$0; \
		    found=1; \
		    after_anchor=1; \
		    next; \
		  } \
		  print $$0; \
		} \
		END { \
		  if (found==0) { \
		    if (NR>0) print ""; \
		    print anchor; \
		    print line; \
		    action="added"; \
		  } \
		  if (status_file!="") { \
		    cmd = "printf \"%s\\n\" \"" action "\" > " status_file; \
		    system(cmd); \
		  } \
		} \
	' "$$ZSHRC" > "$$ZSHRC.tmp" && mv "$$ZSHRC.tmp" "$$ZSHRC"; \
	action=$$(cat "$$STATUS_FILE"); rm -f "$$STATUS_FILE"; \
	if [ "$$action" = "updated" ]; then \
	  echo "Updated PATH entry:"; \
	  echo "$$ANCHOR"; \
	  echo "$$export_line"; \
	else \
	  echo "Added PATH entry:"; \
	  echo "$$ANCHOR"; \
	  echo "$$export_line"; \
	fi


