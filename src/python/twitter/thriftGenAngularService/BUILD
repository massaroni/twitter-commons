python_requirement_library(
  name='jsonpickle',
  requirements=[
    python_requirement(requirement='jsonpickle'),
  ]
)

python_binary(
  name = "thriftGenAngularService",
  source = "thriftGenAngularService.py",
  dependencies = [
    pants("src/python/twitter/common/app"),
    pants("src/python/twitter/thrift/descriptors"),
    pants("src/python/twitter/thrift/text"),
    pants(":jsonpickle")
  ]
)
