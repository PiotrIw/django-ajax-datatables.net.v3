IMAGE := ajax-datatable-demo
CONTAINER := ajax-datatable-demo

.PHONY: demo build run stop

# Build the image and run it in the foreground; Ctrl-C to stop.
demo: build run

build:
	docker build -f Dockerfile -t $(IMAGE) ..

run:
	docker run --rm --name $(CONTAINER) -p 8000:8000 $(IMAGE)

stop:
	docker stop $(CONTAINER)
