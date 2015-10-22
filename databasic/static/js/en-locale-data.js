var gt = new Gettext({
	domain: 'myDomain',
	locale_data: null
});

var _ = function(msgid) { return gt.gettext(msgid); };