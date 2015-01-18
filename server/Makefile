clean:
	rm -f ./*.pyc ./presets/*.pyc

debug:
	python2 main.py debug

prod:
	sudo -b -g dialout nohup python2 probe_start_loop.py prod

prod_term:
	sudo -g dialout python2 main.py prod

