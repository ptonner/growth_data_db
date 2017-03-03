

test:
	if [ -f .test.db ]; then rm .test.db; fi
	nose2
