TARNAME=openstack-ec2-api
SPECFILE=openstack-ec2-api.spec

sources: $(SPECFILE)
	git archive --format=tar --prefix=$(TARNAME)/ HEAD > $(TARNAME).tar
	mkdir -p $(TARNAME)
	cp $(SPECFILE) $(TARNAME)
	cp PKG-INFO $(TARNAME)
	cp openstack-ec2-api-*.service $(TARNAME)
	cp policy.json $(TARNAME)
	cp ec2api.conf.sample $(TARNAME)
	cp AUTHORS $(TARNAME)
	cp ChangeLog $(TARNAME)
	tar --owner=0 --group=0 -rf $(TARNAME).tar $(TARNAME)/$(SPECFILE) $(TARNAME)/PKG-INFO $(TARNAME)/openstack-ec2-api-*.service $(TARNAME)/policy.json $(TARNAME)/ec2api.conf.sample $(TARNAME)/AUTHORS $(TARNAME)/ChangeLog
	gzip -f -9 $(TARNAME).tar
	rm -fr $(TARNAME)

rpm: sources
	rpmbuild -ta $(TARNAME).tar.gz
