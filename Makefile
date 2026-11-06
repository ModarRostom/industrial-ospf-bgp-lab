.PHONY: deploy bootstrap verify failover down lint diagram

deploy:
	sudo containerlab deploy -t topology.clab.yml
	bash scripts/bootstrap.sh

bootstrap:
	bash scripts/bootstrap.sh

verify:
	bash scripts/verify.sh

failover:
	bash scripts/failover.sh

down:
	sudo containerlab destroy -t topology.clab.yml --cleanup

lint:
	python3 -m unittest discover -s tests -v
	bash -n scripts/verify.sh scripts/failover.sh scripts/bootstrap.sh

diagram:
	dot -Tpng docs/topology.dot -o docs/topology.png
